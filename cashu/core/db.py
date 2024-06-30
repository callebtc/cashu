import asyncio
import datetime
import os
import time
from contextlib import asynccontextmanager
from typing import Optional, Union

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy_aio.base import AsyncConnection
from sqlalchemy_aio.strategy import ASYNCIO_STRATEGY  # type: ignore

POSTGRES = "POSTGRES"
COCKROACH = "COCKROACH"
SQLITE = "SQLITE"


class Compat:
    type: Optional[str] = "<inherited>"
    schema: Optional[str] = "<inherited>"

    def interval_seconds(self, seconds: int) -> str:
        if self.type in {POSTGRES, COCKROACH}:
            return f"interval '{seconds} seconds'"
        elif self.type == SQLITE:
            return f"{seconds}"
        return "<nothing>"

    @property
    def timestamp_now(self) -> str:
        if self.type in {POSTGRES, COCKROACH}:
            return "now()"
        elif self.type == SQLITE:
            # return "(strftime('%s', 'now'))"
            return str(int(time.time()))
        return "<nothing>"

    @property
    def serial_primary_key(self) -> str:
        if self.type in {POSTGRES, COCKROACH}:
            return "SERIAL PRIMARY KEY"
        elif self.type == SQLITE:
            return "INTEGER PRIMARY KEY AUTOINCREMENT"
        return "<nothing>"

    @property
    def references_schema(self) -> str:
        if self.type in {POSTGRES, COCKROACH}:
            return f"{self.schema}."
        elif self.type == SQLITE:
            return ""
        return "<nothing>"

    @property
    def big_int(self) -> str:
        if self.type in {POSTGRES}:
            return "BIGINT"
        return "INT"


class Connection(Compat):
    def __init__(self, conn: AsyncConnection, txn, typ, name, schema):
        self.conn = conn
        self.txn = txn
        self.type = typ
        self.name = name
        self.schema = schema

    def rewrite_query(self, query) -> str:
        if self.type in {POSTGRES, COCKROACH}:
            query = query.replace("%", "%%")
            query = query.replace("?", "%s")
        return query

    async def fetchall(self, query: str, values: tuple = ()) -> list:
        result = await self.conn.execute(self.rewrite_query(query), values)
        return await result.fetchall()

    async def fetchone(self, query: str, values: tuple = ()):
        result = await self.conn.execute(self.rewrite_query(query), values)
        row = await result.fetchone()
        await result.close()
        return row

    async def execute(self, query: str, values: tuple = ()):
        return await self.conn.execute(self.rewrite_query(query), values)


class Database(Compat):
    def __init__(self, db_name: str, db_location: str):
        self.name = db_name
        self.db_location = db_location
        self.db_location_is_url = "://" in self.db_location
        if self.db_location_is_url:
            # raise Exception("Remote databases not supported. Use SQLite.")
            database_uri = self.db_location

            if database_uri.startswith("cockroachdb://"):
                self.type = COCKROACH
            else:
                self.type = POSTGRES

            import psycopg2  # type: ignore

            def _parse_timestamp(value, _):
                f = "%Y-%m-%d %H:%M:%S.%f"
                if "." not in value:
                    f = "%Y-%m-%d %H:%M:%S"
                return time.mktime(datetime.datetime.strptime(value, f).timetuple())

            psycopg2.extensions.register_type(  # type: ignore
                psycopg2.extensions.new_type(  # type: ignore
                    psycopg2.extensions.DECIMAL.values,  # type: ignore
                    "DEC2FLOAT",
                    lambda value, curs: float(value) if value is not None else None,
                )
            )
            psycopg2.extensions.register_type(  # type: ignore
                psycopg2.extensions.new_type(  # type: ignore
                    (1082, 1083, 1266),
                    "DATE2INT",
                    lambda value, curs: (
                        time.mktime(value.timetuple()) if value is not None else None  # type: ignore
                    ),
                )
            )

            # psycopg2.extensions.register_type(
            #     psycopg2.extensions.new_type(
            #         (1184, 1114), "TIMESTAMP2INT", _parse_timestamp
            #     )
            # )
        else:
            if not os.path.exists(self.db_location):
                logger.info(f"Creating database directory: {self.db_location}")
                os.makedirs(self.db_location)
            self.path = os.path.join(self.db_location, f"{self.name}.sqlite3")
            database_uri = f"sqlite:///{self.path}"
            self.type = SQLITE

        self.schema = self.name
        if self.name.startswith("ext_"):
            self.schema = self.name[4:]
        else:
            self.schema = None

        self.engine = create_engine(database_uri, strategy=ASYNCIO_STRATEGY)
        self.lock = asyncio.Lock()

    @asynccontextmanager
    async def connect(self):
        await self.lock.acquire()
        try:
            async with self.engine.connect() as conn:  # type: ignore
                async with conn.begin() as txn:
                    wconn = Connection(conn, txn, self.type, self.name, self.schema)

                    if self.schema:
                        if self.type in {POSTGRES, COCKROACH}:
                            await wconn.execute(
                                f"CREATE SCHEMA IF NOT EXISTS {self.schema}"
                            )
                        elif self.type == SQLITE:
                            await wconn.execute(
                                f"ATTACH '{self.path}' AS {self.schema}"
                            )

                    yield wconn
        finally:
            self.lock.release()

    @asynccontextmanager
    async def get_connection(self, conn: Optional[Connection] = None):
        """Either yield the existing database connection (passthrough) or create a new one.

        Args:
            conn (Optional[Connection], optional): Connection object. Defaults to None.

        Yields:
            Connection: Connection object.
        """
        if conn is not None:
            # Yield the existing connection
            yield conn
        else:
            # Create and yield a new connection
            async with self.connect() as new_conn:
                yield new_conn

    async def fetchall(self, query: str, values: tuple = ()) -> list:
        async with self.connect() as conn:
            result = await conn.execute(query, values)
            return await result.fetchall()

    async def fetchone(self, query: str, values: tuple = ()):
        async with self.connect() as conn:
            result = await conn.execute(query, values)
            row = await result.fetchone()
            await result.close()
            return row

    async def execute(self, query: str, values: tuple = ()):
        async with self.connect() as conn:
            return await conn.execute(query, values)

    @asynccontextmanager
    async def reuse_conn(self, conn: Connection):
        yield conn

    def lock_table(self, table: str) -> str:
        if self.type == POSTGRES:
            return f"LOCK TABLE {self.references_schema}{table} IN EXCLUSIVE MODE;"
        elif self.type == COCKROACH:
            return f"LOCK TABLE {self.references_schema}{table};"
        elif self.type == SQLITE:
            return "BEGIN EXCLUSIVE TRANSACTION;"
        return "<nothing>"

    def timestamp_from_seconds(
        self, seconds: Union[int, float, None]
    ) -> Union[str, None]:
        if seconds is None:
            return None
        seconds = int(seconds)
        if self.type in {POSTGRES, COCKROACH}:
            return datetime.datetime.fromtimestamp(seconds).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        elif self.type == SQLITE:
            return str(seconds)
        return None

    def timestamp_now_str(self) -> str:
        timestamp = self.timestamp_from_seconds(time.time())
        if timestamp is None:
            raise Exception("Timestamp is None")
        return timestamp


def table_with_schema(db: Union[Database, Connection], table: str):
    return f"{db.references_schema if db.schema else ''}{table}"


@asynccontextmanager
async def get_connection(db: Database, conn: Optional[Connection] = None):
    """Either yield the existing database connection or create a new one.

    Note: This should be implemented as Database.get_connection(self, conn) but
    since we want to use it in LNbits, we can't change the Database class their.

    Args:
        db (Database): Database object.
        conn (Optional[Connection], optional): Connection object. Defaults to None.

    Yields:
        Connection: Connection object.
    """
    if conn is not None:
        # Yield the existing connection
        yield conn
    else:
        # Create and yield a new connection
        async with db.connect() as new_conn:
            yield new_conn
