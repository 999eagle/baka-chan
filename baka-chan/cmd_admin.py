import asyncio
import discord, discord.errors

import globals
from util import *
from errors import *
from command import Command, Helptext
from data import DataPermissions

strike_actions = ('nothing','kick','mutetext','mutevoice','ban')

@Helptext('Purges the last n messages from the current channel.', '<n>', permission = DataPermissions.Permission.purge)
@Command('purge')
async def cmd_purge(message, args):
	if not sender_has_permission(message, DataPermissions.Permission.purge):
		await send_message(message.channel, globals.message_no_permission)
		return
	if len(args) != 1 or not is_int(args[0]):
		await send_message(message.channel, 'Usage: `{0}purge <n>`'.format(globals.config.cmd_tag))
		return
	limit = int(args[0])
	try:
		channel = message.channel
		iterator = globals.client.logs_from(channel, limit=limit, reverse=True)
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

@Helptext('Strikes a user or removes strikes.', '(add|remove|clear) <@user>', permission = DataPermissions.Permission.strike)
@Command('strike')
async def cmd_strike(message, args):
	if not sender_has_permission(message, DataPermissions.Permission.strike):
		await send_message(message.channel, globals.message_no_permission)
		return
	if len(args) == 2 and args[0] in ('add','remove','clear') and is_usermention(args[1]):
		server_id = message.server.id
		user_id = get_id_from_mention(args[1])
		strikes = globals.data_strikes.getstrikes(server_id, user_id)
		changed = False
		if args[0] == 'add':
			if user_id != globals.dev_id:
				strikes += 1
				globals.data_strikes.addstrike(server_id, user_id)
				changed = True
			else:
				await send_message(message.channel, 'I won\'t strike my dev!')
		elif args[0] == 'clear':
			if strikes > 0:
				strikes = 0
				globals.data_strikes.clearstrikes(server_id, user_id)
				changed = True
			else:
				await send_message(message.channel, '{0} already had 0 strikes'.format(args[1]))
		elif args[0] == 'remove':
			if strikes > 0:
				strikes -= 1
				globals.data_strikes.removestrike(server_id, user_id)
				changed = True
			else:
				await send_message(message.channel, '{0} already had 0 strikes'.format(args[1]))
		if changed:
			if strikes == 1:
				plural = ''
			else:
				plural = 's'
			await send_message(message.channel, '{0} now has {1} strike{2}'.format(args[1], strikes, plural))
			actions = globals.data_settings.get_strike(server_id, strikes)
			await cmd_strike_action(message, actions, user_id)
	else:
		await send_message(message.channel, 'Usage: `strike (add|remove|clear) <@user>`')

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

@Helptext('Bans a user.', '<@user>', permission = DataPermissions.Permission.ban)
@Command('ban')
async def cmd_ban(message, args):
	if not sender_has_permission(message, DataPermissions.Permission.ban):
		await send_message(message.channel, globals.message_no_permission)
		return
	if len(args) == 1 and is_usermention(args[0]):
		member = message.server.get_member(get_id_from_mention(args[0]))
		try:
			await globals.client.ban(member)
			await send_message(message.channel, '{0} was banned from the server'.format(member.mention))
		except discord.Forbidden:
			await send_message(message.channel, 'Couldn\'t ban {0} (no permissions)'.format(member.mention))
	else:
		await send_message(message.channel, 'Usage: `{0}ban <@user>`'.format(globals.config.cmd_tag))

@Helptext('Kicks a user from the server.', '<@user>', permission = DataPermissions.Permission.kick)
@Command('kick')
async def cmd_kick(message, args):
	if not sender_has_permission(message, DataPermissions.Permission.kick):
		await send_message(message.channel, globals.message_no_permission)
		return
	if len(args) == 1 and is_usermention(args[0]):
		member = message.server.get_member(get_id_from_mention(args[0]))
		try:
			await globals.client.kick(member)
			await send_message(message.channel, '{0} was kicked from the server'.format(member.mention))
		except discord.Forbidden:
			await send_message(message.channel, 'Couldn\'t ban {0} (no permissions)'.format(member.mention))
	else:
		await send_message(message.channel, 'Usage: `{0}kick <@user>`'.format(globals.config.cmd_tag))

@Helptext('Modifies permissions.', '<@role> (give|remove) <permission>', permission = DataPermissions.Permission.edit_permissions,
		  after_text = 'Available permissions: ' + ', '.join(DataPermissions.all_perms))
@Helptext('Displays permissions.','(<@role>|<@user>)', permission = DataPermissions.Permission.edit_permissions,
		  before_text = ' ')
@Command('perms')
async def cmd_perms(message, args):
	if not sender_has_permission(message, DataPermissions.Permission.edit_permissions):
		await send_message(message.channel, globals.message_no_permission)
		return
	if len(args) == 1:
		if not is_mention(args[0]):
			await send_message(message.channel, 'Usage: `{0}perms (<@role>|<@user>)`'.format(globals.config.cmd_tag))
			return
		if is_usermention(args[0]):
			def check(perm):
				return globals.data_permissions.user_has_permission(message.server.id, get_id_from_mention(args[0]), perm)
		elif is_rolemention(args[0]):
			def check(perm):
				return globals.data_permissions.role_has_permission(message.server.id, get_id_from_mention(args[0]), perm)
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
			text = '{0} has no special permissions'.format(args[0])
		else:
			text = '{0} has these permissions: {1}'.format(args[0], text)
		await send_message(message.channel, text)
		return
	if not (len(args) == 3 and is_rolemention(args[0]) and args[1] in ('give','remove')):
		await send_message(message.channel, 'Usage: `{0}perms <@role> (give|remove) <permission>`'.format(globals.config.cmd_tag))
		return
	role_id = get_id_from_mention(args[0])
	perm_list = args[2].split(',')
	perms = []
	for p in perm_list:
		if not p in DataPermissions.all_perms:
			await send_message(message.channel, 'Usage: `{0}perms <@role> (give|remove) <permission>`'.format(globals.config.cmd_tag))
			return
		perms.append(DataPermissions.all_perms[p])
	if args[1] == 'give':
		for perm in perms:
			g.perms.add_permission(message.server.id, role_id, perm)
		await send_message(message.channel, 'Modified permissions successfully')
	elif args[1] == 'remove':
		for perm in perms:
			g.perms.remove_permission(message.server.id, role_id, perm)
		await send_message(message.channel, 'Modified permissions successfully')
	else:
		await send_message(message.channel, 'Usage: `{0}perms <@role> (give|remove) <permission>`')

@Helptext('Modified settings.','(get <setting> | set <setting> <value>)', permission = DataPermissions.Permission.settings,
		  after_text = 'Available settings: welcome, strike')
@Command('settings')
async def cmd_settings(message, args):
	if not sender_has_permission(message, DataPermissions.Permission.settings):
		await send_message(message.channel, globals.message_no_permission)
		return
	server_id = message.server.id
	if len(args) > 1 and args[0] == 'set':
		if args[1] == 'welcome':
			await send_message(message.channel, 'Do you want me to announce newly joined people in this channel? If so, please answer "yes" within 5 seconds.')
			msg = await globals.client.wait_for_message(author = message.author, content = 'yes', timeout = 5)
			if msg == None:
				await send_message(message.channel, 'Time expired, nothing was changed')
			else:
				globals.data_settings.set_welcome_channel(server_id, message.channel.id)
				await send_message(message.channel, 'New people will be announced here from now on.')
		elif args[1] == 'strike':
			if len(args) == 4 and is_int(args[2]):
				strike = int(args[2])
				if strike < 1 or strike > 7:
					await send_message(message.channel, 'Strike must be between 1 and 7 inclusive.')
					return
				actions = args[3].split(',')
				for a in actions:
					if not a in strike_actions:
						await send_message(message.channel, 'Unknown action `{0}`'.format(a))
						return
				globals.data_settings.set_strike(server_id, strike, args[3])
				await send_message(message.channel, 'Action changed')
	elif len(args) > 1 and args[0] == 'get':
		if args[1] == 'welcome':
			channel_id = globals.data_settings.get_welcome_channel(server_id)
			if channel_id == '':
				await send_message(message.channel, 'No channel for greetings set.')
			else:
				channel = globals.client.get_channel(channel_id)
				await send_message(message.channel, 'Greetings will be sent to {0}'.format(channel.name))
		elif args[1] == 'strike':
			strikes = []
			for i in range(1,8):
				strikes.append(globals.data_settings.get_strike(server_id, i))
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