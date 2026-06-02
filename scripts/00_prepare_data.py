"""UCI Adult Income データにヘッダーを付与し、デモ用CSVを整形する。

入力: data/adult-all.csv  (jbrownlee/Datasets ミラー、ヘッダー無し48,841行)
出力: data/adult.csv      (ヘッダー付き、欠損 '?' を整形)
"""

from pathlib import Path
from urllib.request import urlopen
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "adult-all.csv"
OUT = ROOT / "data" / "adult.csv"

# ヘッダー無し・48,841 行の UCI Adult ミラー（Kaggle 不要で取得可能）
RAW_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/adult-all.csv"

# UCI Adult の標準カラム順
COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "educational-num",
    "marital-status", "occupation", "relationship", "race", "gender",
    "capital-gain", "capital-loss", "hours-per-week", "native-country", "income",
]


def ensure_raw() -> None:
    """data/adult-all.csv が無ければミラーから取得する（clone 直後でも動くように）。"""
    if RAW.exists():
        return
    RAW.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {RAW_URL} ...")
    with urlopen(RAW_URL) as r:  # noqa: S310  公開データセットの取得
        RAW.write_bytes(r.read())
    print(f"saved -> {RAW}")


def main() -> None:
    ensure_raw()
    df = pd.read_csv(RAW, header=None, names=COLUMNS, skipinitialspace=True)
    # 文字列カラムの前後空白を除去（ミラーによっては空白が残る）
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    # income 表記ゆれ（'<=50K.' 等）を正規化
    df["income"] = df["income"].str.replace(".", "", regex=False)
    df.to_csv(OUT, index=False)
    print(f"rows={len(df):,} cols={len(df.columns)} -> {OUT}")
    print(df.head(3).to_string())
    print("\n[income 分布]")
    print(df["income"].value_counts())


if __name__ == "__main__":
    main()
