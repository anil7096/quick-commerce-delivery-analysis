# Quick-Commerce Delivery Delay Analysis (SQL + Python)

**Role focus:** Data Analyst (Operations / Supply Chain) | **Tools:** Python (pandas, NumPy, matplotlib), SQL (SQLite), root-cause and what-if analysis

## Business problem
A quick-commerce company runs 12 dark stores across Hyderabad and Bengaluru and promises delivery in 12-20 minutes depending on distance. Delays hurt ratings and cause cancellations. **Where, when and why do orders arrive late, and what would fix the most delays?**

## Data (synthetic, reproducible)
`src/generate_data.py` (seed 7) creates **60,000 orders** (Jul-Sep 2026) and a 12-store table. Each order has item count, category, hour, rain flag, orders in the store-hour, and a three-stage time split (pick & pack, rider wait, travel), promise time, delay, cancellation and rating. Rider wait is linked to rider capacity so a real driver exists to discover. Swap in real order logs with the same columns and the pipeline still runs.

## Method
- SQL (`sql/analysis_queries.sql`): KPIs, delay by hour/store/weather, stage breakdown, **capacity buckets** (CTE + window-free derived metric), lateness vs rating/cancellation, revenue at risk.
- Python: five charts and a **counterfactual** (what if rider wait in thin-capacity hours matched normal hours?).

## Key findings (from this dataset)
- Baseline: **8.5% of orders delayed**, 13.6 min average delivery, 1.33% cancelled, rating 4.75.
- **Time of day:** delays peak at **7-8 pm (21% and 17%)** and the lunch hour (10%); off-peak is near 2-3%.
- **Rider capacity is the biggest lever.** When fewer than one rider is available per order in the store-hour, **30-34% of orders are late versus 3-6% otherwise**. Those thin-capacity hours are only **15% of orders but 59% of all delays**. Rider wait there averages about 4.2 min versus 1 min.
- **What-if:** bringing those hours up to normal rider wait cuts overall delays from **8.5% to about 4.4%**.
- **Stores:** Electronic City is the clear outlier (22.5% delayed; 4.2 km average distance, only 14 riders, 48% of its orders placed in hours with fewer than 1 rider per order; 38% delayed in the 6-9 pm block). Whitefield has the thinnest roster (9 riders, 65% of its orders in rider-short hours) but shows only 11% delayed because its promise window is 20 minutes. **Uppal (14%)** is different: capacity is mostly fine (only 9% of its orders in rider-short hours), but its short 12-minute promise leaves almost no buffer at the evening peak (25% delayed). So promise-window calibration matters as much as staffing. Gachibowli and Banjara Hills sit at 1-2%. (Promise windows by distance band are a synthetic assumption.)
- **Rain** lifts delays from 5.8% to 19.3% (travel time 6.6 -> 9.0 min).
- **Lateness costs:** orders 5+ min late rate 4.0 versus 4.8 for on-time, and cancel at about 4.1% versus 1.1%.

## Recommendations
1. Add peak-hour (7-9 pm, 12-1 pm) rider shifts in Electronic City and Whitefield first; target at least 1 rider per order-hour. For Uppal, test a 14-15 minute evening promise or a small peak-hour rider top-up.
2. Add a rain surge-staffing trigger and a longer promise window on rainy evenings.
3. Review Electronic City's catchment: split the zone or open a satellite store to cut the 4+ km average trip.
4. Track "% store-hours below 1 rider per order" as a weekly operational KPI.

## Outputs
`outputs/*.png` (5 charts) and a CSV for every query.

## Run it
```bash
pip install pandas numpy matplotlib
python src/generate_data.py
python src/analysis.py
```

*Figures come from synthetic data; the project demonstrates the method.*
