import configparser, logging

from errors import *
from util import *
import log

class Config(object):
	"""Manges the configuration for the bot."""

	def __init__(self):
		self.loaded = False

	def validate_loaded_config(self):
		#
		# Validate section [General]
		#
		if 'General' not in self.parser:
			raise InvalidConfigException('Section "[General]" is missing.')
		sect_general = self.parser['General']
		# Validate log level
		if 'log_level' not in sect_general:
			raise InvalidConfigException('Key "log_level" in section "[General]" is missing.')
		if sect_general['log_level'] not in ('DEBUG','INFO','WARNING','ERROR','CRITICAL'):
			raise InvalidConfigException('Key "log_level" in section "[General]" must be one of "DEBUG","INFO","WARNING","ERROR","CRITICAL".')
		# Validate start currency
		if 'start_currency' not in sect_general:
			raise InvalidConfigException('Key "start_currency" in section "[General]" is missing.')
		if not is_int(sect_general['start_currency']):
			raise InvalidConfigException('Key "start_currency" in section "[General]" must have an integer value.')
		if 'currency_name' not in sect_general:
			raise InvalidConfigException('Key "currency_name" in section "[General]" is missing.')
		if 'currency_cmd' not in sect_general:
			raise InvalidConfigException('Key "currency_cmd" in section "[General]" is missing.')
		if 'enable_songs' not in sect_general: raise InvalidConfigException('Key "enable_songs" in section "[General]" is missing.')
		if sect_general['enable_songs'].lower() not in ('true','false'): raise InvalidConfigException('Key "enable_songs" in section "[General]" must be one of "true","false".')
		#
		# Validate section [Discord]
		#
		if 'Discord' not in self.parser:
			raise InvalidConfigException('Section "[Discord]" is missing.')
		sect_discord = self.parser['Discord']
		# Validate key login_token
		if 'login_token' not in sect_discord:
			raise InvalidConfigException('Key "login_token" in section "[Discord]" is missing.')
		# Validate key command_tag
		sect_discord['command_tag'] = sect_discord.get('command_tag', '+')
		#
		# Validate section [Games]
		#
		if 'Games' not in self.parser: raise InvalidConfigException('Section "[Games]" is missing.')
		sect_games = self.parser['Games']
		# Validate slots config
		if 'slots_count' not in sect_games: raise InvalidConfigException('Key "slots_count" in section "[Games]" is missing.')
		if not is_int(sect_games['slots_count']): raise InvalidConfigException('Key "slots_count" in section "[Games]" must have an integer value.')
		if 'slots_items' not in sect_games: raise InvalidConfigException('Key "slots_items" in section "[Games]" is missing.')
		if 'slots_bonuses' not in sect_games: raise InvalidConfigException('Key "slots_bonuses" in section "[Games]" is missing.')
		# Validate rps config
		if 'rps_timeout' not in sect_games: raise InvalidConfigException('Key "rps_timeout" in section "[Games]" is missing.')
		if not is_int(sect_games['rps_timeout']): raise InvalidConfigException('Key "rps_timeout" in section "[Games]" must have an integer value.')
		if 'rps_allow_rpsls' not in sect_games: raise InvalidConfigException('Key "rps_allow_rpsls" in section "[Games]" is missing.')
		if sect_games['rps_allow_rpsls'].lower() not in ('true','false'): raise InvalidConfigException('Key "rps_allow_rpsls" in section "[Games]" must be one of "true","false".')
		#
		# Validate section [API]
		#
		if 'API' not in self.parser:
			log.log_warning('Configuration: Section "[API]" is missing. Some commands will not work.')
			# add empty section so that the properties don't have to check for this section later
			self.parser['API'] = {}
		else:
			sect_api = self.parser['API']
			# Validate Steam API config
			if 'steam_api_key' not in sect_api: log.log_warning('Configuration: Key "steam_api_key" in section "[API]" is missing. Steam commands will not work.')
		#
		# Validate section [Updater]
		#
		if 'Updater' not in self.parser:
			log.log_warning('Configuration: Section "[Updater]" is missing. Updating from repo will not work.')
		else:
			sect_updater = self.parser['Updater']
			# Validate GitHub login token
			if 'github_login_token' not in sect_updater: raise InvalidConfigException('Key "github_login_token" in section "[Updater]" is missing.')
			# Validate GitHub repo
			if 'github_repo' not in sect_updater: raise InvalidConfigException('Key "github_repo" in section "[Updater]" is missing.')

		self.loaded = True

	def load(self):
		self.parser = configparser.ConfigParser()
		names = self.parser.read('config.ini')
		if 'config.ini' not in names:
			raise InvalidConfigException('Configuration couldn\'t be loaded.')
		self.validate_loaded_config()
		self._slots_bonuses = None

	@property
	def discord_token(self) -> str:
		if not self.loaded:
			raise ConfigNotLoadedException()
		return self.parser['Discord']['login_token']

	@property
	def cmd_tag(self) -> str:
		if not self.loaded:
			raise ConfigNotLoadedException()
		return self.parser['Discord']['command_tag'].strip('\'"')

	@property
	def log_level(self) -> int:
		if not self.loaded:
			raise ConfigNotLoadedException()
		return getattr(logging, self.parser['General']['log_level'])

	@property
	def start_currency(self) -> int:
		if not self.loaded:
			raise ConfigNotLoadedException()
		return int(self.parser['General']['start_currency'])

	@property
	def currency_name(self) -> str:
		if not self.loaded:
			raise ConfigNotLoadedException()
		return self.parser['General']['currency_name']

	@property
	def currency_cmd(self) -> str:
		if not self.loaded:
			raise ConfigNotLoadedException()
		return self.parser['General']['currency_cmd']

	@property
	def enable_songs(self) -> bool:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['General']['enable_songs'].lower() == 'true'

	@property
	def slots_count(self) -> int:
		if not self.loaded:
			raise ConfigNotLoadedException()
		return int(self.parser['Games']['slots_count'])

	@property
	def slots_items(self) -> list:
		if not self.loaded:
			raise ConfigNotLoadedException()
		items = self.parser['Games']['slots_items'].split(',')
		return [':' + i.strip() + ':' for i in items]

	@property
	def slots_bonuses(self) -> dict:
		if not self.loaded:
			raise ConfigNotLoadedException()
		if self._slots_bonuses == None:
			bonuses_list = self.parser['Games']['slots_bonuses'].split(',')
			self._slots_bonuses = {}
			for b in bonuses_list:
				s = b.split(':')
				self._slots_bonuses[':' + s[0].strip() + ':'] = s[1].strip()
		return self._slots_bonuses

	@property
	def rps_timeout(self) -> int:
		if not self.loaded: raise ConfigNotLoadedException()
		return int(self.parser['Games']['rps_timeout'])

	@property
	def rps_allow_rpsls(self) -> bool:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['Games']['rps_allow_rpsls'].lower() == 'true'

	@property
	def has_steam_api_key(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return 'steam_api_key' in self.parser['API']

	@property
	def steam_api_key(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['API']['steam_api_key']

	@property
	def has_updater_config(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return 'Updater' in self.parser

	@property
	def github_login_token(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['Updater']['github_login_token']

	@property
	def github_repo(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['Updater']['github_repo']
