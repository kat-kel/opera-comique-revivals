from datasets import Datasets
import pandas as pd
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


DIR = Path(__file__).parent.parent.joinpath("results").joinpath("revival")
sn.set_theme(style="whitegrid")


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


def count_works(df) -> str:
    original = set()
    revival = set()
    for i in df:
        if i["year"].startswith("1791"):
            original.add(i["work_id"])
        else:
            revival.add(i["work_id"])
    return f"{len(revival)} revival airs | {len(original)} original airs"


def plot_acts():
    fig, (ax1, ax2, ax3) = plt.subplots(
        ncols=1,
        nrows=3,
        figsize=(8, 12),
        sharex=True,
        sharey=True,
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
    act1_df = pd.DataFrame(act1)
    plot_barchart(df=act1_df, ax=ax1, title_string=f"Act 1\n{count_works(act1)}")

    act2_df = pd.DataFrame(act2)
    plot_barchart(df=act2_df, ax=ax2, title_string=f"Act 2\n{count_works(act2)}")

    act3_df = pd.DataFrame(act3)
    plot_barchart(df=act3_df, ax=ax3, title_string=f"Act 3\n{count_works(act3)}")

    plt.suptitle(
        "Comparison of instrumentation in Guillaume Tell\n(excluding bowed strings)"
    )
    plt.tight_layout()
    of = DIR.joinpath("acts.png")
    fig.savefig(of)


class DataFrame:
    def __init__(
        self, df: pd.DataFrame, features: pd.DataFrame, year: pd.Series, *other_series
    ):
        # Get dataset of operas' instrument deployment / work averages
        self.features = features
        self.year = pd.to_numeric(year)

        # Fit and transform data using PCA
        standard_df = StandardScaler().fit_transform(self.features)
        self.pca = PCA(2)
        X_r = self.pca.fit_transform(standard_df)

        # Convert PCA transformation into data frame
        pca_df = pd.DataFrame(X_r, columns=["PCA1", "PCA2"], index=df.index)
        self.final_df = pd.concat([pca_df, self.year, *other_series], axis=1)


def make_heatmap(d: DataFrame):
    # Set up figure
    fig, (ax) = plt.subplots(figsize=(12, 8))

    # Make heatmap showing PCA analysis
    cmap = sn.diverging_palette(0, 300, s=60, sep=50, as_cmap=True)
    chart = sn.heatmap(
        d.pca.components_,
        ax=ax,
        cmap=cmap,
        yticklabels=[f"PCA{x}" for x in range(1, d.pca.n_components_ + 1)],
        xticklabels=list(d.features.columns),
        linewidths=1,
        annot=True,
        fmt=",.2f",
        cbar_kws={
            "shrink": 0.25,
            "orientation": "vertical",
        },
    )
    chart.set_aspect(2)
    title = "Instrument's influence on principal component\n"
    chart.set_title(title)
    plt.tight_layout()
    of = DIR.joinpath("pca_heatmap.png")
    fig.savefig(of, bbox_inches="tight")


def make_scatter_plot(
    d: DataFrame,
    original_df: pd.DataFrame,
    of: Path,
    hue_label: str,
    colormap: str | None = None,
):
    fig, (ax) = plt.subplots(figsize=(12, 8))
    # Make scatter plot showing PCA results
    x, y = d.final_df["PCA1"], d.final_df["PCA2"]
    if not colormap:
        palette = {
            "original Guillaume Tell": "#E66100",
            "revival Guillaume Tell": "#5D3A9B",
            "19th-c original": "#ebebeb",
        }
        chart = sn.scatterplot(
            data=d.final_df,
            x="PCA1",
            y="PCA2",
            ax=ax,
            hue=hue_label,
            s=100,
            alpha=1,
            palette=palette,
            linewidth=1,
            edgecolor="black",
        )
    else:
        chart = sn.scatterplot(
            data=d.final_df,
            x="PCA1",
            y="PCA2",
            ax=ax,
            hue=hue_label,
            s=100,
            alpha=0.5,
            palette=colormap,
            linewidth=1,
            edgecolor="black",
        )
        hue = original_df[hue_label]
        norm = plt.Normalize(hue.min(), hue.max())
        mappable = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
        mappable.set_array([])
        ax.get_legend().remove()
        _ = plt.colorbar(mappable, ax=ax, shrink=0.5)
    ax.collections[0].set_sizes([200])

    # above_node, below_node = "bottom", "top"
    # if not colormap:
    #     for line in range(0, d.final_df.shape[0]):
    #         chart.text(
    #             x[line] + 0.01,
    #             y[line],
    #             original_df["title"][line],
    #             horizontalalignment="center",
    #             verticalalignment=below_node,
    #             size=6,
    #             color="black",
    #         )
    # for line in range(0, d.final_df.shape[0]):
    #     chart.text(
    #         x[line] + 0.01,
    #         y[line],
    #         original_df["year"][line],
    #         horizontalalignment="center",
    #         # verticalalignment=above_node,
    #         size=8,
    #         color="black",
    #         weight="bold",
    #     )
    chart.set_title(
        "Plotting of Principal Component Analysis (PCA)\n of opéra-comiques' instrumentation, 1800-1840",
        size=24,
    )
    sn.despine()
    plt.tight_layout()
    fig.savefig(of, bbox_inches="tight")


if __name__ == "__main__":
    plot_acts()

    # Calculate PCA
    original_folder = Datasets().build_sparse_opera_averages_df()
    [d.update({"focus": "19th-c original"}) for d in original_folder]
    revival_folder = Datasets(dir=Path("revival_xml")).build_sparse_opera_averages_df()
    [
        d.update({"focus": "original Guillaume Tell"})
        for d in revival_folder
        if d["year"].startswith("1791")
    ]
    [
        d.update({"focus": "revival Guillaume Tell"})
        for d in revival_folder
        if d["year"].startswith("1828")
    ]
    combined_data = original_folder + revival_folder
    combined_df = []
    for d in combined_data:
        combined_df.append(
            {
                k: v
                for k, v in d.items()
                if not k.startswith("Strings, bowed - Double bass")
                and not k.startswith("Strings, bowed - Violoncello")
            }
        )
    cdf = pd.DataFrame(combined_df)
    features = cdf.drop(columns=["focus", "year", "date", "title", "charlton_id"])
    other_labels = [cdf["title"], cdf["focus"]]
    df = DataFrame(cdf, features, pd.to_numeric(cdf["year"]), *other_labels)

    make_heatmap(df)
    of = DIR.joinpath("pca_plot_targets.png")
    make_scatter_plot(d=df, original_df=cdf, of=of, hue_label="focus")

    of = DIR.joinpath("pca_plot_all.png")
    make_scatter_plot(
        d=df, original_df=cdf, of=of, hue_label="year", colormap="Spectral"
    )
