from xml_parser import Datasets
import seaborn as sns
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt


# Get dataset of operas' instrument deployment / work averages
dataset = Datasets().build_sparse_opera_averages_df()
df = pd.DataFrame(dataset)
features = df.drop(columns=["year", "date", "title", "charlton_id"])
labels = pd.to_numeric(df["year"])
ids = df["title"]

# Fit and transform data using PCA
standard_df = StandardScaler().fit_transform(features)
pca = PCA(2)
X_r = pca.fit_transform(standard_df)

# Convert PCA transformation into data frame
pca_df = pd.DataFrame(X_r, columns=["PCA1", "PCA2"], index=df.index)
final_df = pd.concat([pca_df, labels, ids], axis=1)
print("Final PCA data frame:")
print(final_df)
x, y, hue = final_df["PCA1"], final_df["PCA2"], final_df["year"]

# Set up figure
gridkw = dict(height_ratios=[6, 1])
fig, (ax0, ax1) = plt.subplots(nrows=2, ncols=1, figsize=(16, 24), gridspec_kw=gridkw)

# Make heatmap showing PCA analysis
cmap = sns.diverging_palette(0, 300, s=60, sep=50, as_cmap=True)
# cmap = "Accent"
hmp = sns.heatmap(
    pca.components_,
    ax=ax1,
    cmap=cmap,
    yticklabels=[f"PCA{x}" for x in range(1, pca.n_components_ + 1)],
    xticklabels=list(features.columns),
    linewidths=1,
    annot=True,
    fmt=",.2f",
    cbar_kws={
        "shrink": 0.8,
        "orientation": "vertical",
    },
)
hmp.set_aspect("equal")
hmp.set_title(
    "Heatmap showing how much an instrument's deployment throughout the opera influences the principal components of the analysis (PCA)",
    fontdict={"size": 12},
)

# Make scatter plot showing PCA results
colormap = "Spectral"
points = sns.scatterplot(
    data=final_df,
    x="PCA1",
    y="PCA2",
    ax=ax0,
    hue="year",
    s=100,
    alpha=0.5,
    palette=colormap,
)
ax0.collections[0].set_sizes([2_500])
norm = plt.Normalize(hue.min(), hue.max())
mappable = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
mappable.set_array([])
ax0.get_legend().remove()
cbar = plt.colorbar(mappable, ax=ax0, shrink=0.5)

above_node, below_node = "bottom", "top"
for line in range(0, final_df.shape[0]):
    points.text(
        x[line] + 0.01,
        y[line],
        ids[line],
        horizontalalignment="center",
        verticalalignment=below_node,
        size="xx-small",
        color="black",
    )
for line in range(0, final_df.shape[0]):
    points.text(
        x[line] + 0.01,
        y[line],
        hue[line],
        horizontalalignment="center",
        verticalalignment=above_node,
        size="small",
        color="black",
    )
points.set_title(
    "PCA Analysis of opéra-comiques' instrumentation, 1800-1840", fontdict={"size": 18}
)

sns.despine()
plt.tight_layout()

fig.savefig("results/pca.png")
