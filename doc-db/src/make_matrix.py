from lxml import etree
from lxml.etree import XMLParser
from pathlib import Path
from perfRes import MARCMUSPERF
import seaborn as sn
import pandas as pd
import click
import matplotlib.pyplot as plt
from collections import Counter


NS = {"mei": "http://www.music-encoding.org/ns/mei"}

DIR = Path(__file__).parent.parent.joinpath("results")
DIR.mkdir(exist_ok=True)


def parse_persName(tag: etree.Element) -> str | None:
    if tag.xpath("mei:addName", namespaces=NS):
        additional_name = tag.xpath("mei:addName", namespaces=NS)[0].text.strip()
        return additional_name
    elif tag.xpath("mei:famName", namespaces=NS):
        surname = tag.xpath("mei:famName", namespaces=NS)[0].text.strip()
        if not tag.xpath("mei:foreName", namespaces=NS):
            return surname
        else:
            forename = tag.xpath("mei:foreName", namespaces=NS)[0].text.strip()
            return f"{forename} {surname}"
    else:
        ts = []
        for t in tag.xpath("*"):
            ts.append(t.text)
            return " ".join(ts)


def get_composers(tree: etree.Element) -> list:
    data = []
    for resp in tree.xpath("//mei:resp/mei:persName[@role='composer']", namespaces=NS):
        name = parse_persName(resp)
        data.append(name)
    return data


def get_librettists(tree: etree.Element) -> list:
    data = []
    for resp in tree.xpath(
        "//mei:resp/mei:persName[@role='librettist']", namespaces=NS
    ):
        name = parse_persName(resp)
        data.append(name)
    return data


def get_works(tree: etree.Element) -> list:
    data = []
    for work in tree.xpath("//mei:workList/mei:work", namespaces=NS):
        w = {k: 0 for k in MARCMUSPERF.values()}
        for inst in work.xpath("mei:perfMedium//mei:perfRes", namespaces=NS):
            inst_dict = parse_perfRes(instrument=inst)
            w.update(inst_dict)
        data.append(w)
    return data


def parse_perfRes(instrument: etree.Element) -> dict:
    codedval = instrument.get("codedval")
    instrument_label = MARCMUSPERF[codedval]
    count = int(instrument.get("count"))
    return {instrument_label: count}


def parse_tree(fp: Path) -> dict:
    tree = etree.parse(fp, parser=XMLParser())
    opera_id = tree.xpath("//mei:identifier[@type='CharltonWild']", namespaces=NS)[
        0
    ].text.strip()
    year = fp.stem
    title = tree.xpath("//mei:source/mei:bibl/mei:title", namespaces=NS)[0].text.strip()
    composer = get_composers(tree=tree)
    librettist = get_librettists(tree=tree)
    works = get_works(tree=tree)
    data = {
        opera_id: {
            "year": year,
            "title": title,
            "librettist": librettist,
            "composer": composer,
            "works": works,
        }
    }
    return data


@click.command()
@click.option("--decade", "-y", required=True)
@click.option("--directory", "-d", required=True)
def main(decade, directory):
    decade_prefix = decade[:3]
    decade = f"{decade_prefix}0s"
    data = {}
    for f in Path(directory).iterdir():
        if not f.stem.startswith(decade_prefix):
            continue
        opera = parse_tree(f)
        data.update(opera)

    # plotting the heatmap
    all_instrumentation = []
    for opera in data.values():
        i = []
        for work in opera["works"]:
            work_instrumentation = {
                k: v for k, v in work.items() if not k.startswith("Strings, bowed")
            }
            i.append(work_instrumentation)
        all_instrumentation.extend(i)
    hmp_df = pd.DataFrame(all_instrumentation)
    corr = hmp_df.corr(numeric_only=True)
    title_string = f"""{decade} Decade: Correlation of instruments playing together
(excluding bowed instruments)
"""
    sn.set_theme(style="white", palette="pastel")
    fig, (ax1, ax2) = plt.subplots(ncols=1, nrows=2, figsize=(12, 12))
    hm = sn.heatmap(
        ax=ax1,
        data=corr,
        cmap="crest",
        vmax=0.3,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.5, "label": "correlation coefficient"},
    ).set(title=title_string)

    # Plotting the bar plot
    instrument_parts = []
    for metadata in data.values():
        title = metadata["title"]
        year = metadata["year"]
        for w in metadata["works"]:
            instruments = [
                (inst, value)
                for inst, value in w.items()
                if not inst.startswith("Strings, bowed")
            ]
            for inst, count in instruments:
                if count > 0:
                    for i in range(count):
                        opera_data = {
                            "title": title,
                            "year": year,
                            "instrument": inst,
                        }
                        instrument_parts.append(opera_data)

    df_rows = sorted(instrument_parts, key=lambda d: d["year"])
    df_rows = sorted(df_rows, key=lambda d: d["instrument"])
    bar_df = pd.DataFrame(df_rows)
    title_string = f"""{decade} Decade: Total number of instruments per opera number
(excluding bowed instruments)
"""
    sn.histplot(
        bar_df,
        ax=ax2,
        y="title",
        hue="instrument",
        multiple="fill",
        stat="proportion",
        discrete=True,
        shrink=0.8,
        palette="Spectral",
    )
    sn.move_legend(ax2, "upper left", bbox_to_anchor=(1, 1))
    plt.xticks(rotation=90)
    ax2.set(
        ylabel="Opera",
        xlabel="Proportion of parts written for an instrument",
        title=title_string,
    )

    of = DIR.joinpath(f"{decade}.png")
    fig.tight_layout()
    fig.savefig(of)


if __name__ == "__main__":
    main()
