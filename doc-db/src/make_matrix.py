from lxml import etree
from lxml.etree import XMLParser
from datetime import date
from pathlib import Path
from perfRes import MARCMUSPERF
import seaborn as sn
import pandas as pd
import click
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


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
    try:
        tree = etree.parse(fp, parser=XMLParser())
    except Exception as e:
        print(f"\n\n{fp}\n")
        raise e
    opera_id = tree.xpath("//mei:identifier[@type='CharltonWild']", namespaces=NS)[
        0
    ].text.strip()
    year = fp.stem
    title = tree.xpath("//mei:source/mei:bibl/mei:title", namespaces=NS)[0].text.strip()
    # composer = get_composers(tree=tree)
    # librettist = get_librettists(tree=tree)
    works = get_works(tree=tree)
    data = {
        opera_id: {
            "year": year,
            "title": title,
            # "librettist": librettist,
            # "composer": composer,
            "works": works,
        }
    }
    return data


def list_instrumentation_by_work(data: dict) -> list:
    all_instrumentation = []
    for opera in data.values():
        i = []
        for work in opera["works"]:
            work_instrumentation = {
                k: v for k, v in work.items() if not k.startswith("Strings, bowed")
            }
            i.append(work_instrumentation)
        all_instrumentation.extend(i)
    return all_instrumentation


def list_part_with_metadata(data) -> list:
    reverse_index = {v: k for k, v in MARCMUSPERF.items()}
    instrument_parts = []
    for metadata in data.values():
        title = metadata["title"]
        year = metadata["year"]
        for w in metadata["works"]:
            for inst, count in w.items():
                if count > 0:
                    for i in range(count):
                        opera_data = {
                            "title": title,
                            "year": year,
                            "instrument": inst,
                            "instrument_codedval": reverse_index[inst],
                        }
                        instrument_parts.append(opera_data)
    instrument_parts = sorted(instrument_parts, key=lambda d: d["year"])
    instrument_parts = sorted(instrument_parts, key=lambda d: d["instrument_codedval"])
    return instrument_parts


def list_instruments_proportions(data) -> list:
    operas = []
    instrument_list = MARCMUSPERF.values()
    for opera in data.values():
        year = opera["year"]
        n_works = len(opera["works"])
        counter = {k: 0 for k in instrument_list}
        for work in opera["works"]:
            for inst, count in work.items():
                current_count = counter[inst]
                if count > 0:
                    counter.update({inst: current_count + 1})
        for inst, count in counter.items():
            counter.update({inst: count / n_works})
        counter.update({"year": year})
        operas.append(counter)
    operas = sorted(operas, key=lambda d: d["year"])

    instruments = []
    for opera in operas:
        year = int(opera["year"][:4])
        for k in instrument_list:
            inst_proportion = opera[k]
            instruments.append(
                {"year": year, "instrument": k, "proportion": inst_proportion}
            )

    return instruments


def plot_heatmap(df: pd.DataFrame, ax, title_string: str):
    color_palette = sn.color_palette("BuPu", as_cmap=True)
    corr = df.corr(numeric_only=True)
    hm = sn.heatmap(
        ax=ax,
        data=corr,
        cmap=color_palette,
        vmax=0.3,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.5, "label": "correlation coefficient"},
    ).set(title=title_string)
    return hm


def make_palette_by_instrument_group():
    def build_label_hex_pairs(prefix: str, color: str) -> dict:
        labels = [v for k, v in MARCMUSPERF.items() if k.startswith(prefix)]
        hex_list = sn.color_palette(color, len(labels)).as_hex()
        return {k: v for k, v in zip(labels, hex_list)}

    # Select labels from Color Brewer library
    woodwinds_kw = build_label_hex_pairs(prefix="w", color="Greens")
    plucked_kw = build_label_hex_pairs(prefix="t", color="rocket")
    bowed_kw = build_label_hex_pairs(prefix="s", color="Greys")
    percussion_kw = build_label_hex_pairs(prefix="p", color="Blues")
    keys_kw = build_label_hex_pairs(prefix="k", color="Purples")
    brass_kw = build_label_hex_pairs(prefix="b", color="Reds")

    # voices_kw = build_label_hex_pairs(prefix="v", color="YlOrBr")

    kw = brass_kw | keys_kw | percussion_kw | bowed_kw | plucked_kw | woodwinds_kw
    return kw


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


def exclude_rows_by_values(df, col, values):
    return df[~df[col].isin(values)]


def include_rows_by_values(df, col, values):
    return df[df[col].isin(values)]


STRINGS = [v for v in MARCMUSPERF.values() if v.startswith("Strings, plucked")]
WOOWDIND = [v for v in MARCMUSPERF.values() if v.startswith("Woodwind")]
BRASS = [v for v in MARCMUSPERF.values() if v.startswith("Brass")]
PERCUSSION = [v for v in MARCMUSPERF.values() if v.startswith("Percussion")]


def plot_line_chart(df: pd.DataFrame, ax):
    color_palette = make_palette_by_instrument_group()
    plot = sn.lineplot(
        data=df,
        ax=ax,
        x="year",
        y="proportion",
        hue="instrument",
        palette=color_palette,
    )
    ax.set(ylim=(0, 1))
    sn.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
    return plot


@click.group()
def cli():
    pass


@cli.command("barchart")
@click.option(
    "--directory",
    "-d",
    default="xml-files",
    help="Path to the directory containing MEI-XML files",
)
def barchart_command(directory):
    data = {}
    for f in Path(directory).iterdir():
        opera = parse_tree(f)
        data.update(opera)

    # Setting up the plot
    sn.set_theme(style="white", palette="pastel")
    fig = plt.figure(figsize=(32, 18))
    gs = gridspec.GridSpec(4, 2)
    ax0 = plt.subplot(gs[0, 0])
    ax1 = plt.subplot(gs[1, 0])
    ax2 = plt.subplot(gs[2, 0])
    ax3 = plt.subplot(gs[3, 0])
    ax4 = plt.subplot(gs[:4, 1])

    # Plotting bar chart
    parts = list_part_with_metadata(data=data)
    bar_df = pd.DataFrame(parts)
    title_string = "Proportion of parts in an opera per instrument"
    plot_barchart(df=bar_df, ax=ax4, title_string=title_string)
    plt.xticks(rotation=90)

    # Plotting line charts
    data = list_instruments_proportions(data=data)
    line_df = pd.DataFrame.from_dict(data)
    b_df = include_rows_by_values(df=line_df, col="instrument", values=BRASS)
    plot_line_chart(df=b_df, ax=ax0)
    w_df = include_rows_by_values(df=line_df, col="instrument", values=WOOWDIND)
    w_df = exclude_rows_by_values(
        df=w_df,
        col="instrument",
        values=["Woodwinds - Bass clarinet"],
    )
    plot_line_chart(df=w_df, ax=ax1)
    p_df = include_rows_by_values(df=line_df, col="instrument", values=PERCUSSION)
    plot_line_chart(df=p_df, ax=ax2)
    s_df = include_rows_by_values(df=line_df, col="instrument", values=STRINGS)
    plot_line_chart(df=s_df, ax=ax3)

    # Save figure
    of = DIR.joinpath(f"allYears.png")
    fig.tight_layout()
    fig.savefig(of)


@cli.command("decade")
@click.option("--decade", "-y", required=True, help="First 3 digits of the decade")
@click.option(
    "--directory",
    "-d",
    default="xml-files",
    help="Path to the directory containing MEI-XML files",
)
def decade_command(decade, directory):
    decade_prefix = decade[:3]
    decade = f"{decade_prefix}0s"
    data = {}
    for f in Path(directory).iterdir():
        if not f.stem.startswith(decade_prefix):
            continue
        opera = parse_tree(f)
        data.update(opera)

    # Setting up the plot
    sn.set_theme(style="white", palette="pastel")
    fig, (ax1, ax2) = plt.subplots(ncols=1, nrows=2, figsize=(12, 12))

    # Plotting the heatmap
    work_instrumentation = list_instrumentation_by_work(data)
    hmp_df = pd.DataFrame(work_instrumentation)
    title_string = f"{decade} Decade: Correlation of instruments playing together\n(excluding bowed instruments)"
    plot_heatmap(df=hmp_df, ax=ax1, title_string=title_string)

    # Plotting bar chart
    parts = list_part_with_metadata(data=data)
    bar_df = pd.DataFrame(parts)
    title_string = f"{decade} Decade: Proportion of parts in an opera per instrument"
    plot_barchart(df=bar_df, ax=ax2, title_string=title_string)
    plt.xticks(rotation=90)

    # Save figure
    of = DIR.joinpath(f"{decade}.png")
    fig.tight_layout()
    fig.savefig(of)


if __name__ == "__main__":
    cli()
