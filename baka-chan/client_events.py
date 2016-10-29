import discord
import traceback

import globals
import log
import commands
from command import Command
from util import *
from cmd_dev import cmd_dev
import songs

@globals.client.event
async def on_ready():
	log.log_info('Discord client ready, UserID: {0}'.format(globals.client.user.id))
	await globals.client.change_presence(game=discord.Game(name='Use \'{0}help\''.format(globals.config.cmd_tag)))

@globals.client.event
async def on_member_join(member):
	pass

@globals.client.event
async def on_channel_update(before, after):
	pass

@globals.client.event
async def on_message(message):
	try:
		if len(message.content) == 0:
			return
		log.log_debug('Message received. Content: ' + message.content)
		private = message.channel.is_private
		is_dev = (message.author.id == globals.dev_id)
		content = message.content.lower()
		split = [x for x in content.split(' ') if x]
		tag = globals.config.cmd_tag
		if globals.disabled:
			if private and is_dev:
				await cmd_dev(message, split)
			return

		if not tag.endswith(' '):
			if split[0].startswith(tag):
				split[0] = split[0][len(tag):]
				if split[0] == '':
					split.remove('')
				split.insert(0, tag)
		if split[0] == tag.strip():
			if len(split) == 1:
				split.append('')
			if not await Command.execute(message, split, private = private):
				if split[1] == '':
					await send_message(message.channel, 'Type `{0}help`, to get a list with commands.'.format(tag))
				else:
					if private:
						await send_message(message.channel, 'The command `{0}` may not be used in a private channel.'.format(split[1], tag))
					else:
						await send_message(message.channel, 'Unknown command `{0}`. Type `{1}help`, to get a list with commands.'.format(split[1], tag))
		elif private and is_dev:
			await cmd_dev(message, split)
		elif globals.config.enable_songs:
			await songs.try_sing(message)
	except:
		text = traceback.format_exc()
		log.log_error(text)
		text = 'Exception:\n' + text
		user = discord.User(id = globals.dev_id)
		while text != '':
			if len(text) > 1990:
				await send_message(user, '```\n' + text[:1990] + '\n```')
				text = text[1990:]
			else:
				await send_message(user, '```\n' + text + '\n```')
				text = ''
