# Liquor Channel Reconciliation & Sales Performance — Analysis Plan

**Business direction**: a liquor wholesaler (Ohio data) channel management. Data: 307,645 rows, 2017–2020, 396 suppliers, 34,056 items, with retail/warehouse/transfer sales across three channels. Continues the reconciliation theme: quantify **channel structure, channel-coverage gaps, category/supplier performance, seasonality**, and give channel and assortment recommendations.

## 1. Analysis Purpose
- **Channel reconciliation**: sales structure and growth across retail vs warehouse (wholesale) vs transfer (allocation) channels; identify **channel-coverage gaps** (39.6% of items have zero retail sales).
- **Category/supplier performance**: WINE/LIQUOR/BEER category composition, top-supplier concentration, monthly/annual trends and seasonality.
- **Sales forecast**: monthly forecast (category/supplier granularity) to guide stocking.

## 2. Analysis Metrics
- Three-channel sales: total, share, YoY/monthly trends.
- Channel coverage: share of items with zero retail sales, share with warehouse as dominant channel.
- Category composition: WINE/LIQUOR/BEER/KEGS sales and channel.
- Supplier concentration: top-N supplier sales share.
- Monthly trends: annual/monthly sales, seasonality (holidays).

## 3. Data Cleaning
- YEAR/MONTH → date; handle missing SUPPLIER/ITEM TYPE (167/1); RETAIL SALES missing 3.
- ITEM CODE → item; normalize category (uppercase, STR_SUPPLIES/NON-ALCOHOL regroup).
- Derive: total sales = retail + warehouse + transfer, primary/secondary channel.
- Build item-level + supplier-level + monthly-aggregation tables.

## 4. Modeling (ML + statistics; principle/why/how)
- **Monthly sales forecast**: category×month time series, Prophet/linear/tree comparison (honest evaluation; few monthly samples → no DL).
- **Supplier×category clustering**: KMeans by sales/channel/concentration into performance groups.
- Category concentration (HHI) / Pareto.

## 5. Visualizations (each chart Insight+Action)
- Three-channel sales structure (reconciliation gap).
- Category × channel composition.
- Annual/monthly sales trend (seasonality).
- Top-supplier concentration.
- Supplier performance clustering.
- Monthly forecast vs actual.

## 6. Recommendations (landing)
- Route channel-gap items through warehouse/allocation.
- Increase purchase on high-growth categories/suppliers.
- Seasonal stocking.
- Supplier-concentration risk.
