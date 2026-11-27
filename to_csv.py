import pandas as pd

from tekstherkenning_ark.constants import DATA_DIR

if __name__ == "__main__":
    NOMIC_OUTPUT_DIR = DATA_DIR / "nomic_output"

    src_dir = NOMIC_OUTPUT_DIR / "csv" / "HEG0201"
    tgt_dir = NOMIC_OUTPUT_DIR / "csv" / "LYG0201"

    unique_csv_names = set(f.name for f in list(src_dir.glob("*.csv")) + list(tgt_dir.glob("*.csv")))

    for csv_name in unique_csv_names:
        csv_file_src = src_dir / csv_name
        csv_file_tgt = tgt_dir / csv_name

        if csv_file_src.exists() and not csv_file_tgt.exists():
            print(f"{csv_name} only in src")
        elif not csv_file_src.exists() and csv_file_tgt.exists():
            print(f"{csv_name} only in tgt")

        else:
            df_cols_src = sorted(list(pd.read_csv(csv_file_src).columns))
            df_cols_tgt = sorted(list(pd.read_csv(csv_file_tgt).columns))

            if df_cols_src != df_cols_tgt:
                print(f"{csv_name} columns differ")
                tgt_surplus = sorted([c for c in df_cols_tgt if c not in df_cols_src])
                src_surplus = sorted([c for c in df_cols_src if c not in df_cols_tgt])
                if tgt_surplus:
                    print(" tgt:", tgt_surplus)
                if src_surplus:
                    print(" src:", src_surplus)
