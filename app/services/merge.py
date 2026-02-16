"""
ETL Merge Service — combines multiple source files via configurable joins.

Uses pandas DataFrames internally. Produces a merged EtlImportFile
that can be fed into the normal ETL import pipeline.
"""
import json
import logging
import os
import uuid
from io import BytesIO
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.etl import EtlMergeConfig, EtlMergeJoin, EtlImportFile

logger = logging.getLogger(__name__)


class MergeService:
    """Execute multi-file merges based on stored configurations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._settings = get_settings()

    async def preview_merge(
        self, config_id: str, limit: int = 10
    ) -> dict[str, Any]:
        """Preview merge result (first N rows + stats)."""
        config = await self._load_config(config_id)
        df, join_stats = await self._execute_joins(config)
        return {
            "headers": list(df.columns),
            "rows": json.loads(df.head(limit).to_json(orient="records")),
            "total_rows": len(df),
            "total_cols": len(df.columns),
            "join_stats": join_stats,
        }

    async def execute_merge(self, config_id: str) -> dict[str, Any]:
        """Run all join steps and produce a merged EtlImportFile."""
        config = await self._load_config(config_id)
        df, join_stats = await self._execute_joins(config)

        # Save as new Excel file
        import_file = await self._save_merged_file(config, df)

        return {
            "import_file_id": str(import_file.id),
            "original_filename": import_file.original_filename,
            "total_rows": len(df),
            "total_cols": len(df.columns),
            "join_stats": join_stats,
        }

    async def _load_config(self, config_id: str) -> EtlMergeConfig:
        """Load merge config with joins (ordered by sortierung)."""
        result = await self.db.execute(
            select(EtlMergeConfig).where(EtlMergeConfig.id == config_id)
        )
        config = result.scalar_one_or_none()
        if not config:
            raise ValueError(f"MergeConfig {config_id} nicht gefunden")
        return config

    async def _execute_joins(
        self, config: EtlMergeConfig
    ) -> tuple[pd.DataFrame, list[dict]]:
        """Execute all join steps and return merged DataFrame + stats."""
        # 1. Load primary file
        primary_file = await self._find_file_by_role(
            config.source_id, config.primary_file_role
        )
        if not primary_file:
            raise ValueError(
                f"Hauptdatei mit Rolle '{config.primary_file_role}' "
                f"nicht gefunden für Source {config.source_id}"
            )
        primary_df = self._read_file_as_dataframe(primary_file)
        rows_before = len(primary_df)

        join_stats = []

        # 2. Execute each join step
        for join in config.joins:
            join_file = await self._find_file_by_role(
                config.source_id, join.file_role
            )
            if not join_file:
                join_stats.append({
                    "file_role": join.file_role,
                    "status": "skipped",
                    "reason": f"Datei mit Rolle '{join.file_role}' nicht gefunden",
                })
                continue

            right_df = self._read_file_as_dataframe(join_file)
            right_rows = len(right_df)

            # Deduplicate on join key
            if join.deduplicate and join.join_col_right in right_df.columns:
                before_dedup = len(right_df)
                right_df = right_df.drop_duplicates(subset=[join.join_col_right])
                after_dedup = len(right_df)
            else:
                before_dedup = after_dedup = right_rows

            # Select only requested columns (+ join key) BEFORE renaming
            cols_include = self._parse_json(join.columns_include, None)
            if cols_include:
                keep_cols = [join.join_col_right] + [
                    c for c in cols_include if c in right_df.columns
                ]
                right_df = right_df[list(dict.fromkeys(keep_cols))]

            # Apply column renames on right side AFTER filtering
            renames = self._parse_json(join.column_renames, {})
            if renames:
                right_df = right_df.rename(columns=renames)

            # Execute the join
            rows_before_join = len(primary_df)
            primary_df = primary_df.merge(
                right_df,
                left_on=join.join_col_left,
                right_on=join.join_col_right,
                how=join.join_type,
            )

            # Drop the right join key if it's different from left
            if (join.join_col_right != join.join_col_left
                    and join.join_col_right in primary_df.columns):
                primary_df = primary_df.drop(columns=[join.join_col_right])

            join_stats.append({
                "file_role": join.file_role,
                "status": "ok",
                "right_rows": right_rows,
                "after_dedup": after_dedup,
                "cols_added": len(right_df.columns) - 1,  # minus join key
                "rows_before": rows_before_join,
                "rows_after": len(primary_df),
            })

        # 3. Apply output renames
        output_renames = self._parse_json(config.output_renames, {})
        if output_renames:
            primary_df = primary_df.rename(columns=output_renames)

        # 4. Drop unwanted columns
        output_drop = self._parse_json(config.output_drop_cols, [])
        if output_drop:
            drop_existing = [c for c in output_drop if c in primary_df.columns]
            primary_df = primary_df.drop(columns=drop_existing)

        return primary_df, join_stats

    async def _find_file_by_role(
        self, source_id: str, file_role: str
    ) -> EtlImportFile | None:
        """Find the most recent import file with a given role for a source."""
        result = await self.db.execute(
            select(EtlImportFile)
            .where(
                EtlImportFile.source_id == source_id,
                EtlImportFile.file_role == file_role,
                EtlImportFile.is_merged_output == False,  # noqa: E712
            )
            .order_by(EtlImportFile.erstellt_am.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    def _read_file_as_dataframe(self, import_file: EtlImportFile) -> pd.DataFrame:
        """Read an import file from disk into a pandas DataFrame."""
        content = import_file.file_content
        if not content:
            raise ValueError(
                f"Datei '{import_file.original_filename}' nicht auf Disk gefunden"
            )
        # Choose engine based on original filename extension
        fname = (import_file.original_filename or "").lower()
        engine = "xlrd" if fname.endswith(".xls") else "openpyxl"
        return pd.read_excel(BytesIO(content), engine=engine)

    async def _save_merged_file(
        self, config: EtlMergeConfig, df: pd.DataFrame
    ) -> EtlImportFile:
        """Save merged DataFrame as a new EtlImportFile on disk."""
        # Generate filenames
        stored_filename = f"{uuid.uuid4().hex}.xlsx"
        source_dir = str(config.source_id)
        storage_path = os.path.join(
            self._settings.upload_dir, "etl", source_dir
        )
        os.makedirs(storage_path, exist_ok=True)

        # Write Excel
        file_path = os.path.join(storage_path, stored_filename)
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        content = buffer.getvalue()

        with open(file_path, "wb") as f:
            f.write(content)

        # Create DB record
        original_name = f"{config.name.replace(' ', '_')}_merged.xlsx"
        import_file = EtlImportFile(
            source_id=config.source_id,
            original_filename=original_name,
            stored_filename=stored_filename,
            file_size=len(content),
            status="analyzed",
            headers=json.dumps(list(df.columns)),
            row_count=len(df),
            file_role="merged_output",
            merge_config_id=config.id,
            is_merged_output=True,
        )
        self.db.add(import_file)
        await self.db.commit()
        await self.db.refresh(import_file)

        return import_file

    @staticmethod
    def _parse_json(value: str | None, default: Any) -> Any:
        """Parse a JSON text column, returning default if None/invalid."""
        if not value:
            return default
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default
