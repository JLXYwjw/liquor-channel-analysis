# -*- coding: utf-8 -*-
"""酒类渠道指标 → metrics.json。"""
import json
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "output"
clean = pd.read_parquet(OUT / "sales_clean.parquet")
item = pd.read_parquet(OUT / "item_level.parquet")
sup = pd.read_parquet(OUT / "supplier_level.parquet")
mon = pd.read_parquet(OUT / "monthly_agg.parquet")

m = {}
m["rows"] = len(clean)
m["items"] = len(item)
m["suppliers"] = len(sup)
m["categories"] = clean["category"].value_counts().to_dict()
m["years"] = clean.groupby("year")["total_sales"].sum().round(1).to_dict()

# 渠道结构
tot = clean["total_sales"].sum()
m["total_sales"] = round(float(tot), 1)
m["channel"] = {
    "retail": round(float(clean["retail"].sum()), 1),
    "warehouse": round(float(clean["warehouse"].sum()), 1),
    "transfer": round(float(clean["transfer"].sum()), 1),
}
m["channel_pct"] = {
    k: round(v / tot * 100, 1) for k, v in m["channel"].items()
}

# 渠道覆盖缺口
m["retail_zero_pct"] = round((clean["retail"] == 0).mean() * 100, 2)
m["main_channel"] = clean["main_channel"].value_counts().to_dict()

# 类目×渠道
cat = clean.groupby("category")[["retail", "warehouse", "transfer", "total_sales"]].sum().round(1).reset_index()
m["category_channel"] = cat.to_dict("records")

# 供应商集中度（HHI + top share）
shares = (sup["total_sales"] / sup["total_sales"].sum())
m["hhi"] = round(float((shares ** 2).sum() * 10000), 1)
m["supplier_top10_share"] = round(float(shares.sort_values(ascending=False).head(10).sum() * 100), 1)
m["supplier_top5"] = sup.sort_values("total_sales", ascending=False).head(5)[
    ["supplier", "total_sales", "items"]].to_dict("records")

# 月度：总量、峰值月、季节
month_all = clean.groupby(["date", "ym"])["total_sales"].sum().reset_index().sort_values("date")
month_all["date"] = month_all["date"].astype(str)
m["monthly_totals"] = month_all.to_dict("records")
m["peak_month"] = month_all.sort_values("total_sales", ascending=False).head(1)[["ym", "total_sales"]].to_dict("records")
m["year_total"] = clean.groupby("year")["total_sales"].sum().to_dict()

# 帕累托：Top 1% 商品销量占比
item_sorted = item.sort_values("total_sales", ascending=False)
top1 = max(1, int(len(item) * 0.01))
m["item_top1pct_share"] = round(float(item_sorted.head(top1)["total_sales"].sum() / item_sorted["total_sales"].sum() * 100), 1)
m["item_top10pct_share"] = round(float(item_sorted.head(int(len(item) * 0.1))["total_sales"].sum() / item_sorted["total_sales"].sum() * 100), 1)

with open(OUT / "metrics.json", "w", encoding="utf-8") as f:
    json.dump(m, f, ensure_ascii=False, indent=1)
print(json.dumps(m, ensure_ascii=False, indent=1), flush=True)
