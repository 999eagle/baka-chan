import datetime
import json
import os
import sys

# import custom steamwebapi module, not the installed package
# for that the path of the submodule is inserted into sys.path and thus import will search in that path first
submodule_path = os.path.realpath(os.path.abspath(os.path.join(os.path.split(__file__)[0], 'steamwebapi')))
if submodule_path not in sys.path:
	sys.path.insert(0, submodule_path)
import steamwebapi
import steamwebapi.api

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
		url = self.create_request_url(self.interface, 'GetPlayerItems', 1, parameters)
		data = self.retrieve_request(url)
		return self.return_data(data, format=format)

class Steam:
	def __init__(self):
		self.cache_vanityurls_time = datetime.timedelta(hours=10)
		self.cache_vanityurls = {}
		self.cache_userstats_time = datetime.timedelta(hours=2)
		self.cache_userstats_730 = {}
		self.cache_userinfo_time = datetime.timedelta(hours=2)
		self.cache_userinfo = {}
		self.cache_userinventory_time = datetime.timedelta(hours=2)
		self.cache_userinventory_730 = {}

	def load_api(self):
		self.api_userstats = steamwebapi.api.ISteamUserStats(steam_api_key=globals.config.steam_api_key)
		self.api_user = steamwebapi.api.ISteamUser(steam_api_key=globals.config.steam_api_key)
		self.api_econitems730 = IEconItems_730(steam_api_key=globals.config.steam_api_key)

	def _getcachedata(self, cache, key):
		if key in cache:
			c = cache[key]
			if c['time'] < datetime.datetime.now():
				del cache[key]
			else:
				return (True, c['data'])
		return (False, None)
	def _setcachedata(self, cache, cache_time, key, data):
		c = {'time': datetime.datetime.now() + cache_time, 'data': data}
		cache[key] = c

	def _get_user_id(self, user):
		if is_steam_user_id(user):
			return int(user)
		else:
			return self.resolve_vanity_url(user)

	def resolve_vanity_url(self, vanity_url):
		cache_result = self._getcachedata(self.cache_vanityurls, vanity_url)
		if cache_result[0]:
			data = cache_result[1]
		else:
			try:
				resp = self.api_user.resolve_vanity_url(vanity_url, format = 'json')
				log.log_debug('Received Steam API data (ISteamUser/ResolveVanityURL: ' + repr(resp))
				if resp['response']['success'] == 1:
					data = resp['response']['steamid']
				else:
					data = False
			except SystemExit:
				log.log_info('Didn\'t receive Steam API data (ISteamUser/ResolveVanityURL)')
				data = False
			self._setcachedata(self.cache_vanityurls, self.cache_vanityurls_time, vanity_url, data)

		if data == False:
			raise SteamDataException('Vanity URL couldn\'t be resolved.')
		return data

	def get_user_info(self, user):
		user_id = self._get_user_id(user)
		cache_result = self._getcachedata(self.cache_userinfo, user_id)
		if cache_result[0]:
			data = cache_result[1]
		else:
			try:
				resp = self.api_user.get_player_summaries(str(user_id), format = 'json')
				log.log_debug('Received Steam API data (ISteamUser/GetPlayerSummaries): ' + repr(resp))
				if len(resp['response']['players']) == 0:
					data = False
				else:
					data = resp['response']['players'][0]
			except SystemExit:
				log.log_info('Didn\'t receive Steam API data (ISteamUser/GetPlayerSummaries)')
				data = False
			self._setcachedata(self.cache_userinfo, self.cache_userinfo_time, user_id, data)

		if data == False:
			raise SteamDataException('Couldn\'t get user information.')
		return data

	def get_user_stats_730(self, user):
		user_id = self._get_user_id(user)
		cache_result = self._getcachedata(self.cache_userstats_730, user_id)
		if cache_result[0]:
			data = cache_result[1]
		else:
			try:
				resp = self.api_userstats.get_user_stats_for_game(str(user_id), 730, format = 'json')
				log.log_debug('Received Steam API data (ISteamUserStats/GetUserStatsForGame): ' + repr(resp))
				data = resp['playerstats']['stats']
			except SystemExit:
				log.log_info('Didn\'t receive Steam API data (ISteamUserStats/GetUserStatsForGame)')
				data = False
			self._setcachedata(self.cache_userinventory_730, self.cache_userinventory_time, user_id, data)

		if data == False:
			raise SteamDataException('Couldn\'t get user stats.')
		return data

	def get_user_inventory_730(self, user):
		user_id = self._get_user_id(user)
		cache_result = self._getcachedata(self.cache_userinventory_730, user_id)
		if cache_result[0]:
			data = cache_result[1]
		else:
			try:
				resp = self.api_econitems730.get_player_items(str(user_id), format = 'json')
				log.log_debug('Received Steam API data (IEconItems_730/GetPlayerItems): ' + repr(resp))
				data = None
			except SystemExit:
				log.log_info('Didn\'t receive Steam API data (IEconItems_730/GetPlayerItems)')
				data = False
			self._setcachedata(self.cache_userinventory_730, self.cache_userinventory_time, user_id, data)

		return data
