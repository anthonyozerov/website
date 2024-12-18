import requests
import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.family"] = "serif"


headers = {"Authorization": "Bearer shr_o69HxjQ0BYrY2FPD9HxdirhJYcFDCeRolEd744Uj88e"}

base_url = "https://api.density.io/v2/spaces/spc_863128347956216317"

interval = "10m"

start = "2024-12-11T00:00:00"
end = "2024-12-11T23:59:59"

# open file containing times so that we don't repeat them
with open("times.txt", "r") as f:
    times = f.read().splitlines()
with open("data.txt", "r") as f:
    all_data = f.read().splitlines()

for i in range(1500, -1, -1):
    today = datetime.datetime.now().date()
    day = today - datetime.timedelta(days=i)
    start = day.strftime("%Y-%m-%dT00:00:00")
    if start in times:
        continue
    end = day.strftime("%Y-%m-%dT23:59:59")
    url = f"{base_url}/counts?interval={interval}&start_time={start}&end_time={end}"
    new_results = requests.get(url, headers=headers).json()["results"]
    result_strs = []
    for r in new_results:
        result_strs.append(
            f'{r["timestamp"]},{r["count"]},{r["interval"]["analytics"]["min"]},{r["interval"]["analytics"]["max"]}'
        )
    for r in result_strs:
        all_data.append(r)
    if i > 2:
        with open("times.txt", "a") as f:
            f.write(start + "\n")
        with open("data.txt", "a") as f:
            for r in result_strs:
                f.write(str(r) + "\n")


# start working with data to visualize
df = pd.DataFrame(
    [r.split(",") for r in all_data], columns=["timestamp", "count", "min", "max"]
)

df["timestamp"] = pd.to_datetime(df.timestamp)
# convert column to pacific time
df["timestamp"] = df["timestamp"].dt.tz_convert("US/Pacific")
df["weekday"] = df["timestamp"].dt.day_of_week

df["time"] = df["timestamp"].dt.time
df["time_int"] = df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute

# convert count, min, and max to int
df["count"] = df["count"].astype(int)
df["min"] = df["min"].astype(int)
df["max"] = df["max"].astype(int)


def plot_heatmap(df, start, end):
    df_subset = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)]

    heatmap = np.zeros((7, 24 * 6))
    num_days = np.zeros((7, 24 * 6))

    for i, row in df_subset.iterrows():
        tod = row["time_int"] // 10
        dow = row["weekday"]
        count = row["count"]
        heatmap[dow, tod] += count
        num_days[dow, tod] += 1

    heatmap = heatmap / num_days

    fig, ax = plt.subplots()

    cax = ax.imshow(
        heatmap.T,
        aspect="auto",
        interpolation="none",
        cmap="hot",
        extent=[0, 7, 24 * 6, 0],
        vmin=0,
        vmax=160,
    )

    # set the x axis labels
    ax.set_xticks(np.arange(0, 7, 1) + 0.5)
    ax.set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    ax.set_yticks(np.arange(0, 24 * 6, 6))
    # y ticks are only on the hour
    ax.set_yticklabels([f"{h:02d}:00" for h in range(24)])
    # add hlines at the hour
    for h in range(24):
        ax.axhline(h * 6, color="black", linewidth=0.5)
    plt.ylim(23 * 6, 7 * 6)
    plt.colorbar(cax, label="average number of people")
    plt.title("RSF weight room usage " + start + " to " + end)
    return heatmap


def make_heatmap(df, daysback):
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=daysback)
    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")
    heatmap = plot_heatmap(df, start, end)
    plt.savefig(f"heatmap_{daysback}.png", dpi=300)
    return heatmap


heatmap_7 = make_heatmap(df, 7)
heatmap_14 = make_heatmap(df, 14)
heatmap_30 = make_heatmap(df, 30)
heatmap_60 = make_heatmap(df, 60)
heatmap_120 = make_heatmap(df, 120)
heatmap_365 = make_heatmap(df, 365)


# get today's data from the dataframe
today = datetime.datetime.now().date()
start = today.strftime("%Y-%m-%d")
end = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
today_counts = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)]["count"]

# make x and y ticks point inwards
plt.rcParams["xtick.direction"] = "in"
plt.rcParams["ytick.direction"] = "in"

# add top and right ticks
plt.rcParams["xtick.top"] = True
plt.rcParams["ytick.right"] = True


# define the x-axis
xaxis = np.arange(0, 24 * 6, 1)
xaxis_today = xaxis[: len(today_counts)]

# plot today's data
fig, ax = plt.subplots()
plt.plot(xaxis_today, today_counts, label="today so far", color="red", linewidth=3)
if len(today_counts) > 0:
    plt.plot(xaxis_today[-1], today_counts.iloc[-1], "o", markersize=8, color="red")

# plot historical data
today_weekday = today.weekday()
labels = ["last week", "last 2 weeks", "last month", "last 2 months", "last 4 months"]
heatmaps = [heatmap_7, heatmap_14, heatmap_30, heatmap_60, heatmap_120]
alphas = [1, 0.7, 0.5, 0.3, 0.1]
for label, hmap, alpha in zip(labels, heatmaps, alphas):
    plt.plot(xaxis, hmap[today_weekday], label=label, color="black", alpha=alpha)

plt.title(
    f'RSF weight room usage today\ncompared to historical data for {today.strftime("%A")}'
)
plt.ylabel("Number of people")
plt.legend(frameon=False)

ax.set_xticks(np.arange(0, 24 * 6, 6))
ax.set_xticklabels([f"{h:02d}" for h in range(24)])
plt.xlim(0, 24 * 6)
plt.savefig("today.png", dpi=300)

# write txt saying when this was updated
with open("updated.txt", "w") as f:
    f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))