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
    title = tree.xpath("//mei:source/mei:bibl/mei:title", namespaces=NS)[0].text.strip()
    composer = get_composers(tree=tree)
    librettist = get_librettists(tree=tree)
    works = get_works(tree=tree)
    data = {
        opera_id: {
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
    title_string = f"""{decade} opéras-comiques: Correlation of instruments playing together
(excluding bowed instruments)
"""
    sn.set_theme(style="white", palette="pastel")
    fig, (ax1, ax2) = plt.subplots(ncols=2, nrows=1, figsize=(16, 12))
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
    opera_df_rows = []
    for opera_id, metadata in data.items():
        title = metadata["title"]
        opera_counter = Counter(
            {v: 0 for v in MARCMUSPERF.values() if not v.startswith("Strings, bowed")}
        )
        for w in metadata["works"]:
            for inst, value in w.items():
                if inst.startswith("Strings, bowed"):
                    continue
                for i in range(value):
                    opera_counter.update([inst])
        for k, v in opera_counter.items():
            opera_data = {
                "label": f"{title} ({opera_id})",
                "number of times used": v,
                "instrument": k,
            }
            opera_df_rows.append(opera_data)
    bar_df = pd.DataFrame(opera_df_rows)
    title_string = f"""{decade} opéras-comiques: Total number of instrument parts per number, per opera
(excluding bowed instruments)
"""
    sn.barplot(
        bar_df,
        ax=ax2,
        x="label",
        y="number of times used",
        hue="instrument",
        dodge=False,
        orient="x",
    ).set(title=title_string)
    sn.move_legend(ax2, "upper left", bbox_to_anchor=(1, 1))
    plt.xticks(rotation=90)

    of = DIR.joinpath(f"{decade}.png")
    fig.tight_layout()
    fig.savefig(of)


if __name__ == "__main__":
    main()
