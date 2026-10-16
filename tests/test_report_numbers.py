# -*- coding: utf-8 -*-
"""酒类报告数字一致性。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "output"
HTML = ROOT / "report" / "酒类渠道对账与销售绩效分析.html"


def _html():
    return HTML.read_text(encoding="utf-8")


def _m():
    return json.loads((OUT / "metrics.json").read_text(encoding="utf-8"))


def test_channel_match_html():
    m = _m()
    assert abs(m["channel_pct"]["warehouse"] - 64.4) < 0.1
    assert "64.4%" in _html()
    assert abs(m["channel_pct"]["retail"] - 17.9) < 0.1
    assert "17.9%" in _html()


def test_retail_zero_match_html():
    m = _m()
    assert abs(m["retail_zero_pct"] - 39.56) < 0.1
    assert "39.6%" in _html()


def test_supplier_concentration_match_html():
    m = _m()
    assert abs(m["supplier_top10_share"] - 65.8) < 0.1
    assert "65.8%" in _html()
    assert abs(m["hhi"] - 705.2) < 1
    assert "705" in _html()


def test_item_pareto_match_html():
    m = _m()
    assert abs(m["item_top1pct_share"] - 61.1) < 0.1
    assert "61.1%" in _html()


def test_forecast_honesty():
    ml = json.loads((OUT / "ml_result.json").read_text(encoding="utf-8"))
    assert ml["linear_r2_mean"] < 0  # 数据不连续，预测不可靠（诚实声明）
    assert "R²" in _html() and "不可靠" in _html()


def test_clusters_match_html():
    ml = json.loads((OUT / "ml_result.json").read_text(encoding="utf-8"))
    assert len(ml["supplier_clusters"]) == 4
    assert "4" in _html() and "聚类" in _html()
