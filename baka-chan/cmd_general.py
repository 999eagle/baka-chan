import discord
import datetime
import random
import asyncio
import time

from command import Command, StaticResponse
import globals
from util import *
from errors import *

@Command('help', help = 'Shows this help.', allow_private = True)
async def cmd_help(message):
	help_msg = '**Baka-chan** {1}\nMade by **The999eagle#6302**\n\n'.format(globals.config.cmd_tag.strip(), globals.version_str)
	help_msg += Command.get_help(message)
	lines = help_msg.split('\n')
	current_len = 0
	current_text = ''
	for line in lines:
		line_len = len(line)
		if current_len + line_len + 1 > 2000:
			await send_message(message.author, current_text)
			current_len = line_len
			current_text = line
		else:
			current_text += '\n' + line
			current_len += 1 + line_len
	await send_message(message.author, current_text)

@Command('mods', help = 'Shows the mods on the server.')
async def cmd_mods(message):
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

@Command('info', help = 'Shows information about a user.', usage = ('<@user>',))
async def cmd_info(message, mention):
	id = mention.id
	user = None
	for m in message.server.members:
		if m.id == id:
			user = m
	if user == None:
		await send_message(message.channel, 'I don\'t know that user')
		return
	text = 'Information about {0}\n'.format(mention.mention)
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

@Command('ping', help = 'Replies with "Pong" and the current round trip time from the bot to the discord servers.')
async def cmd_ping(message):
	result = await ping(globals.client.ws.host)
	if result == -1:
		await send_message(message.channel, 'The discord servers did not answer my ping, somehow you still can read this.')
	else:
		await send_message(message.channel, 'Pong\nRTT: {0}ms'.format(result))

@Command('roll', help = 'Generate a random number between 1 and <number>.', usage = ('*D<number>',))
async def cmd_roll(message, *args):
	if len(args) == 1 and args[0].startswith('d') and is_int(args[0][1:]):
		number = int(args[0][1:])
		if number <= 1:
			await send_message(message.channel, 'Try a number greater than 1, baka!')
		else:
			await send_message(message.channel, 'Rolling a ' + str(number) + ' sided :game_die: ...\nRolled a ' + str(random.randint(1, number)))
	else:
		raise ArgumentParseException()

@Command('choose', help = 'Choose between different options.', usage = ('*<text> | <text> | ...',))
async def cmd_choose(message, *args):
	if len(args) == 0:
		raise ArgumentParseException()
	choices = [x.strip() for x in ' '.join(args).split('|')]
	if len(choices) == 1:
		await send_message(message.channel, 'Do you really want me to choose from a single option? Well, let me think about this for a while....')
		await asyncio.sleep(10)
		await send_message(message.channel, 'I finally decided! I pick **{0}**.'.format(choices[0]))
	else:
		choice = choices[random.randint(0, len(choices) - 1)]
		await send_message(message.channel, 'I pick **{0}**.'.format(choice))

@Command('calc', help = 'Have Baka-chan calculate something for you.', usage = ('<number 1:float>','<operator:str>','<number 2:float>'))
async def cmd_calc(message, number1, operator, number2):
	if operator == '+':
		result = number1 + number2
	elif operator == '-':
		result = number1 - number2
	elif operator == '*':
		result = number1 * number2
	elif operator == '/':
		result = number1 / number2
	else:
		raise ArgumentParseException()
	await send_message(message.channel, '{0} {1} {2} = {3}'.format(number1, operator, number2, result))

@Command('poke', help = 'Have Baka-chan poke you or another user.', usage = (('optional','<@user>'),))
async def cmd_poke(message, mention):
	if mention == None:
		poke = message.author.mention
	else:
		poke = mention.mention
	text = '*Baka-chan pokes ' + poke + '*'
	await send_message(message.channel, text)
	await send_image(message.channel, 'poke')

@Command('slap', help = 'Have Baka-chan slap you or another user.', usage = (('optional','<@user>'),))
async def cmd_slap(message, mention):
	if mention == None:
		slap = message.author.mention
	else:
		slap = mention.mention
	text = '*Baka-chan slaps ' + slap + '*'
	await send_message(message.channel, text)
	await send_image(message.channel, 'slap')

@Command('ratewaifu', help = 'Rates someone or something from 0 to 100.', usage = ('<waifu:str>',))
async def cmd_ratewaifu(message, waifu):
	await send_message(message.channel, 'I\'d rate {0} a **{1:.2f}/100**'.format(waifu, random.randint(0, 10000) / 100.0))

@Command('invite', help = 'Shows a link to invite me to other servers.', allow_private = True)
async def cmd_invite(message):
	await send_message(message.channel, 'If you want to invite me to your server, use this link: https://discordapp.com/oauth2/authorize?client_id={0}&scope=bot.'.format(globals.client.user.id))

@Command('f', help = 'Pay respects.')
async def cmd_f(message, args):
	await send_image(message.channel, 'pay_respects')

@Command('lewd', help = 'Shows an image with "lewd".')
async def cmd_lewd(message, args):
	await send_image(message.channel, 'lewd')

@Command('about', help = 'Show information about me.', allow_private = True)
async def cmd_about(message):
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

@Command('8ball', help = 'Let me answer your question.', usage = ('*<question>',))
async def cmd_8ball(message, *args):
	await send_message(message.channel, texts_8ball[random.randint(0, len(texts_8ball) - 1)])


@Command('boom')
@StaticResponse('boom')
async def cmd_boom(): pass

@Command('notwork')
@StaticResponse('notwork')
async def cmd_notwork(): pass

@Command('trustme')
@StaticResponse('trustme')
async def cmd_trustme(): pass

@Command('calmdown')
@StaticResponse('calmdown')
async def cmd_calmdown(): pass

@Command('cover_up')
@StaticResponse('cover_up')
async def cmd_cover_up(): pass

@Command('youaintkawaii')
@StaticResponse('you_aint_kawaii')
async def cmd_you_aint_kawaii(): pass

@Command('thumbsup')
async def cmd_thumbs_up(message):
	await send_random_image(message.channel, 'thumbs_up')

@Command('fu')
async def cmd_fu(message):
	await send_random_image(message.channel, 'fu')

@Command('gtfo')
async def cmd_gtfo(message):
	await send_random_image(message.channel, 'gtfo')

@Command('wtf')
async def cmd_wtf(message):
	await send_random_image(message.channel, 'wtf')

texts_8ball = (# standard answers
               'It is certain.',
               'It is decidedly so.',
               'Without a doubt.',
               'Yes, definitely.',
               'You may rely on it.',
               'As I see it, yes.',
               'Most likely.',
               'Outlook good.',
               'Yes.',
               'Signs point to yes.',
               'Reply hazy try again.',
               'Ask again later.',
               'Better not tell you now.',
               'Cannot predict now.',
               'Concentrate and ask again.',
               'Don\'t count on it.',
               'My reply is no.',
               'My sources say no.',
               'Outlook not so good.',
               'Very doubtful.',
               # custom answers
               'I think so.',
               'My sources say yes.',
               'My reply is yes.',
               'Of course.',
               'Yes... uhm, no... What was the question again?',
               'That\'s a secret.',
               'Ask someone who cares.',
               'I\'ll answer you if you give me some cake.',
               'Do you really want to know?',
               'Lame question. Next!',
               'Don\'t ask me, I\'m just a random number generator.',
               'Not without your daddy\'s wallet.',
               'You\'d be better off just going to school.',
               'Yeah and I\'m the pope.',
               )
