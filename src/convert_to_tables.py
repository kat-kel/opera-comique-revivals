import click
from pathlib import Path
import json
import duckdb


DATA_DIR = Path(__file__).parent.parent.joinpath("data")

WORKS_JSON = DATA_DIR.joinpath("works_from_rep_dataset.json")
PERFORMANCES_JSON = DATA_DIR.joinpath("perfomances.json")
PERSONS_JSON = DATA_DIR.joinpath("persons.json")

DUCKDB_PATH = DATA_DIR.joinpath("opera-comique-revivals.duckdb")


class TableBase:
    def __init__(
        self, conn: duckdb.DuckDBPyConnection, name: str, seq: str, create_stmt: str
    ) -> None:
        self.conn = conn
        self.name = name
        self.seq = seq
        self.create_stmt = create_stmt

    def show(self) -> None:
        print(self.conn.table(self.name))

    def drop(self) -> None:
        self.conn.execute(f"DROP TABLE IF EXISTS {self.name}")
        self.conn.execute(f"DROP SEQUENCE IF EXISTS {self.seq}")

    def create(self) -> None:
        self.drop()
        self.conn.execute(self.create_stmt)
        self.conn.execute(f"CREATE SEQUENCE {self.seq}")


class PerformanceTable(TableBase):
    name = "Performances"

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        seq = "PerformanceSequence"
        create_stmt = f"""
CREATE TABLE {self.name} (
    id integer primary key,
    date date not null,
    work_performed integer not null,
    primary_source varchar
)
        """
        super().__init__(conn, self.name, seq, create_stmt)

    def insert(self, row: dict) -> None:
        stmt = f"""
INSERT INTO {self.name} (id, date, work_performed, primary_source)
VALUES (
    nextval('{self.seq}'),
    $date,
    $work,
    $primary_source
)
"""
        self.conn.execute(stmt, row)


class ActionTabel(TableBase):
    name = "Actions"

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        seq = "ActionSequence"
        create_stmt = f"""
CREATE TABLE {self.name} (
    id integer primary key,
    creative_actor integer not null,
    work_produced integer not null,
    as_librettist boolean not null default false,
    as_composer boolean not null default false
);
"""
        super().__init__(conn, self.name, seq, create_stmt)

    def insert_composer(self, row: dict) -> None:
        stmt = f"""
INSERT INTO {self.name} (id, creative_actor, work_produced, as_composer)
VALUES (
    nextval('{self.seq}'),
    $person,
    $work,
    true
)
        """
        self.conn.execute(stmt, row)

    def insert_librettist(self, row: dict) -> None:
        stmt = f"""
INSERT INTO {self.name} (id, creative_actor, work_produced, as_librettist)
VALUES (
    nextval('{self.seq}'),
    $person,
    $work,
    true
)
        """
        self.conn.execute(stmt, row)


class PersonsTable(TableBase):
    name = "Persons"

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        seq = "PersonSequence"
        create_stmt = f"""
CREATE TABLE {self.name} (
    id integer primary key,
    surname varchar(255),
    given_names varchar(255),
    wikidata_id varchar(80)
);
"""
        super().__init__(conn, self.name, seq, create_stmt)

    def insert(self, row: dict) -> None:
        stmt = f"""
INSERT INTO {self.name} (id, surname, given_names)
VALUES (
    $id,
    $surname,
    $given_names
);
"""
        clean_row = {
            "id": int(row["id"]),
            "surname": row["surname"],
            "given_names": row["given_names"],
        }
        self.conn.execute(stmt, clean_row)


class ProductionsTable(TableBase):
    name = "Productions"

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        seq = "ProductionSequence"
        create_stmt = f"""
CREATE TABLE {self.name} (
    id integer primary key,
    charlton_id integer,
    is_revision boolean default false,
    is_borrowed boolean,
    n_acts integer not null,
    creation_date date not null,
    title varchar(255) not null
);
"""
        super().__init__(conn, self.name, seq, create_stmt)

    def insert(self, row: dict) -> None:
        stmt = f"""
INSERT INTO {self.name} (id, charlton_id, is_borrowed, n_acts, creation_date, title)
VALUES (
    nextval('{self.seq}'),
    $charlton_id,
    $is_borrowed,
    $n_acts,
    $creation_date,
    $title
);
"""
        clean_row = {
            k: v
            for k, v in row.items()
            if k
            in [
                "charlton_id",
                "creation_date",
                "title",
                "is_borrowed",
                "n_acts",
            ]
        }
        self.conn.execute(stmt, clean_row)

    @classmethod
    def get_work_id(cls, conn: duckdb.DuckDBPyConnection, charlton_id: int) -> int:
        return conn.table(cls.name).filter(f"charlton_id = {charlton_id}").fetchone()[0]


def json_data(fp: Path) -> dict:
    with open(fp) as f:
        return json.load(f)


def get_connection(ctx) -> duckdb.DuckDBPyConnection:
    return ctx.obj["CONN"]


@click.group()
@click.pass_context
def cli(
    ctx,
):
    ctx.ensure_object(dict)
    ctx.obj["CONN"] = duckdb.connect(str(DUCKDB_PATH))


def persons(ctx):
    persons_dataset = json_data(PERSONS_JSON)
    table = PersonsTable(conn=get_connection(ctx))
    table.create()
    for v in persons_dataset.values():
        table.insert(v)


def works(ctx):
    works_dataset = json_data(WORKS_JSON)
    table = ProductionsTable(conn=get_connection(ctx))
    table.create()
    for v in works_dataset.values():
        table.insert(v)


def actions(ctx):
    conn = get_connection(ctx)
    table = ActionTabel(conn=conn)
    table.create()
    works_dataset = json_data(fp=WORKS_JSON)
    for v in works_dataset.values():
        charlton_id = v["charlton_id"]
        work_id = ProductionsTable.get_work_id(conn=conn, charlton_id=charlton_id)
        for person in v["composers"]:
            person_id = person["id"]
            row = {"person": person_id, "work": work_id}
            table.insert_composer(row=row)
        for person in v["authors"]:
            person_id = person["id"]
            row = {"person": person_id, "work": work_id}
            table.insert_librettist(row=row)


def performances(ctx):
    conn = get_connection(ctx)
    table = PerformanceTable(conn=conn)
    table.create()
    performances_dataset = json_data(fp=PERFORMANCES_JSON)
    for v in performances_dataset.values():
        for charlton_id in v["works"]:
            work_id = ProductionsTable.get_work_id(conn=conn, charlton_id=charlton_id)
            row = {"date": v["date"], "primary_source": v["source"], "work": work_id}
            table.insert(row=row)


@cli.command("performances")
@click.pass_context
def performances_action(ctx):
    performances(ctx)


@cli.command("works")
@click.pass_context
def works_action(ctx):
    works(ctx)


@cli.command("persons")
@click.pass_context
def persons_action(ctx):
    persons(ctx)


@cli.command("actions")
@click.pass_context
def actions_action(ctx):
    actions(ctx)


@cli.command("build")
@click.pass_context
def build_action(ctx):
    persons(ctx)
    works(ctx)
    performances(ctx)
    actions(ctx)


if __name__ == "__main__":
    cli()
