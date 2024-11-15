from xml_parser import Datasets
import pandas as pd
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from utils import make_palette_by_instrument_group


DIR = Path(__file__).parent.parent.joinpath("results")


def plot_barchart(df: pd.DataFrame, ax, title_string: str):
    color_palette = make_palette_by_instrument_group()
    plot = sn.histplot(
        df,
        ax=ax,
        y="year",
        hue="instrument",
        multiple="fill",
        stat="proportion",
        discrete=True,
        shrink=0.8,
        palette=color_palette,
    )
    sn.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
    ax.set(
        ylabel="Premiere",
        xlabel="Proportion",
        title=title_string,
    )
    return plot


sn.set_theme(style="white", palette="pastel")
fig, (ax) = plt.subplots(ncols=1, nrows=1, figsize=(16, 16))

datasets = Datasets()

data = datasets.build_dense_work_df(binary=True, ignore=[])

bar_df = pd.DataFrame(data)
plot_barchart(df=bar_df, ax=ax, title_string="")
plt.tight_layout()

fig.savefig(DIR.joinpath("barchart.png"))
