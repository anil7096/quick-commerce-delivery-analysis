import re, sqlite3, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D, O = ROOT/"data", ROOT/"outputs"
BLUE, ORANGE, INK, MUTED, GRID, AQUA = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e6e5e1", "#1baf7a"
plt.rcParams.update({"axes.edgecolor":GRID,"axes.labelcolor":MUTED,"xtick.color":MUTED,"ytick.color":MUTED,
  "axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,"grid.color":GRID,"axes.axisbelow":True,"figure.dpi":150})
con = sqlite3.connect(":memory:")
orders = pd.read_csv(D/"orders.csv"); stores = pd.read_csv(D/"stores.csv")
orders.to_sql("orders", con, index=False); stores.to_sql("stores", con, index=False)
q = {m.group(1): m.group(2) for m in re.finditer(r"-- name: (\w+)\n(.*?)(?=\n-- name:|\Z)", (ROOT/"sql/analysis_queries.sql").read_text(), re.S)}
R = {k: pd.read_sql(v, con) for k, v in q.items()}
for k, v in R.items(): v.to_csv(O/f"{k}.csv", index=False)

h = R["delay_by_hour"]
fig, ax = plt.subplots(figsize=(8, 4)); ax.bar(h.hour, h.delayed_pct, color=[ORANGE if v > 10 else BLUE for v in h.delayed_pct], width=.7)
ax.set_xlabel("Hour of day"); ax.set_ylabel("% orders delayed"); ax.set_xticks(range(0, 24, 2))
ax.set_title("Delays concentrate in the lunch and 7-9 pm peaks", loc="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(O/"01_delay_by_hour.png"); plt.close()

s = R["delay_by_store"].sort_values("delayed_pct"); lab = s.area + " (" + s.city.str[:3] + ")"
fig, ax = plt.subplots(figsize=(8, 5)); ax.barh(lab, s.delayed_pct, color=[ORANGE if v > s.delayed_pct.median()*1.5 else BLUE for v in s.delayed_pct], height=.6)
for y, v in enumerate(s.delayed_pct): ax.text(v + .15, y, f"{v:.1f}%", va="center", fontsize=7.5, color=INK)
ax.grid(axis="y", visible=False); ax.set_xlabel("% orders delayed")
ax.set_title("Store gap: sprawling, thinly staffed zones lag", loc="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(O/"02_delay_by_store.png"); plt.close()

b = R["delay_stage_breakdown"].set_index("status")[["pick_pack","rider_wait","travel"]]
fig, ax = plt.subplots(figsize=(7, 3.2)); left = np.zeros(2); cols = [BLUE, ORANGE, AQUA]
for c, col in zip(b.columns, cols):
    ax.barh(b.index, b[c], left=left, color=col, height=.5, edgecolor="white", linewidth=2, label=c.replace("_", " "))
    for i, v in enumerate(b[c]): ax.text(left[i] + v/2, i, f"{v:.1f}", ha="center", va="center", color="white", fontsize=8)
    left += b[c].values
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.2), fontsize=8); ax.grid(False)
ax.set_xlabel("Average minutes"); ax.set_title("Delayed orders lose time to rider wait and travel", loc="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(O/"03_stage_breakdown.png"); plt.close()

c = R["rider_capacity_buckets"]
fig, ax = plt.subplots(figsize=(7, 3.8)); ax.bar(c.capacity_bucket.str[3:], c.delayed_pct, color=BLUE, width=.55)
for i, v in enumerate(c.delayed_pct): ax.text(i, v + .3, f"{v:.1f}%", ha="center", fontsize=8, color=INK)
ax.set_xlabel("Riders available per order in the store-hour"); ax.set_ylabel("% delayed")
ax.set_title("Delay rate rises sharply when riders per order fall", loc="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(O/"04_capacity_vs_delay.png"); plt.close()

# heatmap: store x hour block
o = orders.merge(stores, on="store_id"); o["block"] = pd.cut(o.hour, [-1,5,10,14,17,21,23], labels=["0-5","6-10","11-14","15-17","18-21","22-23"])
piv = o.pivot_table(index="area", columns="block", values="delayed", aggfunc="mean", observed=True)*100
fig, ax = plt.subplots(figsize=(7, 5)); im = ax.imshow(piv.values, cmap="Blues", aspect="auto")
ax.set_xticks(range(piv.shape[1]), piv.columns); ax.set_yticks(range(piv.shape[0]), piv.index); ax.grid(False)
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]; ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7.5, color="white" if v > piv.values.max()*.6 else INK)
ax.set_xlabel("Hour block"); ax.set_title("% delayed by store and time block", loc="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(O/"05_store_hour_heatmap.png"); plt.close()

# --- what-if: delayed orders in low-capacity store-hours; if rider wait were typical, how many would still be late?
o["rpo"] = (o.riders_on_roster/3)/o.orders_in_store_hour
low = o.rpo < 1.0
typical_wait = o.loc[~low, "rider_wait_min"].mean()
o["total_fix"] = np.where(low, o.pick_pack_min + typical_wait + o.travel_min, o.total_min)
fix_delayed = (o.total_fix > o.promised_min + 2).mean()*100
print(pd.concat([R["kpi_overview"]]).to_string(index=False))
print("what-if delayed % :", round(o.delayed.mean()*100,1), "->", round(fix_delayed,1), "| low-capacity share of orders", round(low.mean()*100,1), "| of delays", round(o.delayed[low].sum()/o.delayed.sum()*100,1))
for k in ["delay_by_rain","delay_stage_breakdown","rider_capacity_buckets","lateness_vs_rating_cancel","revenue_at_risk"]: print(R[k].to_string(index=False))
print(R["delay_by_store"].head(3).to_string(index=False)); print(R["delay_by_store"].tail(2).to_string(index=False))
print(h.sort_values("delayed_pct", ascending=False).head(4).to_string(index=False))
