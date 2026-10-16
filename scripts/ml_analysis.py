# -*- coding: utf-8 -*-
"""酒类：供应商绩效聚类 + 月度销售预测。
- 供应商×类目聚类（KMeans，按销量/渠道/规模）
- 月度预测：滞后+趋势特征，线性 vs 随机森林（类目粒度，诚实评估；月级样本少→不用DL）
输出：ml_result.json + supplier_clusters.parquet + forecast.parquet
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

OUT = Path(__file__).resolve().parent.parent / "data" / "output"
sup = pd.read_parquet(OUT / "supplier_level.parquet")
mon = pd.read_parquet(OUT / "monthly_agg.parquet")

r = {}
r["n_suppliers"] = len(sup)
r["n_monthly"] = len(mon)

# ---------- 供应商绩效聚类 ----------
feat = pd.DataFrame({
    "sales_log": np.log1p(sup["total_sales"]),
    "warehouse_share": (sup["warehouse"] / sup["total_sales"].clip(1)).clip(0, 1),
    "retail_share": (sup["retail"] / sup["total_sales"].clip(1)).clip(0, 1),
    "items_log": np.log1p(sup["items"]),
})
r["supplier_features"] = list(feat.columns)
sup["retail_share"] = feat["retail_share"]
sup["warehouse_share"] = feat["warehouse_share"]
X = StandardScaler().fit_transform(feat.fillna(0))
km = KMeans(n_clusters=4, random_state=42, n_init=10)
sup["cluster"] = km.fit_predict(X)
prof = sup.groupby("cluster").agg(
    n=("supplier", "count"), sales=("total_sales", "mean"),
    retail_share=("retail_share", "mean"), items=("items", "mean"),
).reset_index()
r["supplier_clusters"] = prof.to_dict("records")
sup.to_parquet(OUT / "supplier_clusters.parquet", index=False)

# ---------- 类目月度预测（线性 vs 随机森林，滞后特征） ----------
cat_series = mon.pivot_table(index="date", columns="category", values="total_sales", aggfunc="sum").fillna(0).sort_index()
r["forecast_rows"] = len(cat_series)
results = {}
for cat_name in cat_series.columns:
    y = cat_series[cat_name].values
    n = len(y)
    if n < 8:
        continue
    featf = pd.DataFrame({
        "lag1": pd.Series(y).shift(1), "lag2": pd.Series(y).shift(2),
        "lag3": pd.Series(y).shift(3), "month": cat_series.index.month,
        "t": np.arange(n),
    })
    d = pd.concat([pd.Series(y, name="y"), featf], axis=1).dropna()
    Xf = d[["lag1", "lag2", "lag3", "month", "t"]].values
    yf = d["y"].values
    tr = int(len(d) * 0.75)
    if tr < 3:
        continue
    Xtr, Xte, ytr, yte = Xf[:tr], Xf[tr:], yf[:tr], yf[tr:]
    out = {}
    for name, mdl in [("linear", LinearRegression()), ("rf", RandomForestRegressor(n_estimators=200, random_state=42))]:
        mdl.fit(Xtr, ytr)
        p = mdl.predict(Xte)
        out[name] = {"mae": round(float(mean_absolute_error(yte, p)), 2),
                     "r2": round(float(r2_score(yte, p)), 3)}
    results[cat_name] = out
r["forecast_by_category"] = results

# 全类目汇总（线性平均）
maes = [v["linear"]["mae"] for v in results.values() if "linear" in v]
r2s = [v["linear"]["r2"] for v in results.values() if "linear" in v]
r["linear_mae_mean"] = round(float(np.mean(maes)), 2) if maes else None
r["linear_r2_mean"] = round(float(np.mean(r2s)), 3) if r2s else None

with open(OUT / "ml_result.json", "w", encoding="utf-8") as f:
    json.dump(r, f, ensure_ascii=False, indent=1)
print(json.dumps(r, ensure_ascii=False, indent=1), flush=True)
