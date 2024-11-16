from lxml import etree
from lxml.etree import XMLParser
from pathlib import Path
from perfRes import MARCMUSPERF


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
        id = work.get("{http://www.w3.org/XML/1998/namespace}id")
        w = {"n": n, "id": id, "title": title, "instrumentation": instrumentation}
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
