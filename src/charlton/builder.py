from pathlib import Path
import csv
from collections import namedtuple
import re
import json
from operator import itemgetter


CHARLTON_DB_DIR = Path(__file__).parent.parent.parent.joinpath("charlton-db")
DATA_DB_DIR = Path(__file__).parent.parent.parent.joinpath("data")
AUTEURS = CHARLTON_DB_DIR.joinpath("auteurs.tsv")
COMPOSITEURS = CHARLTON_DB_DIR.joinpath("compositeurs.tsv")
REPRESENTATIONS = DATA_DB_DIR.joinpath("representations-2022-03-24.csv")

Person = namedtuple("Author", field_names=["surname", "given_names", "id"])
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
            d = [i.strip() for i in row]
            dataset.append(NamedTuple(*d))
        return dataset


def parse_csv(filepath: Path, NamedTuple: namedtuple) -> list[RepDatasetRow]:
    with open(filepath) as fd:
        reader = csv.reader(fd)
        reader.__next__()
        dataset = []
        for row in reader:
            d = [i.strip() for i in row]
            dataset.append(NamedTuple(*d))
        return dataset


def match_person(namestring: str, person_data: list[Person]) -> Person | None:
    surname, given_names = namestring, None
    matches = re.search(pattern=r"(^[^,]+),\s(.*)", string=namestring)
    if matches:
        surname, given_names = matches.group(1), matches.group(2)
    for person in person_data:
        if person.surname == surname and person.given_names == given_names:
            return person
        elif person.surname == surname:
            return person


def main():
    author_data = parse_tsv(filepath=AUTEURS, NamedTuple=Person)
    composer_data = parse_tsv(filepath=COMPOSITEURS, NamedTuple=Person)

    preliminary_people = author_data + composer_data

    print(preliminary_people)

    peeps = {}
    for p in preliminary_people:
        key = p.surname
        if p.given_names:
            key = f"{p.surname}, {p.given_names}"
        peeps.update({key: p})

    from pprint import pprint

    pprint(peeps)

    # rep_dataset = parse_csv(filepath=REPRESENTATIONS, NamedTuple=RepDatasetRow)

    # works = {}
    # performances = []
    # for row in rep_dataset:
    #     composer1 = match_person(namestring=row.composer1, person_data=composer_data)
    #     composer2 = match_person(namestring=row.composer2, person_data=composer_data)
    #     composer3 = match_person(namestring=row.composer3, person_data=composer_data)
    #     author1 = match_person(namestring=row.author1, person_data=author_data)
    #     author2 = match_person(namestring=row.author2, person_data=author_data)
    #     author3 = match_person(namestring=row.author3, person_data=author_data)

    #     composers = [c for c in [composer1, composer2, composer3] if c]
    #     authors = [c for c in [author1, author2, author3] if c]

    #     work = Work(
    #         charlton_id=row.charlton_id,
    #         creation_date=row.creation_date,
    #         title=row.title,
    #         is_ballet=row.is_ballet,
    #         is_borrowed=row.is_borrowed,
    #         n_acts=row.n_acts,
    #         composers=composers,
    #         authors=authors,
    #     )
    #     works.update({work.charlton_id: work})

    #     performance = Performance(date=row.date, charlton_id=row.charlton_id)
    #     performances.append(performance)


if __name__ == "__main__":
    main()
