import discord
import traceback

import globals
import log
import commands
from command import Command
from util import *

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
		# TODO: fix this
		#is_dev = (message.author.id == globals.dev_id)
		is_dev = False
		content = message.content.lower()
		split = [x for x in content.split(' ') if x]
		tag = globals.config.cmd_tag
		# TODO: fix this
		#if globals.disabled:
		#	if private and is_dev:
		#		await cmd_dev(message, split)
		#	return

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
		# TODO: fix this
		#elif private and is_dev:
		#	await cmd_dev(message, split)
		#else:
		#	def normalize_lyrics(l: str):
		#		s = l.lower().rstrip(' !.?')
		#		s = s.replace(',','').replace('\'','')
		#		return s
		#	matched = False
		#	for s in g.songs:
		#		for t in s:
		#			if matched:
		#				await send_message(message.channel, t + ':notes:')
		#				break
		#			if normalize_lyrics(content).endswith(normalize_lyrics(t)):
		#				matched = True
		#		if matched:
		#			break
	except:
		text = traceback.format_exc()
		log.log_error(text)
		# TODO: fix this
		#text = 'Exception:\n' + text
		#user = discord.User(id=g.dev_id)
		#while text != '':
		#	if len(text) > 1990:
		#		await send_message(user, '```\n' + text[:1990] + '\n```')
		#		text = text[1990:]
		#	else:
		#		await send_message(user, '```\n' + text + '\n```')
		#		text = ''