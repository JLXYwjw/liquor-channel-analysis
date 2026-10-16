# -*- coding: utf-8 -*-
"""酒类渠道数据清洗：
- YEAR/MONTH → 日期；SUPPLIER/ITEM TYPE/RETAIL SALES 缺失处理
- 派生 total_sales、主渠道；类目归一
- 输出：sales_clean.parquet（行级）、supplier_level.parquet、monthly_agg.parquet、cleaning_report.json
"""
import json
from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "Warehouse_and_Retail_Sales.csv"
OUT = Path(__file__).resolve().parent.parent / "data" / "output"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW)
report = {}
report["rows_in"] = len(df)
report["missing_in"] = {c: int(df[c].isna().sum()) for c in df.columns}

# 日期
df["ym"] = df["YEAR"].astype(str) + "-" + df["MONTH"].astype(str).str.zfill(2)
df["date"] = pd.to_datetime(df["ym"] + "-01")
report["date_min"] = str(df["date"].min().date())
report["date_max"] = str(df["date"].max().date())

# 缺失处理
df["SUPPLIER"] = df["SUPPLIER"].fillna("UNKNOWN")
df["ITEM TYPE"] = df["ITEM TYPE"].fillna("UNKNOWN")
df["RETAIL SALES"] = df["RETAIL SALES"].fillna(0.0)

# 类目归一（非饮品/杂项归 OTHER）
cat_map = {"STR_SUPPLIES": "OTHER", "REF": "OTHER", "DUNNAGE": "OTHER"}
df["ITEM TYPE"] = df["ITEM TYPE"].str.upper().replace(cat_map)

# 派生
df["retail"] = df["RETAIL SALES"].fillna(0.0)
df["transfer"] = df["RETAIL TRANSFERS"].fillna(0.0)
df["warehouse"] = df["WAREHOUSE SALES"].fillna(0.0)
df["total_sales"] = df["retail"] + df["warehouse"] + df["transfer"]
ch = df[["warehouse", "retail", "transfer"]].idxmax(axis=1)
df["main_channel"] = ch.map({"warehouse": "仓储", "retail": "零售", "transfer": "调拨"})

clean = df.rename(columns={
    "SUPPLIER": "supplier", "ITEM CODE": "item_code", "ITEM DESCRIPTION": "item_desc",
    "ITEM TYPE": "category", "YEAR": "year", "MONTH": "month",
}).drop(columns=["RETAIL SALES", "RETAIL TRANSFERS", "WAREHOUSE SALES"])
clean = clean[["date", "ym", "year", "month", "supplier", "item_code", "item_desc",
               "category", "retail", "transfer", "warehouse", "total_sales", "main_channel"]]
clean = clean.sort_values(["date", "item_code"])
report["rows_out"] = len(clean)
report["retail_zero_pct"] = round((clean["retail"] == 0).mean() * 100, 2)
report["retail_only_zero_pct"] = round(((clean["retail"] == 0) & (clean["total_sales"] > 0)).mean() * 100, 2)
report["nulls_out"] = {c: int(clean[c].isna().sum()) for c in clean.columns}
clean.to_parquet(OUT / "sales_clean.parquet", index=False)

# 商品级（item × category）
item = clean.groupby(["item_code", "category", "supplier"]).agg(
    total_sales=("total_sales", "sum"), retail=("retail", "sum"),
    warehouse=("warehouse", "sum"), transfer=("transfer", "sum"),
    n_months=("ym", "nunique"),
).reset_index()
item.to_parquet(OUT / "item_level.parquet", index=False)
report["items"] = len(item)

# 供应商级
sup = clean.groupby("supplier").agg(
    total_sales=("total_sales", "sum"), retail=("retail", "sum"),
    warehouse=("warehouse", "sum"), transfer=("transfer", "sum"),
    items=("item_code", "nunique"),
).reset_index()
sup.to_parquet(OUT / "supplier_level.parquet", index=False)
report["suppliers"] = len(sup)

# 月度聚合（类目×月）
monthly = clean.groupby(["ym", "date", "category"]).agg(
    total_sales=("total_sales", "sum"), retail=("retail", "sum"),
    warehouse=("warehouse", "sum"), transfer=("transfer", "sum"),
).reset_index().sort_values("date")
monthly.to_parquet(OUT / "monthly_agg.parquet", index=False)
report["monthly_rows"] = len(monthly)

with open(OUT / "cleaning_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False), flush=True)
