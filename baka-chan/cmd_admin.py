import asyncio
import discord, discord.errors

import globals
from util import *
from errors import *
from command import Command
from data import DataPermissions

strike_actions = ('nothing','kick','mutetext','mutevoice','ban')

@Command('purge', help = 'Purges the last n messages from the current channel.', usage = ('<n:int>',), permission = DataPermissions.Permission.purge)
async def cmd_purge(message, n):
	try:
		channel = message.channel
		iterator = globals.client.logs_from(channel, limit = n, reverse=True)
		ret = []
		count = 0
		deleted = False
		while not deleted:
			try:
				msg = await iterator.iterate()
			except asyncio.QueueEmpty:
				if count >= 2:
					await globals.client.delete_messages(ret[-count:])
				elif count == 1:
					await globals.client.delete_message(ret[-1])
				log.log_info('Deleted {0} messages from channel {1}({2}) on server {3}({4})'.format(len(ret), channel.name, channel.id, channel.server.name, channel.server.id))
				return deleted
			else:
				if count == 100:
					await globals.client.delete_messages(ret[-100:])
					count = 1
					await asyncio.sleep(1)
				count += 1
				ret.append(msg)
	except discord.errors.Forbidden:
		await send_message(message.channel, 'I don\'t have permission to delete messages.')

@Command('strike', help = 'Strikes a user or removes strikes.', usage = (('oneof','add','remove','clear'),'<@user>'), permission = DataPermissions.Permission.strike)
async def cmd_strike(message, action, user):
	server_id = message.server.id
	user_id = user.id
	strikes = globals.data_strikes.getstrikes(server_id, user_id)
	changed = False
	if action == 'add':
		if user_id != globals.dev_id:
			strikes += 1
			globals.data_strikes.addstrike(server_id, user_id)
			changed = True
		else:
			await send_message(message.channel, 'I won\'t strike my dev!')
	elif action == 'clear':
		if strikes > 0:
			strikes = 0
			globals.data_strikes.clearstrikes(server_id, user_id)
			changed = True
		else:
			await send_message(message.channel, '{0} already had 0 strikes'.format(user.mention))
	elif action == 'remove':
		if strikes > 0:
			strikes -= 1
			globals.data_strikes.removestrike(server_id, user_id)
			changed = True
		else:
			await send_message(message.channel, '{0} already had 0 strikes'.format(user.mention))
	if changed:
		if strikes == 1:
			plural = ''
		else:
			plural = 's'
		await send_message(message.channel, '{0} now has {1} strike{2}'.format(user.mention, strikes, plural))
		actions = globals.data_settings.get_strike(server_id, strikes)
		await cmd_strike_action(message, actions, user_id)

async def cmd_strike_action(message, action, target_id):
	actions = action.split(',')
	server = globals.client.get_server(message.server.id)
	member = server.get_member(target_id)
	for a in actions:
		if a == 'kick':
			try:
				await globals.client.kick(member)
				await send_message(message.channel, '{0} was kicked from the server'.format(member.mention))
			except discord.Forbidden:
				await send_message(message.channel, 'Couldn\'t kick {0} (no permissions)'.format(member.mention))
		elif a == 'ban':
			try:
				await globals.client.ban(member,delete_message_days=0)
				await send_message(message.channel, '{0} was banned from the server'.format(member.mention))
			except discord.Forbidden:
				await send_message(message.channel, 'Couldn\'t ban {0} (no permissions)'.format(member.mention))

@Command('ban', help = 'Bans a user from the server.', usage = ('<@user>',), permission = DataPermissions.Permission.ban)
async def cmd_ban(message, user):
	member = message.server.get_member(user.id)
	try:
		await globals.client.ban(member)
		await send_message(message.channel, '{0} was banned from the server'.format(member.mention))
	except discord.Forbidden:
		await send_message(message.channel, 'Couldn\'t ban {0} (no permissions)'.format(member.mention))

@Command('kick', help = 'Kicks a user from the server.', usage = ('<@user>',), permission = DataPermissions.Permission.kick)
async def cmd_kick(message, user):
	member = message.server.get_member(user.id)
	try:
		await globals.client.kick(member)
		await send_message(message.channel, '{0} was kicked from the server'.format(member.mention))
	except discord.Forbidden:
		await send_message(message.channel, 'Couldn\'t ban {0} (no permissions)'.format(member.mention))

@Command('perms', help = 'Displays permissions.', usage = (('oneof','<@user>','<@role>'),), permission = DataPermissions.Permission.display_permissions)
async def cmd_perms_display(message, mention):
	if mention.type == 'role':
		def check(perm):
			return globals.data_permissions.role_has_permission(message.server.id, mention.id, perm)
	elif mention.type == 'user':
		def check(perm):
			return globals.data_permissions.user_has_permission(message.server.id, mention.id, perm)
	else:
		def check(perm):
			return False
	text = ''
	for p in DataPermissions.all_perms:
		perm = DataPermissions.all_perms[p]
		if check(perm):
			if text != '':
				text += ', '
			text += p
	if text == '':
		text = '{0} has no special permissions'.format(mention.mention)
	else:
		text = '{0} has these permissions: {1}'.format(mention.mention, text)
	await send_message(message.channel, text)

@Command('perms', help = 'Edit permissions.', usage = (('oneof','give','remove'),'<@role>','<permissions:str>'), permission = DataPermissions.Permission.edit_permissions)
async def cmd_perms_edit(message, action, role, perms):
	role_id = role.id
	perm_list = perms.split(',')
	parsed_perms = []
	for p in perm_list:
		if not p in DataPermissions.all_perms:
			raise ArgumentParseException()
		parsed_perms.append(DataPermissions.all_perms[p])
	if action == 'give':
		for perm in parsed_perms:
			globals.data_permissions.addperm(message.server.id, role_id, perm)
		await send_message(message.channel, 'Modified permissions successfully')
	elif action == 'remove':
		for perm in parsed_perms:
			globals.data_permissions.removeperm(message.server.id, role_id, perm)
		await send_message(message.channel, 'Modified permissions successfully')

@Command('settings', help = 'Display a setting.', usage = ('get','<setting:str>'), permission = DataPermissions.Permission.settings)
async def cmd_settings_get(message, setting):
	if setting == 'welcome':
		channel_id = globals.data_settings.get_welcome_channel(message.server.id)
		if channel_id == '':
			await send_message(message.channel, 'No channel for greetings set.')
		else:
			channel = globals.client.get_channel(channel_id)
			await send_message(message.channel, 'Greetings will be sent to {0}'.format(channel.name))
	elif setting == 'strike':
		strikes = []
		for i in range(1,8):
			strikes.append(globals.data_settings.get_strike(message.server.id, i))
		text = ''
		for i in range(0, len(strikes)):
			if strikes[i] != 'nothing':
				if i == 1:
					plural = ''
				else:
					plural = 's'
				text += '{0} strike{1}: {2}\n'.format(i + 1, plural, strikes[i])
		if text == '':
			text = 'No actions defined'
		await send_message(message.channel, text)
	else:
		raise ArgumentParseException()

@Command('settings', help = 'Change a setting.', usage = ('set','<setting:str>','*[<value>]'), permission = DataPermissions.Permission.settings)
async def cmd_settings_set(message, setting, *args):
	if setting == 'welcome':
		await send_message(message.channel, 'Do you want me to announce newly joined people in this channel? If so, please answer "yes" within 5 seconds.')
		msg = await globals.client.wait_for_message(author = message.author, content = 'yes', timeout = 5)
		if msg == None:
			await send_message(message.channel, 'Time expired, nothing was changed')
		else:
			globals.data_settings.set_welcome_channel(message.server.id, message.channel.id)
			await send_message(message.channel, 'New people will be announced here from now on.')
	elif setting == 'strike':
		if len(args) >= 2 and is_int(args[0]):
			strike = int(args[0])
			if strike < 1 or strike > 7:
				await send_message(message.channel, 'Strike must be between 1 and 7 inclusive.')
				return
			actions = args[1].split(',')
			for a in actions:
				if not a in strike_actions:
					await send_message(message.channel, 'Unknown action `{0}`'.format(a))
					return
			globals.data_settings.set_strike(message.server.id, strike, args[1])
			await send_message(message.channel, 'Action changed')
		else:
			raise ArgumentParseException()
	else:
		raise ArgumentParseException()
