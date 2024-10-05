from datetime import date
import duckdb
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import dates as mdates


MONTHLY_STATS = (
    Path(__file__).parent.parent.joinpath("results").joinpath("monthly_statistics.csv")
)

PERFORMANCES = (
    Path(__file__)
    .parent.parent.joinpath("results")
    .joinpath("list_of_performances.csv")
)


rel = duckdb.read_csv(str(MONTHLY_STATS))

mmin = rel.min("month").fetchone()[0]
mmax = rel.max("month").fetchone()[0]

x = "month"

sns.set_theme("paper")

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True)
ax3.set_xlim(mmin, mmax)

# Major ticks every half year, minor ticks every month,
ax3.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
# Text in the x-axis will be displayed in 'YYYY-mm' format.
ax3.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
# Rotates and right-aligns the x labels so they don't crowd each other.
for label in ax3.get_xticklabels(which="major"):
    label.set(rotation=180 + 90, horizontalalignment="right")

y = "age of oldest work (year)"
g = sns.lineplot(ax=ax1, data=rel.df(), x=x, y=y)
g.set_title("Age (years) of oldest work per month")

y = "population skewness"
g = sns.lineplot(ax=ax2, data=rel.df(), x=x, y=y)
g.set_title("Skewness of the age of works performed in a month")

y = "population standard deviation (year)"
g = sns.lineplot(ax=ax3, data=rel.df(), x=x, y=y)
g.set_title("Standard deviation of the age of works performed in a month")

fig.set_size_inches(18, 10)
fig.tight_layout()
fig.savefig("vis/ages.png")
