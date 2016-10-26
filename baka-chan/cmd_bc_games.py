import operator
import random
import asyncio

from command import Command
from data import DataPermissions
import globals
from util import *

@Command(globals.config.currency_cmd, 'bc', help = 'Shows how many {0} you have or another user has.'.format(globals.config.currency_name), usage = (('optional','<@user>'),))
async def cmd_coins_display(message, mention):
	if mention == None:
		user_id = message.author.id
		user_mention = message.author.mention
	else:
		user_id = mention.id
		user_mention = mention.mention
	coins = str(globals.data_coins.getcoins(message.server.id, user_id))
	await send_message(message.channel, '{1} has {2} {0}'.format(globals.config.currency_name, user_mention, coins))

@Command(globals.config.currency_cmd, 'bc', help = 'Gives your own {0} to another user.'.format(globals.config.currency_name), usage = ('give','<@user>','<amount:int>'))
async def cmd_coins_give(message, mention, amount):
	if message.author.id == mention.id:
		await send_message(message.channel, 'No need to give yourself your own {0}'.format(globals.config.currency_name))
		return
	if amount > 0:
		points = globals.data_coins.getcoins(server, mention.id) + amount
		points2 = globals.data_coins.getcoins(server, message.author.id) - amount
		if points2 >= 0:
			globals.data_coins.setcoins(server, mention.id, points)
			globals.data_coins.setcoins(server, message.author.id, points2)
			await send_message(message.channel, '{1} received {2} {0} from {4} and now has {3} {0}'.format(globals.config.currency_name, mention.mention, amount, points, message.author.mention))
		else:
			await send_message(message.channel, '{4} wanted to give {2} {0} to {1}, but only has {5} {0}'.format(globals.config.currency_name, mention.mention, amount, points, message.author.mention, globals.data_coins.getcoins(server, message.author.id)))
	else:
		await send_message(message.channel, '{2} wanted to steal {0} from {1}!'.format(globals.config.currency_name, mention.mention, message.author.mention))

@Command(globals.config.currency_cmd, 'bc', help = 'Spawns {0} on a user.'.format(globals.config.currency_name), usage = ('spawn','<@user>','<amount:int>'), permission = DataPermissions.Permission.coins_spawn)
async def cmd_coins_spawn(message, mention, amount):
	if amount > 0:
		points = globals.data_coins.getcoins(message.server.id, mention.id) + amount
		globals.data_coins.setcoins(message.server.id, mention.id, points)
		await send_message(message.channel, '{1} received {2} {0} and now has {3} {0}'.format(globals.config.currency_name, mention.mention, amount, points))
	else:
		await send_message(message.channel, 'Only a positive amount of {0} can be spawned.'.format(globals.config.currency_name))

@Command(globals.config.currency_cmd, 'bc', help = 'Despawns {0} from a user.'.format(globals.config.currency_name), usage = ('despawn','<@user>','<amount:int>'), permission = DataPermissions.Permission.coins_despawn)
async def cmd_coins_despawn(message, mention, amount):
	if amount > 0:
		points = globals.data_coins.getcoins(message.server.id, mention.id) - amount
		if points >= 0:
			globals.data_coins.setcoins(message.server.id, mention.id, points)
			await send_message(message.channel, '{1} lost {2} {0} and now has {3} {0}'.format(globals.config.currency_name, mention.mention, amount, points))
		else:
			await send_message(message.channel, '{1} only has {2} {0}'.format(globals.config.currency_name, mention.mention, points + amount))
	else:
		await send_message(message.channel, 'Only a positive amount of {0} can be despawned.'.format(globals.config.currency_name))

@Command('leaderboard', help = 'Displays the leaderboard of {0}.'.format(globals.config.currency_name))
async def cmd_leaderboard(message):
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

@Command('slots', help = 'Play a round of slots.', usage = ('<bet:int>',))
async def cmd_slots(message, bet):
	server = message.server.id
	if bet <= 0:
		await send_message(message.channel, 'You have to bet at least 1 {0}'.format(globals.config.currency_name))
		return
	user_id = message.author.id
	points = globals.data_coins.getcoins(server, user_id)
	if bet > points:
		await send_message(message.channel, 'You only have {0} {1}'.format(points, globals.config.currency_name))
	else:
		slots_items = globals.config.slots_items
		slots_count = globals.config.slots_count
		slots_bonuses = globals.config.slots_bonuses

		slot_max = len(slots_items) - 1
		text = ':slot_machine: Spending {0} {1}\nResults:'.format(bet, globals.config.currency_name)
		numbers = {}
		for i in range(0, slot_max + 1):
			numbers.setdefault(i, 0)
		for i in range(0, slots_count):
			number = random.randint(0, slot_max)
			text += slots_items[number] + ' '
			numbers[number] += 1
		text += '\n' + message.author.mention + ', '
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
		points -= bet
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
		points += bet * win
		globals.data_coins.setcoins(server, user_id, int(points))
		await send_message(message.channel, text)
