#!/usr/bin/env python3
"""
Analysiert die Struktur der Legacy-Geodaten-Tabellen im MS SQL Server.
Gibt Spalten, Datentypen, Constraints und Beispieldaten aus.

WICHTIG: NUR LESEZUGRIFF - keine Schreiboperationen!
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pymssql
from app.config import get_settings

# Geo-Tabellen die analysiert werden sollen
LEGACY_TABLES = [
    "spi_tGeoLand",
    "spi_tGeoBundesland",
    "spi_tGeoRegierungsbezirk",
    "spi_tGeoKreis",
    "spi_tGeoOrt",
    "spi_tGeoOrtsteil",
]


def get_connection():
    """Creates a connection to the legacy MS SQL Server."""
    settings = get_settings()
    return pymssql.connect(
        server=settings.mssql_host,
        port=settings.mssql_port,
        database=settings.mssql_database,
        user=settings.mssql_user,
        password=settings.mssql_password,
        as_dict=False,
    )


def analyze_table(cursor, table_name: str) -> dict:
    """Analyzes a single table and returns its structure."""

    # Column information
    cursor.execute("""
        SELECT
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_NAME = %s
        ORDER BY c.ORDINAL_POSITION
    """, (table_name,))

    columns = cursor.fetchall()

    # Primary Key
    cursor.execute("""
        SELECT kcu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        WHERE tc.TABLE_NAME = %s
          AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
    """, (table_name,))

    pk_columns = [row[0] for row in cursor.fetchall()]

    # Foreign Keys
    cursor.execute("""
        SELECT
            kcu.COLUMN_NAME as fk_column,
            ccu.TABLE_NAME as ref_table,
            ccu.COLUMN_NAME as ref_column
        FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
            ON rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE ccu
            ON rc.UNIQUE_CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
        WHERE kcu.TABLE_NAME = %s
    """, (table_name,))

    foreign_keys = cursor.fetchall()

    # Row count
    cursor.execute(f"SELECT COUNT(*) FROM dbo.{table_name}")
    row_count = cursor.fetchone()[0]

    # Sample data (first 3 rows)
    cursor.execute(f"SELECT TOP 3 * FROM dbo.{table_name}")
    sample_data = cursor.fetchall()

    # Column names for sample data
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """, (table_name,))
    column_names = [row[0] for row in cursor.fetchall()]

    return {
        "table": table_name,
        "columns": columns,
        "column_names": column_names,
        "primary_key": pk_columns,
        "foreign_keys": foreign_keys,
        "row_count": row_count,
        "sample_data": sample_data,
    }


def print_table_info(info: dict):
    """Prints table information in a readable format."""
    print(f"\n{'='*70}")
    print(f"Tabelle: {info['table']}")
    print(f"Anzahl Datensätze: {info['row_count']}")
    print('='*70)

    # Columns
    print("\nSpalten:")
    print("-" * 70)
    print(f"{'Name':<30} {'Typ':<15} {'Länge':<10} {'Nullable':<10} {'PK':<5}")
    print("-" * 70)

    for col in info["columns"]:
        name, dtype, char_len, num_prec, nullable, default = col
        length = char_len if char_len else (num_prec if num_prec else "-")
        is_pk = "PK" if name in info["primary_key"] else ""
        print(f"{name:<30} {dtype:<15} {str(length):<10} {nullable:<10} {is_pk:<5}")

    # Foreign Keys
    if info["foreign_keys"]:
        print("\nForeign Keys:")
        for fk in info["foreign_keys"]:
            print(f"  {fk[0]} -> {fk[1]}.{fk[2]}")

    # Sample Data
    if info["sample_data"]:
        print("\nBeispieldaten (erste 3 Zeilen):")
        print("-" * 70)

        # Print column headers
        col_widths = [max(15, len(name)) for name in info["column_names"]]
        header = " | ".join(f"{name:<{w}}" for name, w in zip(info["column_names"], col_widths))
        print(header[:200] + "..." if len(header) > 200 else header)
        print("-" * min(len(header), 200))

        # Print rows
        for row in info["sample_data"]:
            row_str = " | ".join(
                f"{str(val)[:w]:<{w}}" for val, w in zip(row, col_widths)
            )
            print(row_str[:200] + "..." if len(row_str) > 200 else row_str)


def generate_markdown_report(results: list[dict], output_path: Path):
    """Generates a Markdown documentation of the legacy schema."""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Legacy Geodaten Schema\n\n")
        f.write("**Quelle:** `192.168.91.22:1433/toyware`\n\n")
        f.write("**Generiert am:** " + __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M") + "\n\n")
        f.write("---\n\n")

        # Summary table
        f.write("## Übersicht\n\n")
        f.write("| Tabelle | Datensätze | Primary Key |\n")
        f.write("|---------|------------|-------------|\n")
        for info in results:
            pk = ", ".join(info["primary_key"]) if info["primary_key"] else "-"
            f.write(f"| {info['table']} | {info['row_count']:,} | {pk} |\n")
        f.write("\n---\n\n")

        # Detailed tables
        for info in results:
            f.write(f"## {info['table']}\n\n")
            f.write(f"**Datensätze:** {info['row_count']:,}\n\n")

            # Columns
            f.write("### Spalten\n\n")
            f.write("| Spalte | Datentyp | Länge | Nullable | PK | FK |\n")
            f.write("|--------|----------|-------|----------|----|----|n")

            fk_map = {fk[0]: f"{fk[1]}.{fk[2]}" for fk in info["foreign_keys"]}

            for col in info["columns"]:
                name, dtype, char_len, num_prec, nullable, default = col
                length = char_len if char_len else (num_prec if num_prec else "-")
                is_pk = "✓" if name in info["primary_key"] else ""
                fk_ref = fk_map.get(name, "")
                f.write(f"| {name} | {dtype} | {length} | {nullable} | {is_pk} | {fk_ref} |\n")

            f.write("\n")

            # Foreign Keys
            if info["foreign_keys"]:
                f.write("### Beziehungen\n\n")
                for fk in info["foreign_keys"]:
                    f.write(f"- `{fk[0]}` → `{fk[1]}.{fk[2]}`\n")
                f.write("\n")

            f.write("---\n\n")

    print(f"\nMarkdown-Report geschrieben: {output_path}")


def main():
    """Main function."""
    print("="*70)
    print("Legacy Geodaten-DB Analyse")
    print("Server: 192.168.91.22:1433 / Database: toyware")
    print("WICHTIG: Nur Lesezugriff!")
    print("="*70)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("\n✓ Verbindung hergestellt\n")
    except Exception as e:
        print(f"\n✗ Verbindungsfehler: {e}")
        print("\nStellen Sie sicher, dass:")
        print("  - Der Server erreichbar ist (192.168.91.22)")
        print("  - Die .env Datei korrekte Credentials enthält")
        print("  - pymssql installiert ist (uv sync)")
        sys.exit(1)

    results = []

    for table_name in LEGACY_TABLES:
        try:
            info = analyze_table(cursor, table_name)
            results.append(info)
            print_table_info(info)
        except Exception as e:
            print(f"\n✗ Fehler bei Tabelle {table_name}: {e}")

    conn.close()

    # Generate Markdown report
    output_dir = Path(__file__).parent.parent / "docs" / "prd"
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(results, output_dir / "03_migration.md")

    print("\n" + "="*70)
    print("Analyse abgeschlossen!")
    print("="*70)


if __name__ == "__main__":
    main()
