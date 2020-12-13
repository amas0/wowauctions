import os
from pathlib import Path

import wowauctions

client_id = os.environ.get('WOW_AUCTION_CLIENT_ID')
client_secret = os.environ.get('WOW_AUCTION_CLIENT_SECRET')
db_loc = Path(os.environ.get('WOW_AUCTION_DB_PATH'))
wowauctions.utils.pull_auctions_and_update_db(client_id, client_secret, db_loc)
