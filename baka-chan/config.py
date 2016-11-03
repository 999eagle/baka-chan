import configparser, logging
import shutil

from errors import *
from util import *
import log

class Config(object):
	"""Manges the configuration for the bot."""

	version = '1'

	def __init__(self):
		self.loaded = False

	def _update_config_to_v1(self):
		if 'config_version' in self.parser['General'] and self.parser['General']['config_version'] != '0':
			raise InvalidConfigException('Can\'t upgrade to version 1.')
		self.parser['General']['config_version'] = '1'
		if 'Updater' in self.parser:
			sect_updater = self.parser['Updater']
			self.parser.add_section('GitHub')
			self.parser['GitHub']['login_token'] = sect_updater['github_login_token']
			self.parser['GitHub']['update_repo'] = sect_updater['github_repo']
			self.parser['GitHub']['enable_reports'] = 'True'
			self.parser['GitHub']['issue_labels'] = 'autoreport'
			self.parser.remove_section('Updater')

	def validate_loaded_config(self):
		#
		# Validate section [General]
		#
		if 'General' not in self.parser:
			raise InvalidConfigException('Section "[General]" is missing.')
		sect_general = self.parser['General']
		# Absolute first thing: validate configuration version
		if 'config_version' not in sect_general or sect_general['config_version'] != Config.version:
			old_version = '0'
			if 'config_version' in sect_general:
				old_version = sect_general['config_version']
			version = old_version
			if version == '0':
				self._update_config_to_v1()
				version = '1'
			if version != Config.version:
				raise InvalidConfigException('Config file has an unsupported version.')
			else:
				log.log_info('Configuration file has been upgraded from version {0} to version {1}. The old file can be found as "config.bak.ini".'.format(old_version, version))
				shutil.copy2('config.ini', 'config.bak.ini')
				with open('config.ini', 'w') as f:
					self.parser.write(f)
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
		try:
			str2bool(sect_general['enable_songs'])
		except ValueError:
			raise InvalidConfigException('Key "enable_songs" in section "[General]" must be a boolean value.')
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
		try:
			str2bool(sect_games['rps_allow_rpsls'])
		except ValueError:
			raise InvalidConfigException('Key "rps_allow_rpsls" in section "[Games]" must be a boolean value.')
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
		# Validate section [GitHub]
		#
		if 'GitHub' not in self.parser:
			log.log_warning('Configuration: Section "[GitHub]" is missing. GitHub integration will not work.')
		else:
			sect_github = self.parser['GitHub']
			# Validate login token
			if 'login_token' not in sect_github: raise InvalidConfigException('Key "login_token" in section "[GitHub]" is missing.')
			# Validate update repo
			if 'update_repo' not in sect_github: log.log_warning('Key "update_repo" in section "[GitHub]" is missing. Updating from GitHub repo will not work.')
			# Validate reports
			if 'enable_reports' not in sect_github: sect_github['enable_reports'] = 'false'
			try:
				str2bool(sect_github['enable_reports'])
			except ValueError:
				raise InvalidConfigException('Key "enable_reports" in section "[GitHub]" must be a boolean value.')
			if str2bool(sect_github['enable_reports']):
				if 'issue_labels' not in sect_github: sect_github['issue_labels'] = ''

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
		return str2bool(self.parser['General']['enable_songs'])

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
		return str2bool(self.parser['Games']['rps_allow_rpsls'])

	@property
	def has_steam_api_key(self) -> bool:
		if not self.loaded: raise ConfigNotLoadedException()
		return 'steam_api_key' in self.parser['API']

	@property
	def steam_api_key(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['API']['steam_api_key']

	@property
	def has_github_config(self) -> bool:
		if not self.loaded: raise ConfigNotLoadedException()
		return 'GitHub' in self.parser

	@property
	def github_login_token(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['GitHub']['login_token']

	@property
	def has_github_update_repo(self) -> bool:
		if not self.loaded: raise ConfigNotLoadedException()
		return 'update_repo' in self.parser['GitHub']

	@property
	def github_update_repo(self) -> str:
		if not self.loaded: raise ConfigNotLoadedException()
		return self.parser['GitHub']['update_repo']

	@property
	def github_enable_reports(self) -> bool:
		if not self.loaded: raise ConfigNotLoadedException()
		return str2bool(self.parser['GitHub']['enable_reports'])

	@property
	def github_issue_labels(self) -> list:
		if not self.loaded: raise ConfigNotLoadedException()
		labels = self.parser['GitHub']['issue_labels'].split(',')
		return [l.strip() for l in labels]
