from xml_parser import Datasets
import seaborn as sns
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid")


class DataFrame:
    def __init__(self):
        # Get dataset of operas' instrument deployment / work averages
        dataset = Datasets().build_sparse_opera_averages_df()
        self.df = pd.DataFrame(dataset)
        self.features = self.df.drop(columns=["year", "date", "title", "charlton_id"])
        self.labels = pd.to_numeric(self.df["year"])
        self.ids = self.df["title"]

        # Fit and transform data using PCA
        standard_df = StandardScaler().fit_transform(self.features)
        self.pca = PCA(2)
        X_r = self.pca.fit_transform(standard_df)

        # Convert PCA transformation into data frame
        pca_df = pd.DataFrame(X_r, columns=["PCA1", "PCA2"], index=self.df.index)
        self.final_df = pd.concat([pca_df, self.labels, self.ids], axis=1)


def make_heatmap(d: DataFrame):
    # Set up figure
    fig, (ax) = plt.subplots(figsize=(12, 8))

    # Make heatmap showing PCA analysis
    cmap = sns.diverging_palette(0, 300, s=60, sep=50, as_cmap=True)
    chart = sns.heatmap(
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
    chart.set_aspect("equal")
    title = "Instrument's influence on principal component\n"
    chart.set_title(title)
    plt.tight_layout()
    fig.savefig("results/pca_variables_and_components.png", bbox_inches="tight")


def make_scatter_plot(d: DataFrame):
    fig, (ax) = plt.subplots(figsize=(16, 24))
    # Make scatter plot showing PCA results
    colormap = "Spectral"
    hue, x, y = d.df["year"], d.final_df["PCA1"], d.final_df["PCA2"]
    chart = sns.scatterplot(
        data=d.final_df,
        x="PCA1",
        y="PCA2",
        ax=ax,
        hue="year",
        s=100,
        alpha=0.5,
        palette=colormap,
    )
    ax.collections[0].set_sizes([2_000])
    norm = plt.Normalize(hue.min(), hue.max())
    mappable = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
    mappable.set_array([])
    ax.get_legend().remove()
    _ = plt.colorbar(mappable, ax=ax, shrink=0.5)

    above_node, below_node = "bottom", "top"
    for line in range(0, d.final_df.shape[0]):
        chart.text(
            x[line] + 0.01,
            y[line],
            d.df["title"][line],
            horizontalalignment="center",
            verticalalignment=below_node,
            size=6,
            color="black",
        )
    for line in range(0, d.final_df.shape[0]):
        chart.text(
            x[line] + 0.01,
            y[line],
            hue[line],
            horizontalalignment="center",
            verticalalignment=above_node,
            size=8,
            color="black",
            weight="bold",
        )
    chart.set_title(
        "PCA Analysis of opéra-comiques' instrumentation, 1800-1840",
        size=24,
    )

    sns.despine()
    plt.tight_layout()

    fig.savefig("results/pca_plot.png", bbox_inches="tight")


if __name__ == "__main__":
    df = DataFrame()
    make_heatmap(df)
    make_scatter_plot(df)
