import os, os.path
import json
from enum import Enum

import globals
from platform_specific import PlatformSpecific
from errors import *
import log

all_data = []

class Data(object):
	"""Base class for data containers."""

	def __init__(self, file):
		p = PlatformSpecific.inst()
		self.path = p.convert_path('data\\')
		self.dirty = False
		self.loaded = False
		self.data = {}
		if not os.path.isdir(self.path):
			os.mkdir(self.path)
		self.path += file
		all_data.append(self)

	@classmethod
	def save_all_dirty(cls):
		for d in all_data:
			if d.dirty:
				d.save()

	@classmethod
	def load_all(cls):
		for d in all_data:
			d.load()

	def load(self):
		if os.path.isfile(self.path):
			with open(self.path, 'r') as file:
				self.data = json.load(file)
		self.dirty = False
		self.loaded = True

	def save(self):
		with open(self.path, 'w') as file:
			json.dump(self.data, file)
		self.dirty = False
		log.log_debug('Saved data file {0}'.format(self.path))

	def getserver(self, server_id):
		if not server_id in self.data:
			self.data[server_id] = {}
		return self.data[server_id]

	def getvalue(self, server_id, key, default_value=None):
		server = self.getserver(server_id)
		if key not in server:
			return default_value
		return server[key]

	def setvalue(self, server_id, key, value):
		server = self.getserver(server_id)
		server[key] = value
		self.dirty = True

class DataCoins(Data):
	"""Stores how many coins users have."""

	def __init__(self):
		super(DataCoins, self).__init__('coins.json')

	def getcoins(self, server_id, user_id):
		return self.getvalue(server_id, user_id, globals.config.start_currency)
	def setcoins(self, server_id, user_id, coins):
		self.setvalue(server_id, user_id, coins)
	def getservercoins(self, server_id):
		return self.getserver(server_id)

class DataStrikes(Data):
	"""Stores how many strikes users have."""

	def __init__(self):
		super(DataStrikes, self).__init__('strikes.json')

	def getstrikes(self, server_id, user_id):
		return self.getvalue(server_id, user_id, 0)
	def clearstrikes(self, server_id, user_id):
		server = self.getserver(server_id)
		del server[user_id]
	def addstrike(self, server_id, user_id):
		self.setvalue(server_id, user_id, self.getstrikes(server_id, user_id) + 1)
	def removestrike(self, server_id, user_id):
		self.setvalue(server_id, user_id, self.getstrikes(server_id, user_id) - 1)

class DataSettings(Data):
	"""Stores server settings."""
	
	def __init__(self):
		super(DataSettings, self).__init__('settings.json')
		self.default_settings = {'welcome_channel':'',
		                         'strike_1':'nothing','strike_2':'nothing','strike_3':'kick','strike_4':'mutetext,mutevoice','strike_5':'ban','strike_6':'nothing','strike_7':'nothing'}

	def getsetting(self, server_id, setting):
		if setting not in self.default_settings:
			raise InvalidSettingException('Setting "{0}" is unknown.'.format(setting))
		return self.getvalue(server_id, setting, self.default_settings[setting])
	def setsetting(self, server_id, setting, value):
		if setting not in self.default_settings:
			raise InvalidSettingException('Setting "{0}" is unknown.'.format(setting))
		self.setvalue(server_id, setting, value)

	# helper for strike n
	def get_strike(self, server_id, strike):
		if 1 <= strike <= 7:
			return getattr(self, 'get_strike_' + str(strike))(server_id)
		else:
			raise InvalidSettingException('Strike must be between 1 and 7 inclusive.')
	def set_strike(self, server_id, strike, action):
		if 1 <= strike <= 7:
			return getattr(self, 'set_strike_' + str(strike))(server_id, action)
		else:
			raise InvalidSettingException('Strike must be between 1 and 7 inclusive.')

	# welcome_channel
	def get_welcome_channel(self, server_id):
		return self.getsetting(server_id, 'welcome_channel')
	def set_welcome_channel(self, server_id, channel_id):
		self.setsetting(server_id, 'welcome_channel', channel_id)
	# strike_1
	def get_strike_1(self, server_id):
		return self.getsetting(server_id, 'strike_1')
	def set_strike_1(self, server_id, action):
		self.setsetting(server_id, 'strike_1', action)
	# strike_2
	def get_strike_2(self, server_id):
		return self.getsetting(server_id, 'strike_2')
	def set_strike_2(self, server_id, action):
		self.setsetting(server_id, 'strike_2', action)
	# strike_3
	def get_strike_3(self, server_id):
		return self.getsetting(server_id, 'strike_3')
	def set_strike_3(self, server_id, action):
		self.setsetting(server_id, 'strike_3', action)
	# strike_4
	def get_strike_4(self, server_id):
		return self.getsetting(server_id, 'strike_4')
	def set_strike_4(self, server_id, action):
		self.setsetting(server_id, 'strike_4', action)
	# strike_5
	def get_strike_5(self, server_id):
		return self.getsetting(server_id, 'strike_5')
	def set_strike_5(self, server_id, action):
		self.setsetting(server_id, 'strike_5', action)
	# strike_6
	def get_strike_6(self, server_id):
		return self.getsetting(server_id, 'strike_6')
	def set_strike_6(self, server_id, action):
		self.setsetting(server_id, 'strike_6', action)
	# strike_7
	def get_strike_7(self, server_id):
		return self.getsetting(server_id, 'strike_7')
	def set_strike_7(self, server_id, action):
		self.setsetting(server_id, 'strike_7', action)

class DataPermissions(Data):
	"""Stores permissions settings."""
	class Permission(Enum):
		none = 0
		coins_spawn = 1
		coins_despawn = 2
		strike = 4
		edit_permissions = 8
		settings = 16
		ban = 32
		kick = 64
		mute = 128
		purge = 256
	all_perms = { 'coins_spawn':      Permission.coins_spawn,
	              'coins_despawn':    Permission.coins_despawn,
	              'strike':           Permission.strike,
	              'edit_permissions': Permission.edit_permissions,
	              'settings':         Permission.settings,
	              'ban':              Permission.ban,
	              'kick':             Permission.kick,
	              'mute':             Permission.mute,
	              'purge':            Permission.purge}
	
	def __init__(self):
		super(DataPermissions, self).__init__('settings.json')

	def getperm(self, server_id, role_id):
		return self.getvalue(server_id, role_id, DataPermissions.Permission.none.value)
	def setperm(self, server_id, role_id, permission):
		if isinstance(permission, DataPermissions.Permission):
			self.setvalue(server_id, role_id, permission.value)
		elif isinstance(permission, int):
			self.setvalue(server_id, role_id, permission)
		else:
			raise ValueError('permission must be either int or Permission')

	def addperm(self, server_id, role_id, permission):
		p = self.getperm(server_id, role_id)
		p |= permission.value
		self.setperm(server_id, role_id, p)
	def removeperm(self, server_id, role_id, permission):
		p = self.getperm(server_id, role_id)
		p &= (~ permission.value)
		self.setperm(server_id, role_id, p)

	def role_has_permission(self, server_id, role_id, permission):
		if permission == DataPermissions.Permission.none:
			return True
		discord_server = globals.client.get_server(server_id)
		for role in discord_server.roles:
			if role.id == role_id and role.permissions.administrator:
				return True
		return (self.getperm(server_id, role_id) & permission.value) == permission.value
	def user_has_permission(self, server_id, user_id, permission):
		if permission == DataPermissions.Permission.none:
			return True
		discord_server = globals.client.get_server(server_id)
		discord_member = None
		for member in discord_server.members:
			if member.id == user_id:
				discord_member = member
		if discord_member == None:
			raise ValueError('user_id not found')
		for role in discord_member.roles:
			if self.role_has_permission(server_id, role.id, permission):
				return True
		return False
