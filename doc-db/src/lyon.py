from datasets import Datasets
import pandas as pd
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


DIR = Path(__file__).parent.parent.joinpath("results")


def plot_barchart(df: pd.DataFrame, ax, title_string: str):
    plot = sn.histplot(
        df,
        ax=ax,
        hue="title",
        y="instrument",
        multiple="layer",
        discrete=True,
        shrink=0.8,
        legend=False,
    )
    plot.legend(
        title="Version",
        labels=["Revival (1828)", "Original (1791)"],
        bbox_to_anchor=(1, 1),
    )
    ax.set(
        ylabel="Instrument",
        xlabel="Count of airs in which 1 or more of the instrument is required",
        title=title_string,
    )
    return plot


sn.set_theme(style="whitegrid")

fig, (ax1, ax2, ax3) = plt.subplots(
    ncols=1,
    nrows=3,
    figsize=(8, 12),
    sharex=True,
)

datasets = Datasets(dir=Path("revival_xml"))

data = datasets.build_dense_work_df(binary=True, ignore=["Strings, bowed"])

act1 = sorted(
    [d for d in data if d["work_id"].startswith("act1")],
    key=lambda d: d["instrument_codedval"],
)
act2 = sorted(
    [d for d in data if d["work_id"].startswith("act2")],
    key=lambda d: d["instrument_codedval"],
)
act3 = sorted(
    [d for d in data if d["work_id"].startswith("act3")],
    key=lambda d: d["instrument_codedval"],
)


def count_works(df) -> str:
    original = set()
    revival = set()
    for i in df:
        if i["year"].startswith("1791"):
            original.add(i["work_id"])
        else:
            revival.add(i["work_id"])
    return f"{len(revival)} revival airs | {len(original)} original airs"


act1_df = pd.DataFrame(act1)
chart = plot_barchart(df=act1_df, ax=ax1, title_string=f"Act 1\n{count_works(act1)}")

act2_df = pd.DataFrame(act2)
chart = plot_barchart(df=act2_df, ax=ax2, title_string=f"Act 2\n{count_works(act2)}")

act3_df = pd.DataFrame(act3)
chart = plot_barchart(df=act3_df, ax=ax3, title_string=f"Act 3\n{count_works(act3)}")

plt.suptitle(
    "Comparison of instrumentation in Guillaume Tell\n(excluding bowed strings)"
)


plt.tight_layout()


fig.savefig("results/revival.png")
