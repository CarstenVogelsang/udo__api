"""Merge Busch product data from 4 source files into one import-ready Excel.

Source files (docs/Busch_11_2025/):
- BUSCH.xlsx: Main product master data (2,686 articles)
- 0809mobaauto.xls: Dealer price list (GNP, VE, Rabatt, MwSt)
- Busch_Produktsicherheit_2025_3.xlsx: Product safety texts (DE/EN/FR)
- pangv-busch.csv: PAngV base price data (364 articles)

Output: BUSCH_merged.xlsx with normalized column names.
"""
import sys
from pathlib import Path

import pandas as pd

INPUT_DIR = Path(__file__).parent.parent / "docs" / "Busch_11_2025"
OUTPUT_FILE = INPUT_DIR / "BUSCH_merged.xlsx"


def main():
    print("=== Busch Data Merge ===\n")

    # 1. Main file: BUSCH.xlsx
    print("1. Loading BUSCH.xlsx ...")
    df_main = pd.read_excel(INPUT_DIR / "BUSCH.xlsx")
    print(f"   {len(df_main)} rows, {len(df_main.columns)} columns")

    # 2. Dealer price list: 0809mobaauto.xls (GNP, VE, Rabatt, MwSt)
    print("2. Loading 0809mobaauto.xls ...")
    df_handel = pd.read_excel(INPUT_DIR / "0809mobaauto.xls")
    df_handel = df_handel.rename(columns={"Artikelnummer": "Artikel"})
    # Only take columns not already in main file
    merge_cols = ["Artikel", "GNP", "VE", "Rabatt", "MWST"]
    df_main = df_main.merge(
        df_handel[merge_cols].drop_duplicates(subset=["Artikel"]),
        on="Artikel",
        how="left",
    )
    print(f"   Merged: GNP, VE, Rabatt, MWST")

    # 3. Product safety: Busch_Produktsicherheit_2025_3.xlsx
    # Header row has duplicate column names ("Text" x3, "Link" x3, "Link 2" x3)
    # so we read with header=None and assign names manually.
    print("3. Loading Busch_Produktsicherheit_2025_3.xlsx ...")
    df_safety_raw = pd.read_excel(
        INPUT_DIR / "Busch_Produktsicherheit_2025_3.xlsx",
        header=None,
        skiprows=2,  # Skip header row + legend row
    )
    # Assign meaningful column names by position
    safety_col_names = [
        "Artikel", "EAN_safety", "Beschreibung_safety",
        "Sicherheitssymbol", "Handelsname",
        "Sicherheitstext_DE", "Sicherheitstext_EN", "Sicherheitstext_FR",
        "Sicherheitsdatenblatt_Link",
        "Sicherheitsinfo_DE", "Sicherheitsinfo_EN", "Sicherheitsinfo_FR",
        "Entsorgung_DE", "Entsorgung_EN", "Entsorgung_FR",
    ]
    df_safety_raw.columns = safety_col_names[:len(df_safety_raw.columns)]

    # Only merge relevant columns
    safety_merge = df_safety_raw[
        ["Artikel", "Sicherheitssymbol", "Sicherheitstext_DE"]
    ].drop_duplicates(subset=["Artikel"])

    df_main = df_main.merge(safety_merge, on="Artikel", how="left")
    print(f"   Merged: Sicherheitssymbol, Sicherheitstext_DE")

    # 4. PAngV: pangv-busch.csv (364 rows)
    print("4. Loading pangv-busch.csv ...")
    df_pangv = pd.read_csv(INPUT_DIR / "pangv-busch.csv", sep=";", encoding="utf-8")
    df_pangv = df_pangv.rename(columns={
        "NUMMER": "Artikel",
        "BEZ": "PAngV_Einheit",
        "INHALT": "PAngV_Inhalt",
        "GRUNDMENGE": "PAngV_Grundmenge",
    })
    # Fix decimal comma → dot
    df_pangv["PAngV_Inhalt"] = (
        df_pangv["PAngV_Inhalt"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .apply(lambda x: float(x) if x not in ("nan", "") else None)
    )
    df_pangv["PAngV_Grundmenge"] = pd.to_numeric(
        df_pangv["PAngV_Grundmenge"], errors="coerce"
    )

    df_main = df_main.merge(
        df_pangv[["Artikel", "PAngV_Einheit", "PAngV_Inhalt", "PAngV_Grundmenge"]],
        on="Artikel",
        how="left",
    )
    print(f"   Merged: PAngV_Einheit, PAngV_Inhalt, PAngV_Grundmenge")

    # 5. Data cleanup
    print("\n5. Cleaning data ...")

    # VKP/GNP: Round to 2 decimals (float artifacts like 55.990001...)
    for col in ["VKP", "GNP"]:
        if col in df_main.columns:
            df_main[col] = df_main[col].round(2)

    # Memo: Remove _x000D_ artifacts (Excel CR/LF encoding)
    for col in ["Memo", "Memo Englisch", "Memo Französisch"]:
        if col in df_main.columns:
            df_main[col] = (
                df_main[col]
                .astype(str)
                .str.replace("_x000D_", "", regex=False)
                .replace("nan", None)
            )

    # Normalize column names for EAV code-matching
    rename_map = {
        "Spur H0": "spur_h0",
        "Spur N": "spur_n",
        "Spur TT": "spur_tt",
        "Spur Z": "spur_z",
        "Spur 1/G": "spur_1g",
        "Spur 0": "spur_0",
        "Automarken": "automarke",
        "Warengruppe": "warengruppe_code",
    }
    df_main = df_main.rename(columns=rename_map)

    # Drop columns we don't need for import
    drop_cols = ["Video-Datei", "Link", "Merker", "Ausverkauft"]
    for col in drop_cols:
        if col in df_main.columns:
            df_main = df_main.drop(columns=[col])

    # 6. Output
    print(f"\n6. Writing {OUTPUT_FILE.name} ...")
    df_main.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")

    print(f"\n=== Result ===")
    print(f"Rows: {len(df_main)}")
    print(f"Columns ({len(df_main.columns)}):")
    for i, col in enumerate(df_main.columns):
        non_null = df_main[col].notna().sum()
        pct = non_null / len(df_main) * 100
        print(f"  {i+1:2d}. {col:30s} {non_null:5d} ({pct:.0f}%)")

    print(f"\nOutput: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
