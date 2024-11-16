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


XML_DIR = Path(__file__).parent.parent.joinpath("xml-files")

NS = {"mei": "http://www.music-encoding.org/ns/mei"}


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
        instrumentation = {k: 0 for k in MARCMUSPERF.values()}
        for inst in work.xpath("mei:perfMedium//mei:perfRes", namespaces=NS):
            inst_dict = parse_perfRes(instrument=inst)
            instrumentation.update(inst_dict)
        n = int(work.get("n"))
        title = work.xpath("mei:title", namespaces=NS)[0].text
        w = {"n": n, "title": title, "instrumentation": instrumentation}
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
    work_list = get_works(tree=tree)

    sums = {k: 0 for k in MARCMUSPERF.values()}
    for work in work_list:
        for instrument, count in work["instrumentation"].items():
            if count > 0:
                sums[instrument] += 1

    return {
        "charlton_id": opera_id,
        "year": year,
        "title": title,
        # "librettist": librettist,
        # "composer": composer,
        "works": work_list,
        "deployments": sums,
    }


IGNORED_PREFIXES = ["Strings", "Keyboard"]


class Datasets:

    def __init__(self, dir: Path = XML_DIR, prefix: str | None = None) -> None:
        if prefix:
            files = [fp for fp in dir.iterdir() if fp.startswith(prefix)]
        else:
            files = [fp for fp in dir.iterdir()]
        self.opera_dicts = [parse_tree(fp=fp) for fp in files]

    @staticmethod
    def _get_list_of_instruments_to_ignore(l: list) -> list:
        instruments_to_ignore = []
        for x in l:
            for y in MARCMUSPERF.values():
                if y.startswith(x):
                    instruments_to_ignore.append(y)
        return instruments_to_ignore

    def build_sparse_work_df(self, ignore: list = IGNORED_PREFIXES) -> list[dict]:
        work_list = []
        instrumts_to_ignore = self._get_list_of_instruments_to_ignore(l=ignore)
        for d in self.opera_dicts:
            for w in d["works"]:
                i = w["instrumentation"]
                work_list.append(
                    {k: v for k, v in i.items() if not k in instrumts_to_ignore}
                )
        return work_list

    def build_dense_work_df(
        self, ignore: list = IGNORED_PREFIXES, binary: bool = False
    ) -> list[dict]:
        work_list = []
        reverse_index = {v: k for k, v in MARCMUSPERF.items()}
        instruments_to_ignore = self._get_list_of_instruments_to_ignore(l=ignore)
        for d in self.opera_dicts:
            title = d["title"]
            year = d["year"]
            for w in d["works"]:
                instrumentation = w["instrumentation"]
                work_n = w["n"]
                for instrument, count in instrumentation.items():
                    if instrument in instruments_to_ignore:
                        continue
                    if count > 0:
                        if not binary:
                            for _ in range(count):
                                work_list.append(
                                    {
                                        "title": title,
                                        "year": year,
                                        "work_number": work_n,
                                        "instrument": instrument,
                                        "instrument_codedval": reverse_index[
                                            instrument
                                        ],
                                    }
                                )
                        else:
                            work_list.append(
                                {
                                    "title": title,
                                    "year": year,
                                    "work_number": work_n,
                                    "instrument": instrument,
                                    "instrument_codedval": reverse_index[instrument],
                                }
                            )

        work_list = sorted(work_list, key=lambda d: d["year"])
        work_list = sorted(work_list, key=lambda d: d["instrument_codedval"])
        return work_list

    def build_dense_opera_averages_df(self, ignore: list = []) -> list[dict]:
        opera_list = []
        reverse_index = {v: k for k, v in MARCMUSPERF.items()}
        sections = {
            "Strings, bowed": "bowed",
            "Strings, plucked": "plucked",
            "Brass": "brass",
            "Woodwinds": "woodwind",
            "Percussion": "percussion",
            "Keyboard": "keys",
        }
        instrumts_to_ignore = self._get_list_of_instruments_to_ignore(l=ignore)
        for d in self.opera_dicts:
            n_works = len(d["works"])
            averages = {
                k: (v / n_works)
                for k, v in d["deployments"].items()
                if k not in instrumts_to_ignore
            }
            for instrument, avg in averages.items():
                # Get the instrument's section
                for k, v in sections.items():
                    if instrument.startswith(k):
                        section = v
                        break
                opera_list.append(
                    {
                        "year": d["year"][:4],
                        "date": d["year"],
                        "instrument": instrument,
                        "instrument_codedval": reverse_index[instrument],
                        "proportion": avg,
                        "section": section,
                    }
                )
        opera_list = sorted(opera_list, key=lambda d: d["year"])
        return opera_list

    def build_sparse_opera_averages_df(self, ignore: list = []) -> list[dict]:
        opera_list = []
        instrumts_to_ignore = self._get_list_of_instruments_to_ignore(l=ignore)
        for metadata in self.opera_dicts:
            n_works = len(metadata["works"])
            averages = {
                k: (v / n_works)
                for k, v in metadata["deployments"].items()
                if k not in instrumts_to_ignore
            }
            opera = {
                "date": metadata["year"],
                "year": metadata["year"][:4],
                "charlton_id": metadata["charlton_id"],
                "title": metadata["title"],
            } | averages
            opera_list.append(opera)
        opera_list = sorted(opera_list, key=lambda d: d["date"])
        return opera_list
