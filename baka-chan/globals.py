import os

from config import Config
from discord import Client
from data import *
from steam import Steam

version_str = 'v0.4'
dev_id = '111563848405798912'
running_in_foreground = False
disabled = False
config = Config()
client = Client()
data_coins = DataCoins()
data_strikes = DataStrikes()
data_settings = DataSettings()
data_permissions = DataPermissions()
api_steam = Steam()

message_no_permission = 'You don\'t have the permission to do that.'

def init():
	try:
		if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()):
			running_in_foreground = True
	except:
		running_in_foreground = False
