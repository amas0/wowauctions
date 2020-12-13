from __future__ import annotations

from wowapi import WowApi
from wowapi.exceptions import WowApiException

import wowauctions.db as db
from wowauctions.data import Auction, Item


TICHONDRIUS_ID = 11


def get_item_from_api(item_id: int, wowapi: WowApi) -> Item:
    try:
        api_response = wowapi.get_item_data(region='us', namespace='static-us',
                                            locale='en_US', id=item_id)
        item = Item(id=item_id, name=api_response.get('name'),
                    item_class=api_response.get('item_class').get('name'),
                    item_subclass=api_response.get('item_subclass').get('name'),
                    quality=api_response.get('quality').get('name'))
    except WowApiException:
        # In the event the item pull from the API fails, save the id with empty attributes
        item = Item(id=item_id, name='', item_class='', item_subclass='', quality='')
    return item


def api_response_to_auction(response: dict, item: Item):
    quantity = response.get('quantity')
    unit_price = response.get('unit_price')
    buyout = response.get('buyout')
    return Auction(id=int(response.get('id')),
                   item=item,
                   quantity=int(quantity) if quantity is not None else None,
                   unit_price=int(unit_price) if unit_price is not None else None,
                   buyout=int(buyout) if buyout is not None else None,
                   time_left=response.get('time_left'))


def get_auctions_from_api(wowapi: WowApi, auction_db: db.AuctionDB, realm_id=TICHONDRIUS_ID) -> list[Auction]:
    api_response = wowapi.get_auctions(region='us', namespace='dynamic-us', connected_realm_id=realm_id)
    auction_response = api_response.get('auctions', [])
    item_ids = {int(auction_dict.get('item').get('id')) for auction_dict in auction_response}
    item_dict = {}
    for item_id in item_ids:
        if (item := auction_db.get_item_by_id(item_id)) is not None:
            item_dict[item_id] = item
        else:
            item_dict[item_id] = get_item_from_api(item_id, wowapi=wowapi)

    auction_objects = []
    for auction_dict in auction_response:
        item = item_dict.get(auction_dict.get('item').get('id'))
        auction = api_response_to_auction(auction_dict, item=item)
        auction_objects.append(auction)
    return auction_objects


