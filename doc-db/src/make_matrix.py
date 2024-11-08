from lxml import etree
from lxml.etree import XMLParser
from pathlib import Path
from perfRes import MARCMUSPERF
import csv
import seaborn as sn
from collections import Counter
import pandas as pd
import numpy as np
import click
import matplotlib.pyplot as plt


NS = {"mei": "http://www.music-encoding.org/ns/mei"}

DIR = Path(__file__).parent.parent.joinpath("results")
DIR.mkdir(exist_ok=True)


@click.command()
@click.option("--decade", "-y", required=True)
def main(decade):
    decade = decade[:3]
    outfile_stem = f"{decade}0s"
    files = [fp for fp in Path("xml-files").iterdir() if fp.stem.startswith(decade)]
    operas = []
    with open(DIR.joinpath(f"{outfile_stem}.csv"), "w") as f:
        writer = csv.DictWriter(f, fieldnames=["opera"] + list(MARCMUSPERF.values()))
        writer.writeheader()
        for f in files:
            tree = etree.parse(f, parser=XMLParser())
            work_id = tree.xpath(
                "//mei:identifier[@type='CharltonWild']", namespaces=NS
            )[0].text.strip()
            counter = Counter({k: 0 for k in MARCMUSPERF.keys()})
            for group in tree.xpath("//mei:perfResList", namespaces=NS):
                instruments = sorted(
                    [
                        t.get("codedval")
                        for t in group.xpath("mei:perfRes", namespaces=NS)
                    ]
                )
                row = {k: 0 for k in MARCMUSPERF.keys()}
                for i in instruments:
                    row[i] = 1
                    counter.update([i])

                # Change label for CSV row
                new_row = {MARCMUSPERF[k]: v for k, v in row.items()}
                new_row.update({"opera": work_id})
                writer.writerow(new_row)

            operas.append(counter)

    data = [
        {MARCMUSPERF[k]: v for k, v in o.items() if not k.startswith("s")}
        for o in operas
    ]

    df = pd.DataFrame(data)

    corr = df.corr(numeric_only=True)

    title_string = f"""Correlation of instruments playing together proportional to numbers in the opera
Decade: {outfile_stem}, excluding bowed instruments
"""

    # plotting the heatmap
    sn.set_theme(style="white", palette="pastel")
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(8, 6))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    hm = sn.heatmap(
        ax=ax,
        data=corr,
        cmap="crest",
        mask=mask,
        vmax=0.3,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.75, "label": "correlation coefficient"},
    ).set(title=title_string)

    of = DIR.joinpath(f"{outfile_stem}.png")
    fig.tight_layout()
    fig.savefig(of)


if __name__ == "__main__":
    main()
