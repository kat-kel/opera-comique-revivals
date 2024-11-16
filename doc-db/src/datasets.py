from pathlib import Path
from perfRes import MARCMUSPERF
from xml_parser import parse_tree


XML_DIR = Path(__file__).parent.parent.joinpath("xml-files")


IGNORED_PREFIXES = ["Strings", "Keyboard"]


class Datasets:

    def __init__(
        self,
        dir: Path = XML_DIR,
        prefix: str | None = None,
        files: list[Path] | None = None,
    ) -> None:
        if not files:
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
                work_id = w["id"]
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
                                        "work_id": work_id,
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
                                    "work_id": work_id,
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
