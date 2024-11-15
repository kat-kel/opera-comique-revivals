from xml_parser import Datasets
import pandas as pd
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from perfRes import MARCMUSPERF
from matplotlib.ticker import PercentFormatter
import matplotlib.ticker as mtick


from utils import make_palette_by_instrument_group

DIR = Path(__file__).parent.parent.joinpath("results")


SECTION_PALETTE = make_palette_by_instrument_group()


def make_lineplot(ax, df, palette=SECTION_PALETTE):
    plot = sns.lineplot(
        data=df,
        ax=ax,
        x="year",
        y="proportion",
        hue="instrument",
        palette=palette,
        linewidth=3,
    )
    ax.set(
        xlabel="Premier",
        ylabel="Numbers with instrument",
    )
    # ax.set(ylim=(0, 1.1))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(5.0))
    ax.tick_params(labelrotation=90)
    sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
    return plot


def make_color_palette(color: str, dataframe: list[dict]) -> dict:
    label_coded_vals = sorted(set([i["instrument_codedval"] for i in dataframe]))
    labels = [MARCMUSPERF[v] for v in label_coded_vals]
    hex_list = sns.color_palette(color, len(labels)).as_hex()
    return {k: v for k, v in zip(labels, hex_list)}


def main():
    dataset = Datasets().build_opera_averages_df(ignore=["Woodwinds - Bass"])
    [d.update({"proportion": d["proportion"] * 5}) for d in dataset]

    sns.set_theme(style="whitegrid")
    fig, (ax1, ax2, ax3) = plt.subplots(
        ncols=1, nrows=3, figsize=(12, 10), sharey=True, sharex=True
    )

    # Filter dataset by instrument section
    brass_dataset = [d for d in dataset if d["section"].lower().startswith("brass")]
    ww_dataset = [d for d in dataset if d["section"].lower().startswith("woodwind")]
    perc_dataset = [d for d in dataset if d["section"].lower().startswith("percussion")]

    # Brass
    cp = make_color_palette(color="Reds", dataframe=brass_dataset)
    df = pd.DataFrame(brass_dataset)
    make_lineplot(ax=ax1, df=df, palette=cp)

    # Woodwind
    cp = make_color_palette(color="Greens", dataframe=ww_dataset)
    df = pd.DataFrame(ww_dataset)
    make_lineplot(ax=ax2, df=df, palette=cp)

    # Percussion
    cp = make_color_palette(color="Blues", dataframe=perc_dataset)
    df = pd.DataFrame(perc_dataset)
    make_lineplot(ax=ax3, df=df, palette=cp)

    fig.suptitle(
        "Proportion of opera's numbers in which the instrument plays"
    )  # or plt.suptitle('Main title')

    plt.tight_layout()
    fig.savefig(DIR.joinpath("lineplot.png"))


if __name__ == "__main__":
    main()
