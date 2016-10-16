import discord
import datetime
import random
import asyncio
import time

from command import Command, StaticResponse, Helptext
import globals
from util import *

@Helptext('Shows this help.')
@Command('help', allow_private=True)
async def cmd_help(message, args):
	help_msg = '**Baka-chan** {1}\nMade by **The999eagle#6302**\n\nAll commands must be prefixed with `{0}`.\n\n'.format(globals.config.cmd_tag.strip(), globals.version_str)
	help_msg += Helptext.get_help(message)
	await send_message(message.author, help_msg)

@Helptext('Show mods on the server.')
@Command('mods')
async def cmd_mods(message, args):
	server = message.server
	mod_roles = []
	text = ''
	for r in server.roles:
		if r.permissions.manage_messages or r.permissions.kick_members or r.permissions.ban_members:
			mod_roles.append(r)
	for m in server.members:
		is_mod = False
		if not m.bot:
			for r in m.roles:
				if r in mod_roles:
					is_mod = True
		if is_mod:
			if m.status == discord.Status.online:
				text += ':large_blue_circle:'
			elif m.status == discord.Status.idle:
				text += ':red_circle:'
			else:
				text += ':black_circle:'
			text += ' **' + m.name + '#' + m.discriminator + '**\n'
	if text == '':
		text = 'No mods are on this server somehow'
	await send_message(message.channel, text)

@Helptext('Shows information about a user.')
@Command('info', '<@user>')
async def cmd_info(message, args):
	if len(args) != 1 or not is_usermention(args[0]):
		await send_message(message.channel, 'Usage: `{0}info <@user>`'.format(globals.config.cmd_tag))
		return
	id = get_id_from_mention(args[0])
	user = None
	for m in message.server.members:
		if m.id == id:
			user = m
	if user == None:
		await send_message(message.channel, 'I don\'t know that user')
		return
	text = 'Information about {0}\n'.format(args[0])
	text += '--------------------------\n'
	text += '**Username:** {0}#{1}\n'.format(user.name, str(user.discriminator))
	text += '**User ID:** {0}\n'.format(str(user.id))
	text += '**Created:** {0}\n'.format(str(user.created_at.replace(microsecond=0)))
	text += '**Bot:** '
	if user.bot:
		text += 'yes\n'
	else:
		text += 'no\n'
	if user.avatar_url != '':
		text += '**Avatar URL:** {0}\n'.format(user.avatar_url)
	await send_message(message.channel, text)

@Helptext('Replies with "Pong".')
@Command('ping')
async def cmd_ping(message, args):
	result = await ping(globals.client.ws.host)
	if result == -1:
		await send_message(message.channel, 'The discord servers did not answer my ping, somehow you still can read this.')
	else:
		await send_message(message.channel, 'Pong\nRTT: {0}ms'.format(result))

@Helptext('Generate a random number between 1 and <number> (both inclusive).','D<number>')
@Command('roll')
async def cmd_roll(message, args):
	if len(args) == 1 and args[0].startswith('d') and is_int(args[0][1:]):
		number = int(args[0][1:])
		if number <= 1:
			await send_message(message.channel, 'Try a number greater than 1, baka!')
		else:
			await send_message(message.channel, 'Rolling a ' + str(number) + ' sided :game_die: ...\nRolled a ' + str(random.randint(1, number)))
	else:
		await send_message(message.channel, 'Usage: `{0}roll D<number>`'.format(globals.config.cmd_tag))

@Helptext('Choose between different options.','<text> | <text> | ...')
@Command('choose')
async def cmd_choose(message, args):
	if len(args) == 0:
		await send_message(message.channel, 'Usage: `{0}choose <text> | <text> | ...`'.format(globals.config.cmd_tag))
		return
	choices = [x.strip() for x in ' '.join(args).split('|')]
	if len(choices) == 1:
		await send_message(message.channel, 'Do you really want me to choose from a single option? Well, let me think about this for a while....')
		await asyncio.sleep(10)
		await send_message(message.channel, 'I finally decided! I pick **{0}**.'.format(choices[0]))
	else:
		choice = choices[random.randint(0, len(choices) - 1)]
		await send_message(message.channel, 'I pick **{0}**.'.format(choice))

@Helptext('Have Baka-chan calculate something for you.', '<Number 1> <Operator> <Number 2>')
@Command('calc')
async def cmd_calc(message, args):
	if len(args) <= 2:
		await send_message(message.channel, 'baka')
	else:
		num1 = float(args[2])
		num2 = float(args[4])
		operator = args[3]
		result = str(num1 operator num2)
		await send_message(message.channel, result)

@Helptext('Have Baka-chan poke you or another user.','[<@user>]')
@Command('poke')
async def cmd_poke(message, args):
	if len(args) == 0:
		poke = message.author.mention
	elif is_usermention(args[0]):
		poke = args[0]
	else:
		poke = message.author.mention
	text = '*Baka-chan pokes ' + poke + '*'
	await send_message(message.channel, text)
	await send_image(message.channel, 'poke')

@Helptext('Have Baka-chan slap you or another user.','[<@user>]')
@Command('slap')
async def cmd_slap(message, args):
	if len(args) == 0:
		slap = message.author.mention
	elif is_usermention(args[0]):
		slap = args[0]
	else:
		slap = message.author.mention
	text = '*Baka-chan slaps ' + slap + '*'
	await send_message(message.channel, text)
	await send_image(message.channel, 'slap')

@Helptext('Rates someone or something from 0 to 100.','<waifu>')
@Command('ratewaifu')
async def cmd_ratewaifu(message, args):
	if len(args) == 1:
		await send_message(message.channel, 'I\'d rate {0} a **{1:.2f}/100**'.format(args[0], random.randint(0, 10000) / 100.0))
	else:
		await send_message(message.channel, 'Usage: `{0}ratewaifu <waifu>`'.format(globals.config.cmd_tag))

@Helptext('Shows a link to invite me to other servers.')
@Command('invite',allow_private=True)
async def cmd_invite(message, args):
	await send_message(message.channel, 'If you want to invite me to your server, use this link: https://discordapp.com/oauth2/authorize?client_id={0}&scope=bot.'.format(globals.client.user.id))

@Helptext('Pay respects.')
@Command('f')
async def cmd_f(message, args):
	await send_image(message.channel, 'pay_respects')

@Helptext('Shows an image with "lewd".')
@Command('lewd')
async def cmd_lewd(message, args):
	await send_image(message.channel, 'lewd')

@Helptext('Show information about me.')
@Command('about',allow_private=True)
async def cmd_about(message, args):
	text = '__**Baka-chan** {0}__\n**Made by:** The999eagle#6302\n**API-Binding:** discord.py v0.13\n**Current uptime:** '.format(globals.version_str)
	uptime_total = int((datetime.datetime.now() - globals.start_time).total_seconds())
	uptime_sec = uptime_total % 60
	uptime_total = int((uptime_total - uptime_sec) / 60)
	uptime_min = uptime_total % 60
	uptime_total = int((uptime_total - uptime_min) / 60)
	uptime_hours = uptime_total % 24
	uptime_total = int((uptime_total - uptime_hours) / 24)
	uptime_days = uptime_total
	if uptime_days > 0:
		text += '{0}d '.format(uptime_days)
	text += '{0}h {1}min {2}s'.format(uptime_hours, uptime_min, uptime_sec)
	await send_message(message.channel, text)

@Command('boom')
@StaticResponse('boom')
async def cmd_boom(message, args): pass

@Command('notwork')
@StaticResponse('notwork')
async def cmd_notwork(message, args): pass

@Command('trustme')
@StaticResponse('trustme')
async def cmd_trustme(message, args): pass

@Command('calmdown')
@StaticResponse('calmdown')
async def cmd_calmdown(message, args): pass

@Command('cover_up')
@StaticResponse('cover_up')
async def cmd_cover_up(message, args): pass

@Command('youaintkawaii')
@StaticResponse('you_aint_kawaii')
async def cmd_you_aint_kawaii(message, args): pass

@Command('thumbsup')
async def cmd_thumbs_up(message, args):
	await send_random_image(message.channel, 'thumbs_up')

@Command('fu')
async def cmd_fu(message, args):
	await send_random_image(message.channel, 'fu')

@Command('gtfo')
async def cmd_gtfo(message, args):
	await send_random_image(message.channel, 'gtfo')

@Command('wtf')
async def cmd_wtf(message, args):
	await send_random_image(message.channel, 'wtf')