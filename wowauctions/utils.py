from datetime import datetime
from pathlib import Path

from wowauctions import api, db


def pull_auctions_and_update_db(client_id: str, client_secret: str, db_path: Path):
    client = api.WowApi(client_id, client_secret)
    now = datetime.utcnow()
    with db.AuctionDB(db_path) as adb:
        auctions = api.get_auctions_from_api(client, auction_db=adb)
        adb.insert_auctions(auctions, now)
