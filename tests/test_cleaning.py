# -*- coding: utf-8 -*-
"""酒类渠道清洗口径测试。"""
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "output"


def _clean():
    return pd.read_parquet(OUT / "sales_clean.parquet")


def test_clean_shape():
    df = _clean()
    assert len(df) == 307645
    for c in ["retail", "warehouse", "transfer", "total_sales", "main_channel"]:
        assert c in df.columns


def test_no_missing():
    df = _clean()
    assert df.isna().sum().sum() == 0


def test_retail_zero_pct():
    df = _clean()
    assert abs((df["retail"] == 0).mean() * 100 - 39.56) < 0.1


def test_item_supplier_levels():
    item = pd.read_parquet(OUT / "item_level.parquet")
    sup = pd.read_parquet(OUT / "supplier_level.parquet")
    assert len(item) == 37321
    assert len(sup) == 397


def test_monthly_agg():
    mon = pd.read_parquet(OUT / "monthly_agg.parquet")
    assert len(mon) == 145
    assert "category" in mon.columns


def test_supplier_clusters():
    c = pd.read_parquet(OUT / "supplier_clusters.parquet")
    assert len(c) == 397
    assert "cluster" in c.columns
