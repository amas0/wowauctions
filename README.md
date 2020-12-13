# WoW Auctions

Package and utilities for maintaining of a database of active auctions
on the Tichondrius server. Uses Blizzard API access to pull and structure
auction information into a sqlite database. 

Also provides abstractions for Auctions and Items to provide easy extensibility.

### Updater setup

The base level of the project directory contains an `update.py` script that
pulls auction info from the Blizzard API. It requires three environment
variables to be defined:

* WOW_AUCTION_CLIENT_ID
* WOW_AUCTION_CLIENT_SECRET
* WOW_AUCTION_DB_PATH

With these defined, running the `update.py` script with the `wowauctions`
package installed will properly update the database with present auction info.

### Systemd services

The project also provides two systemd files -- a service and timer for setting
up an automated running of the update service to pull auction info to a db on
an hourly basis.

To install them, edit the `auctions-updater.service` file to run the 
`update.py` script by providing the proper absolute execution paths
to `ExecStart=`. Install both the `service` and `timer` files and enable/start
them.