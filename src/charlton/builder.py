from pathlib import Path
import csv
from collections import namedtuple
from datetime import date
import json


CHARLTON_DB_DIR = Path(__file__).parent.parent.parent.joinpath("charlton-db")
DATA_DB_DIR = Path(__file__).parent.parent.parent.joinpath("data")
AUTEURS = CHARLTON_DB_DIR.joinpath("auteurs.tsv")
COMPOSITEURS = CHARLTON_DB_DIR.joinpath("compositeurs.tsv")
CHARLTON_WORKS = CHARLTON_DB_DIR.joinpath("some_works_charlton.csv")
REPRESENTATIONS = DATA_DB_DIR.joinpath("representations-2022-03-24.csv")

Person = namedtuple(
    "Person", field_names=["surname", "given_names", "id"], defaults=[None, None, None]
)
RepDatasetRow = namedtuple(
    "RepDatasetRow",
    field_names=[
        "date",
        "charlton_id",
        "source",
        "title",
        "creation_date",
        "is_ballet",
        "is_borrowed",
        "n_acts",
        "composer1",
        "composer2",
        "composer3",
        "author1",
        "author2",
        "author3",
        "rewriter1",
        "rewriter2",
        "rewriter3",
    ],
)

Work = namedtuple(
    "Work",
    field_names=[
        "charlton_id",
        "creation_date",
        "title",
        "is_ballet",
        "is_borrowed",
        "n_acts",
        "composers",
        "authors",
    ],
)

CharltonWork = namedtuple(
    "CharltonWork",
    field_names=[
        "title",
        "creation_day",
        "creation_month",
        "creation_year",
        "acts",
        "author1",
        "author2",
        "author3",
        "author4",
        "author_arranger1",
        "author_arranger2",
        "author_arranger3",
        "composer1",
        "composer2",
        "composer3",
        "composer4",
        "composer_arranger1",
        "composer_arranger2",
    ],
)

Performance = namedtuple(
    "Performance",
    field_names=["date", "charlton_id"],
)


def strip(t: str) -> str:
    return t.strip()


def parse_tsv(filepath: Path, NamedTuple: namedtuple) -> list[Person]:
    with open(filepath) as fd:
        reader = csv.reader(fd, delimiter="\t", quotechar='"')
        dataset = []
        for row in reader:
            d = []
            for c in row:
                v = c.strip()
                if v == "":
                    d.append(None)
                else:
                    d.append(v)
            dataset.append(NamedTuple(*d))
        return dataset


def parse_csv(filepath: Path, NamedTuple: namedtuple) -> list[RepDatasetRow]:
    with open(filepath) as fd:
        reader = csv.reader(fd)
        reader.__next__()
        dataset = []
        for row in reader:
            d = []
            for c in row:
                v = c.strip()
                if v == "":
                    d.append(None)
                else:
                    d.append(v)
            dataset.append(NamedTuple(*d))
        return dataset


class Dataset:
    def __init__(self, persons: dict, fp: Path = REPRESENTATIONS):
        self.rep_list = parse_csv(filepath=fp, NamedTuple=RepDatasetRow)
        self.len = len(self.rep_list)
        self.person_dict = persons
        self.composer_attribute_names = ["composer1", "composer2", "composer3"]
        self.author_attribute_names = ["author1", "author2", "author3"]
        self.rewriter_attribute_names = ["rewriter1", "rewriter2", "rewriter3"]

    def person_matcher(self, namestring: str) -> Person | None:
        if namestring and namestring != "0":
            return self.person_dict[namestring]

    def _get_people(self, row: RepDatasetRow, attribute_names: list) -> set:
        values = [getattr(row, name) for name in attribute_names]
        people = set([self.person_matcher(p) for p in values])
        if None in people:
            people.remove(None)
        return sorted(people)

    def get_work(self, n: int) -> Work:
        composers = self.get_composers(n)
        authors = self.get_authors(n)
        # rewriters = self.get_rewriters(n)
        row = self.rep_list[n]
        return Work(
            charlton_id=row.charlton_id,
            creation_date=str(date.fromisoformat(row.creation_date[:10])),
            title=row.title,
            is_ballet=row.is_ballet,
            is_borrowed=row.is_borrowed,
            n_acts=row.n_acts,
            composers=composers,
            authors=authors,
        )

    def get_composers(self, n: int) -> set:
        row = self.rep_list[n]
        return self._get_people(row=row, attribute_names=self.composer_attribute_names)

    def get_authors(self, n: int) -> set:
        row = self.rep_list[n]
        return self._get_people(row=row, attribute_names=self.author_attribute_names)

    def get_rewriters(self, n: int) -> set:
        row = self.rep_list[n]
        return self._get_people(row=row, attribute_names=self.rewriter_attribute_names)


def main():
    # Step 1. Process people
    author_data = parse_tsv(filepath=AUTEURS, NamedTuple=Person)
    composer_data = parse_tsv(filepath=COMPOSITEURS, NamedTuple=Person)
    preliminary_people = author_data + composer_data
    all_persons_set = set()
    TempPerson = namedtuple(
        "TempPerson",
        field_names=["full_name", "surname", "given_names"],
        defaults=[None, None, None],
    )
    for p in preliminary_people:
        full_name = p.surname
        if p.given_names:
            full_name = f"{p.surname}, {p.given_names}"
        temp_person_tuple = TempPerson(full_name, p.surname, p.given_names)
        all_persons_set.add(temp_person_tuple)
    all_persons_dict = {}
    for i, p in enumerate(sorted(all_persons_set)):
        key = p.full_name
        tup = Person(surname=p.surname, given_names=p.given_names, id=i)
        all_persons_dict.update({key: tup})

    # Step 2. Synthesize representations dataset with people dataset
    works = {}
    dataset = Dataset(persons=all_persons_dict)
    for n in range(dataset.len):
        work = dataset.get_work(n=n)
        works.update({work.charlton_id: work})

    # Step 3. Relate works to performances
    performances = {}
    for n, row in enumerate(dataset.rep_list):
        work = dataset.get_work(n=n)
        perf_date = str(date.fromisoformat(row.date[:10]))
        if not performances.get(perf_date):
            performances.update(
                {perf_date: {"source": row.source, "date": perf_date, "works": []}}
            )
        performances[perf_date]["works"].append(work.charlton_id)

    with open("data/perfomances.json", "w") as f:
        json.dump(performances, fp=f, indent=4)

    works_json = {}
    for id, w in sorted(works.items()):
        d = {k: v for k, v in zip(Work._fields, w)}
        composers = [{k: v for k, v in zip(Person._fields, c)} for c in d["composers"]]
        authors = [{k: v for k, v in zip(Person._fields, c)} for c in d["authors"]]
        d.update({"composers": composers})
        d.update({"authors": authors})
        d.update({"adapters": [], "arrangers": []})
        works_json.update({id: d})
    with open("data/works_from_rep_dataset.json", "w") as f:
        json.dump(works_json, fp=f, indent=4, ensure_ascii=False)

    with open("data/persons.json", "w") as f:
        persons = {}
        for name_string, d in all_persons_dict.items():
            p = Person(*d)
            persons.update(
                {
                    p.id: {
                        "id": p.id,
                        "surname": p.surname,
                        "given_names": p.given_names,
                        "name_string": name_string,
                        "wikidata_id": None,
                        "biblissima_id": None,
                        "bnf_id": None,
                    }
                }
            )
        json.dump(persons, fp=f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
