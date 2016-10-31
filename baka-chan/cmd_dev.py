import discord

import globals
from util import *

async def cmd_dev(message, args):
	if len(args) == 0 or args[0] != 'dev':
		return
	if len(args) == 2:
		if args[1] == 'disable':
			globals.disabled = True
			await globals.client.change_presence(game = discord.Game(name = 'Currently disabled'), status = discord.Status.idle)
			await send_message(message.channel, 'Baka-chan was disabled.')
		elif args[1] == 'enable':
			globals.disabled = False
			await globals.client.change_presence(game = discord.Game(name = 'Use `{0}help`'.format(globals.config.cmd_tag)), status = discord.Status.online)
			await send_message(message.channel, 'Baka-chan was enabled.')
	if len(args) == 3:
		if args[1] == 'update':
			await send_message(message.channel, 'Updating, please wait...')
			from updater import Updater
			with Updater(globals.client.loop) as u:
				await u.update_from_github_repo(args[2])
