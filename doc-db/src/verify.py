from lxml import etree
from lxml.etree import XMLParser
from pathlib import Path
from collections import Counter
from pprint import pprint
from perfRes import MARCMUSPERF

NS = {"mei": "http://www.music-encoding.org/ns/mei"}

counter = Counter()


for f in Path("xml-files").iterdir():
    tree = etree.parse(f, parser=XMLParser())
    for pr in tree.xpath("//mei:perfRes", namespaces=NS):
        codedval = pr.get("codedval")
        if not codedval:
            print(f)
            print("codedval: ", codedval)
            raise KeyError
        if codedval not in list(MARCMUSPERF.keys()):
            print(f)
            print("codedval: ", codedval)
            raise KeyError
        counter.update([pr.get("codedval")])


pprint(counter)
