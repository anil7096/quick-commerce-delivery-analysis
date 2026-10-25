"""Synthetic quick-commerce orders for a Hyderabad + Bengaluru dark-store network (seeded)."""
import numpy as np, pandas as pd
from pathlib import Path
rng = np.random.default_rng(7); OUT = Path(__file__).resolve().parents[1] / "data"

stores = []
areas = {"Hyderabad":["Gachibowli","Madhapur","Kukatpally","Banjara Hills","Uppal","Miyapur"],
         "Bengaluru":["Koramangala","Indiranagar","Whitefield","HSR Layout","Electronic City","Jayanagar"]}
for c, al in areas.items():
    for a in al: stores.append((f"DS{len(stores)+1:02d}", c, a))
stores = pd.DataFrame(stores, columns=["store_id","city","area"])
stores["riders_on_roster"] = rng.integers(14, 36, len(stores))
stores["avg_distance_km"] = rng.uniform(1.4, 3.2, len(stores)).round(2)
stores.loc[stores.area.isin(["Whitefield","Electronic City"]), "avg_distance_km"] += 1.0   # sprawling zones
stores.loc[stores.area.isin(["Whitefield","Electronic City"]), "riders_on_roster"] -= 6

N = 60000
days = pd.date_range("2026-07-01", "2026-09-30")
od = rng.choice(days, N)
w = np.array([.4,.2,.1,.05,.05,.1,.6,1.5,3,3.2,3.5,4.5,5,4,3.4,3.6,4,5,7.5,8.5,7.5,5.5,2.8,1.2]); hr = rng.choice(24, N, p=w / w.sum())
hr = hr.astype(int)
df = pd.DataFrame({"order_id": [f"O{i+1:06d}" for i in range(N)], "order_date": od, "hour": hr,
                   "store_id": rng.choice(stores.store_id, N)})
df = df.merge(stores, on="store_id")
df["dow"] = pd.to_datetime(df.order_date).dt.day_name()
df["items"] = rng.choice([1,2,3,4,5,6,8,10], len(df), p=[.18,.22,.2,.15,.1,.07,.05,.03])
df["rain"] = (pd.to_datetime(df.order_date).dt.dayofyear % 7 == 0) | (rng.random(len(df)) < .06)
df["category_mix"] = rng.choice(["Grocery","Fresh","Dairy","Snacks","Personal care","Electronics"], len(df), p=[.34,.2,.14,.16,.1,.06])
# orders per store-hour -> load (drives wait for rider)
df["slot"] = pd.to_datetime(df.order_date).astype(str) + "-" + df.hour.astype(str) + "-" + df.store_id
load = df.groupby("slot").order_id.transform("count")
df["orders_in_store_hour"] = load
df["riders_per_order_hour"] = (df.riders_on_roster / 3) / load.clip(lower=1)    # ~1/3 of roster active per hour
peak = df.hour.isin([12,13,19,20,21])

pick = 2.2 + 0.35*df["items"] + (df.category_mix == "Fresh")*0.8 + rng.gamma(2, .6, len(df)) + (load > load.quantile(.85))*1.6
wait = np.where(df.riders_per_order_hour < 1.0, rng.gamma(2.2, 1.9, len(df)), rng.gamma(1.4, .7, len(df)))
travel = df.avg_distance_km * rng.uniform(2.0, 3.0, len(df)) * np.where(df.rain, 1.35, 1.0) * np.where(peak, 1.15, 1.0)
df["pick_pack_min"] = pick.round(1); df["rider_wait_min"] = np.round(wait, 1); df["travel_min"] = travel.round(1)
df["total_min"] = (df.pick_pack_min + df.rider_wait_min + df.travel_min).round(1)
df["promised_min"] = np.select([df.avg_distance_km < 2.0, df.avg_distance_km <= 3.0], [12, 16], 20)
df["delayed"] = df.total_min > df.promised_min + 2
df["cancelled"] = rng.random(len(df)) < (0.008 + 0.0025*(df.total_min - 12).clip(lower=0))
df["rating"] = np.clip(np.round(5 - 0.13*(df.total_min - df.promised_min).clip(lower=0) + rng.normal(0, .6, len(df))), 1, 5).astype(int)
df.loc[df.cancelled, "rating"] = np.nan
df["order_value_inr"] = (df["items"] * rng.uniform(70, 160, len(df))).round()
cols = ["order_id","order_date","hour","dow","store_id","items","category_mix","rain","orders_in_store_hour",
        "pick_pack_min","rider_wait_min","travel_min","total_min","promised_min","delayed","cancelled","rating","order_value_inr"]
df[cols].to_csv(OUT/"orders.csv", index=False)
stores.to_csv(OUT/"stores.csv", index=False)
print(len(df), "orders; delayed %", round(100*df.delayed.mean(),1))
