import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Collection, Optional

from wowauctions.data import Auction, Item


@dataclass(frozen=True)
class DBColumn:
    name: str
    type: str
    options: str = ''

    @property
    def create_statement(self) -> str:
        return ' '.join((self.name, self.type, self.options)).strip()


@dataclass(frozen=True)
class DBTable:
    name: str
    schema: list[DBColumn]
    options: str = ''

    @property
    def create_statement(self) -> str:
        params = ',\n'.join([col.create_statement for col in self.schema] + [self.options])
        params = params.strip().rstrip(',')
        statement = f'CREATE TABLE {self.name} ({params});'
        return statement


ITEM_TABLE = DBTable(name='items', schema=[
    DBColumn(name='id', type='INTEGER', options='PRIMARY KEY'),
    DBColumn(name='name', type='TEXT', options='NOT NULL'),
    DBColumn(name='item_class', type='TEXT'),
    DBColumn(name='item_subclass', type='TEXT'),
    DBColumn(name='quality', type='TEXT')
])
AUCTION_TABLE = DBTable(name='auctions', schema=[
    DBColumn(name='id', type='INTEGER', options='NOT NULL'),
    DBColumn(name='pull_id', type='INTEGER', options='NOT NULL'),
    DBColumn(name='item_id', type='INTEGER', options='NOT NULL'),
    DBColumn(name='quantity', type='INTEGER'),
    DBColumn(name='unit_price', type='INTEGER'),
    DBColumn(name='buyout', type='INTEGER'),
    DBColumn(name='time_left', type='INTEGER')
], options='PRIMARY KEY (id, pull_id)')
PULLS_TABLE = DBTable(name='pulls', schema=[
    DBColumn(name='id', type='INTEGER', options='PRIMARY KEY AUTOINCREMENT'),
    DBColumn(name='datetime_utc', type='TEXT', options='NOT NULL')
])


class AuctionDB:
    ITEM_TABLE = ITEM_TABLE
    AUCTION_TABLE = AUCTION_TABLE
    PULLS_TABLE = PULLS_TABLE

    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.validate_or_create_tables()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.conn.rollback()
            print(exc_type)
        else:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()

    @property
    def tables(self) -> set[str]:
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return {x[0] for x in self.cursor.fetchall()}

    def validate_or_create_tables(self) -> None:
        """Checks for the existence of defined tables, otherwise creates them"""
        tables = self.tables
        if self.ITEM_TABLE.name not in tables:
            self.cursor.execute(self.ITEM_TABLE.create_statement)
        if self.AUCTION_TABLE.name not in tables:
            self.cursor.execute(self.AUCTION_TABLE.create_statement)
        if self.PULLS_TABLE.name not in tables:
            self.cursor.execute(self.PULLS_TABLE.create_statement)

    def insert_pull(self, dt: datetime) -> int:
        if self.get_pull_id_by_datetime(dt) is None:
            self.cursor.execute("INSERT INTO pulls (datetime_utc) VALUES (?)",
                                (dt.isoformat(timespec='seconds'),))
            return self.get_pull_id_by_datetime(dt)

    def get_pull_id_by_datetime(self, dt) -> Optional[int]:
        self.cursor.execute("SELECT * FROM pulls WHERE datetime_utc = ?",
                            (dt.isoformat(timespec='seconds'),))
        if db_response := self.cursor.fetchone():
            return db_response[0]
        else:
            return None

    def insert_item(self, item: Item) -> None:
        if self.get_item_by_id(item.id) is None:
            self.cursor.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)",
                                (item.id, item.name, item.item_class,
                                 item.item_subclass, item.quality))

    def insert_items(self, items: Collection[Item]) -> None:
        new_items = [item for item in items if self.get_item_by_id(item.id) is None]
        if new_items:
            params = [(item.id, item.name, item.item_class, item.item_subclass, item.quality)
                      for item in new_items]
            self.cursor.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?)", params)

    def get_item_by_id(self, item_id: int):
        self.cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        if db_response := self.cursor.fetchone():
            return Item(*db_response)
        else:
            return None

    def insert_auction(self, auction: Auction, dt: datetime):
        self.insert_item(auction.item)
        if (pull_id := self.get_pull_id_by_datetime(dt)) is None:
            pull_id = self.insert_pull(dt)
        if self.get_auction_by_id_pull(auction.id, pull_id) is None:
            self.cursor.execute("INSERT INTO wowauctions VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (auction.id, pull_id, auction.item.id,
                                 auction.quantity, auction.unit_price, auction.buyout,
                                 auction.time_left_key))

    def insert_auctions(self, auctions: list[Auction], dt: datetime):
        self.insert_items({auction.item for auction in auctions})
        if (pull_id := self.get_pull_id_by_datetime(dt)) is None:
            pull_id = self.insert_pull(dt)
            new_auctions = auctions
        else:
            new_auctions = [auction for auction in auctions
                            if self.get_auction_by_id_pull(auction.id, pull_id) is None]
        if new_auctions:
            params = [(auction.id, pull_id, auction.item.id, auction.quantity,
                       auction.unit_price, auction.buyout, auction.time_left_key)
                      for auction in new_auctions]
            self.cursor.executemany("INSERT INTO wowauctions VALUES (?, ?, ?, ?, ?, ?, ?)", params)

    def get_auction_by_id_pull(self, auction_id: int, pull_id: int):
        self.cursor.execute("SELECT * FROM wowauctions WHERE id = ? AND pull_id = ?",
                            (auction_id, pull_id))
        if db_response := self.cursor.fetchone():
            return Auction(id=db_response[0], item=self.get_item_by_id(db_response[2]),
                           *db_response[3:])
        else:
            return None
