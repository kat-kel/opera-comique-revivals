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


def stats():
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
    fig.savefig(Path(__file__).parent.joinpath("ages.png"))


def perf():
    conn = duckdb.connect()
    conn.execute(
        "create table perfs as select * from read_csv('{}')".format(PERFORMANCES)
    )
    sns.set_theme("paper")

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex=True, sharey=True)
    ax3.set_ylim(0, 82)

    query = f"""
    SELECT
        date_part('month', day_of_performance) AS "month",
        date_part('year', day_of_performance) AS "year",
        day_of_performance,
        days_old/365 as days_old,
        number_of_acts,
        charlton_id
    FROM perfs
    WHERE year < 1830
    AND days_old > (365 + 180)
"""
    df_1820s = conn.sql(query)
    g = sns.histplot(
        ax=ax1,
        data=df_1820s.df(),
        y="days_old",
        hue="year",
        binwidth=1,
        multiple="stack",
        palette=sns.color_palette("coolwarm", as_cmap=True),
    )
    g.set_title("Age of the works performed in the 1820s")
    g.set_xlabel("Number of performances")
    g.set_ylabel("Years between work's performance and creation")

    query = f"""
    SELECT
        date_part('month', day_of_performance) AS "month",
        date_part('year', day_of_performance) AS "year",
        day_of_performance,
        days_old/365 as days_old,
        number_of_acts,
        charlton_id
    FROM perfs
    WHERE year < 1840
    AND year > 1829
    AND days_old > (365 + 180)
"""
    df_1830s = conn.sql(query)
    g = sns.histplot(
        ax=ax2,
        data=df_1830s.df(),
        y="days_old",
        hue="year",
        binwidth=1,
        multiple="stack",
        palette=sns.color_palette("coolwarm", as_cmap=True),
    )
    g.set_title("Age of the works performed in the 1830s")
    g.set_xlabel("Number of performances")
    g.set_ylabel("Years between work's performance and creation")

    query = f"""
    SELECT
        date_part('month', day_of_performance) AS "month",
        date_part('year', day_of_performance) AS "year",
        day_of_performance,
        days_old/365 as days_old,
        number_of_acts,
        charlton_id
    FROM perfs
    WHERE year > 1839
    AND days_old > (365 + 180)
"""
    df_1840s = conn.sql(query)
    g = sns.histplot(
        ax=ax3,
        data=df_1840s.df(),
        y="days_old",
        hue="year",
        binwidth=1,
        multiple="stack",
        palette=sns.color_palette("coolwarm", as_cmap=True),
    )
    g.set_title("Age of the works performed in the 1840s")
    g.set_xlabel("Number of performances")
    g.set_ylabel("Years between work's performance and creation")

    fig.set_size_inches(12, 18)
    fig.tight_layout()
    fig.savefig(Path(__file__).parent.joinpath("perfs.png"))


if __name__ == "__main__":
    # stats()
    perf()
