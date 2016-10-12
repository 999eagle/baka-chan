import datetime
import json
import steamwebapi, steamwebapi.api

import globals
from errors import *
from util import *

class IEconItems_730(steamwebapi.api._SteamWebAPI):
	def __init__(self,**kwargs):
		self.interface = 'IEconItems_730'
		super(IEconItems_730, self).__init__(**kwargs)
	
	def get_player_items(self, steamID, format=None):
		"""Request the items of a given steam ID.

		steamID: The user ID
		format: Return format. None defaults to json. (json, xml, vdf)

		"""
		parameters = {'steamid' : steamID}
		if format is not None:
			parameters['format'] = format
		url = self.create_request_url(self.interface, 'GetPlayerItems', 1,
			parameters)
		data = self.retrieve_request(url)
		return self.return_data(data, format=format)

class Steam:
	def __init__(self):
		self.api_userstats = steamwebapi.api.ISteamUserStats(steam_api_key=globals.config.steam_api_key)
		self.api_user = steamwebapi.api.ISteamUser(steam_api_key=globals.config.steam_api_key)
		self.api_econitems730 = IEconItems_730(steam_api_key=globals.config.steam_api_key)