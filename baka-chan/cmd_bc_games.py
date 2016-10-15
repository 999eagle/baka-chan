import operator
import random
import asyncio

from command import Command, Helptext
from data import DataPermissions
import globals
from util import *

@Helptext('Take {0} from a user.'.format(globals.config.currency_name),'despawn <@user> <{0}>'.format(globals.config.currency_name),permission=DataPermissions.Permission.coins_despawn)
@Helptext('Give a user {0}.'.format(globals.config.currency_name),'spawn <@user> <{0}>'.format(globals.config.currency_name),permission=DataPermissions.Permission.coins_spawn)
@Helptext('Give your own {0} to another user'.format(globals.config.currency_name),'give <@user> <{0}>'.format(globals.config.currency_name))
@Helptext('Shows how many {0} a user has. If no user is given, shows how many {0} you have.'.format(globals.config.currency_name),'[<@user>]')
@Command(globals.config.currency_cmd, 'bc')
async def cmd_points(message, args):
	server = message.server.id
	user_id = None
	if len(args) == 0:
		user_id = message.author.id
	elif is_usermention(args[0]):
		user_id = get_id_from_mention(args[0])
	if user_id != None:
		points = str(globals.data_coins.getcoins(server, user_id))
		await send_message(message.channel, '<@{1}> has {2} {0}'.format(globals.config.currency_name, user_id, points))
	else:
		if len(args) == 3 and args[0] in ['spawn', 'give', 'despawn'] and is_usermention(args[1]) and is_int(args[2]):
			user_id = get_id_from_mention(args[1])
			if args[0] == 'spawn':
				if not sender_has_permission(message, DataPermissions.Permission.coins_spawn):
					await send_message(message.channel, globals.message_no_permission)
					return
				if int(args[2]) > 0:
					points = globals.data_coins.getcoins(server, user_id) + int(args[2])
					globals.data_coins.setcoins(server, user, points)
					await send_message(message.channel, '<@{1}> received {2} {0} and now has {3} {0}'.format(globals.config.currency_name, user_id, args[2], str(points)))
				else:
					await send_message(message.channel, 'To deduct {0} use `{1}{2} despawn <@user> <{0}>`'.format(globals.config.currency_name, globals.config.cmd_tag, globals.config.currency_cmd))
			elif args[0] == 'despawn':
				if not sender_has_permission(message, DataPermissions.Permission.coins_despawn):
					await send_message(message.channel, globals.message_no_permission)
					return
				if int(args[2]) > 0:
					points = globals.data_coins.getcoins(server, user_id) - int(args[2])
					if points >= 0:
						globals.data_coins.setcoins(server, user_id, points)
						await send_message(message.channel, '<@{1}> lost {2} {0} and now has {3} {0}'.format(globals.config.currency_name, user_id, args[2], str(points)))
					else:
						await send_message(message.channel, '<@{1}> only has {2} {0}'.format(globals.config.currency_name, user_id, str(globals.data_coins.getcoins(server, user_id))))
				else:
					await send_message(message.channel, 'To spawn {0} use `{1}{2} spawn <@user> <{0}>`'.format(globals.config.currency_name, globals.config.cmd_tag, globals.config.currency_cmd))
			elif args[0] == 'give':
				user2_id = message.author.id
				if user2_id == user_id:
					await send_message(message.channel, 'No need to give yourself your own {0}'.format(globals.config.currency_name))
					return
				if int(args[2]) > 0:
					points = globals.data_coins.getcoins(server, user_id) + int(args[2])
					points2 = globals.data_coins.getcoins(server, user2_id) - int(args[2])
					if points2 >= 0:
						globals.data_coins.setcoins(server, user_id, points)
						globals.data_coins.setcoins(server, user2_id, points2)
						await send_message(message.channel, '<@{1}> received {2} {0} from <@{4}> and now has {3} {0}'.format(globals.config.currency_name, user_id, args[2], str(points), user2_id))
					else:
						await send_message(message.channel, '<@{4}> wanted to give {2} {0} to <@{1}>, but only has {5} {0}'.format(globals.config.currency_name, user_id, args[2], str(points), user2_id, str(globals.data_coins.getcoins(server, user2))))
				else:
					await send_message(message.channel, '<@{2}> wanted to steal {0} from <@{1}>!'.format(globals.config.currency_name, user_id, user2_id))
		else:
			await send_message(message.channel, 'Usage: `{1}{2} [<@user> | (give | spawn | despawn) <@user> <{0}>]`'.format(globals.config.currency_name, globals.config.cmd_tag, globals.config.currency_cmd))

@Helptext('Displays the leaderboard of {0}.'.format(globals.config.currency_name))
@Command('leaderboard')
async def cmd_leaderboard(message, args):
	server = message.server.id
	pts = globals.data_coins.getservercoins(server)
	text = ''
	counter = 1
	for p in sorted(pts.items(), key=operator.itemgetter(1), reverse=True):
		if counter == 1:
			text += ':first_place:'
		elif counter == 2:
			text += ':second_place:'
		elif counter == 3:
			text += ':third_place:'
		counter += 1
		text += '<@{1}> with {2} {0}\n'.format(globals.config.currency_name, p[0], str(p[1]))
	if text == '':
		await send_message(message.channel, 'No users have {0} at the moment.'.format(globals.config.currency_name))
	else:
		await send_message(message.channel, text)

@Helptext('Play a round of slots.','<bet>')
@Command('slots')
async def cmd_slots(message, args):
	server = message.server.id
	if len(args) == 0 or not is_int(args[0]):
		await send_message(message.channel, 'Usage: `{0}slots <{1}>`'.format(globals.config.cmd_tag, globals.config.currency_name))
	else:
		spending = int(args[0])
		if spending <= 0:
			await send_message(message.channel, 'You have to bet at least 1 {0}'.format(globals.config.currency_name))
			return
		user_id = message.author.id
		points = globals.data_coins.getcoins(server, user_id)
		if spending > points:
			await send_message(message.channel, 'You only have {0} {1}'.format(points, globals.config.currency_name))
		else:
			slots_items = globals.config.slots_items
			slots_count = globals.config.slots_count
			slots_bonuses = globals.config.slots_bonuses

			slot_max = len(slots_items) - 1
			text = ':slot_machine: Spending {0} {1}\nResults:'.format(spending, globals.config.currency_name)
			numbers = {}
			for i in range(0, slot_max + 1):
				numbers.setdefault(i, 0)
			for i in range(0, slots_count):
				number = random.randint(0, slot_max)
				text += slots_items[number] + ' '
				numbers[number] += 1
			text += '\n' + user + ', '
			highest = 0
			bonus = 0
			bonustext = ''
			wins = {}
			for i in range(0, slots_count):
				wins.setdefault(i + 1, 0)
			for i in range(0, slot_max + 1):
				n = numbers[i]
				if n >= 1 and slots_items[i] in slots_bonuses.keys():
					bonus += 1
					bonustext += slots_items[i] + ' ' + slots_bonuses[slots_items[i]] + ' '
				if n >= 1:
					wins[n] += 1
			points -= spending
			win = 0
			if wins[5] == 1:
				text += 'you got five of a kind! Are you a hacker?'
				win = 12
			elif wins[4] == 1:
				text += 'you got four of a kind! You\'re really lucky!'
				win = 6
			elif wins[3] == 1 and wins[2] == 1:
				text += 'you got a full house! Are you a hacker?'
				win = 12
			elif wins[3] == 1:
				text += 'you got a triple!'
				win = 4
			elif wins[2] == 2:
				text += 'you got two pairs! You\'re really lucky!'
				win = 6
			elif wins[2] == 1:
				text += 'you got a pair!'
				win = 2
			else:
				text += 'you won nothing.'
				win = 0

			if win > 0:
				if bonus > 0:
					text += ' You got these bonuses: ' + bonustext
				win = win * (2 ** bonus)
				text += '\nYou won ' + str(win) + 'x your bet.'
			points += spending * win
			globals.data_coins.setcoins(server, user_id, int(points))
			await send_message(message.channel, text)
