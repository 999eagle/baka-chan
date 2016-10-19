import asyncio

from command import Command
import globals
from util import *

class Rps:
	"""Manages RPS games."""
	_instance = None
	@classmethod
	def instance(cls):
		if Rps._instance == None:
			Rps._instance = Rps()
		return Rps._instance

	def __init__(self):
		self.active_games = []

	def start_game(self, server, player1, player2, bet, is_rpsls):
		if globals.data_coins.getcoins(server, player1) < bet:
			return (False, '{1} only has {2} {0}')
		if globals.data_coins.getcoins(server, player2) < bet:
			return (False, '{3} only has {4} {0}')
		for game in self.active_games:
			if game.p1 == player1 or game.p2 == player1:
				return (False, '{1} is already in a game of rock-paper-scissors')
			if game.p1 == player2 or game.p2 == player2:
				return (False, '{3} is already in a game of rock-paper-scissors')
		game = RpsGame(server, player1, player2, bet, is_rpsls)
		self.active_games.append(game)
		asyncio.ensure_future(self.game_timeout(game))
		return (True, game)

	async def game_timeout(self, game):
		await asyncio.sleep(globals.config.rps_timeout)
		if game.status == 0:
			self.end_game(game)
			await send_message(game.channel, '<@{0}> didn\'t accept <@{1}>\'s challenge in time.'.format(game.p2, game.p1))

	def end_game(self, game):
		self.active_games.remove(game)

	def get_activegame(self, user):
		for game in self.active_games:
			if game.p1 == user or game.p2 == user:
				return game
		return None

class RpsGame:
	def __init__(self, server, player1, player2, bet, is_rpsls):
		self.p1 = player1
		self.p2 = player2
		self.p1_choice = None
		self.p2_choice = None
		self.bet = bet
		self.is_rpsls = is_rpsls
		self.server = server
		# status
		# 0: game started
		# 1: player2 accepted
		# 2: players made their choice
		self.status = 0

	def get_winner(self):
		if self.status != 2:
			return None
		winning = {
			0:(2,3), # rock beats scissors, lizard
			1:(0,4), # paper beats rock, spock
			2:(1,3), # scissors beats paper, lizard
			3:(1,4), # lizard beats paper, spock
			4:(0,2) }# spock beats rock, scissors
		if self.p2_choice == self.p1_choice:
			return 0 # tie
		elif self.p2_choice in winning[self.p1_choice]:
			return 1 # player1
		else:
			return 2 # player2

@Command('rps', help = 'Challenge a user to a game of rock-paper-scissors. The winner gets the bet.', usage = ('<@user>','<bet:int>',('optional','rpsls')))
async def cmd_rps(message, mention, bet, rpsls):
	server = message.server.id
	rps = Rps.instance()
	player1_id = message.author.id
	player2_id = mention.id
	if player1_id == player2_id:
		await send_message(message.channel, 'You can\'t challenge yourself to a game of rock-paper-scissors.')
		return
	if bet <= 0:
		await send_message(message.channel, 'You have to bet at least 1 {0}'.format(globals.config.currency_name))
		return
	if rpsls == None:
		rpsls = False
	result = rps.start_game(server, player1_id, player2_id, bet, rpsls)
	if result[0] == False:
		await send_message(message.channel, result[1].format(globals.config.currency_name, message.author.mention, globals.data_coins.getcoins(server, player1_id), mention.mention, globals.data_coins.getcoins(server, player2_id)))
	else:
		result[1].channel = message.channel
		await send_message(message.channel, '{0}, you have been challenged to a game of rock-paper-scissors. You can accept in the next {2} seconds with `{1}rps a`.'.format(mention.mention, globals.config.cmd_tag, globals.config.rps_timeout))

@Command('rps', usage = ('a',))
async def cmd_rps_accept(message):
	server = message.server.id
	rps = Rps.instance()
	player_id = message.author.id
	game = rps.get_activegame(player_id)
	if game == None:
		await send_message(message.channel, '{0}, you have not been challenged to a game of rock-paper-scissors.'.format(message.author.mention))
	elif game.status != 0:
		await send_message(message.channel, 'This game is already running.')
	elif game.p1 == player_id:
		await send_message(message.channel, '{0}, you started this game yourself, you don\'t have to accept.'.format(message.author.mention))
	else:
		game.status = 1 # player2 accepted
		if game.is_rpsls:
			option_text = '"rock", "paper", "scissors", "lizard" or "spock"'
			options = ('rock', 'paper', 'scissors', 'lizard', 'spock')
		else:
			option_text = '"rock", "paper" or "scissors"'
			options = ('rock','paper','scissors')
		await send_message(game.channel, '{0}, you accepted <@{1}>\'s challenge. Both please DM me your choices. No special tag is needed, just send me {2}.'.format(message.author.mention, game.p1, option_text))
		asyncio.ensure_future(cmd_rps_continue(game, 1, options))
		asyncio.ensure_future(cmd_rps_continue(game, 2, options))

async def cmd_rps_continue(game, player_idx, options:list):
	if player_idx == 1:
		player = game.p1
	else:
		player = game.p2
	def check(msg):
		return msg.author.id == player and msg.content.lower() in options and msg.channel.is_private
	msg = await globals.client.wait_for_message(check=check)
	choice = options.index(msg.content.lower())
	if player_idx == 1:
		game.p1_choice = choice
		game.p1_text = options[choice]
	else:
		game.p2_choice = choice
		game.p2_text = options[choice]
	await send_message(msg.channel, 'You chose ' + options[choice])

	if game.p1_choice != None and game.p2_choice != None and game.status != 2:
		game.status = 2
		winner = game.get_winner()
		message = ''
		if winner == 0:
			message = 'both of you chose ' + game.p1_text + '. That\'s a tie.'
		else:
			message = '<@{0}> chose {1}, <@{2}> chose {3}. '.format(game.p1, game.p1_text, game.p2, game.p2_text)
			if winner == 1:
				message += 'That\'s a win for <@' + game.p1 + '>!'
				globals.data_coins.setcoins(game.server, game.p1, globals.data_coins.getcoins(game.server, game.p1) + game.bet)
				globals.data_coins.setcoins(game.server, game.p2, globals.data_coins.getcoins(game.server, game.p2) - game.bet)
			elif winner == 2:
				message += 'That\'s a win for <@' + game.p2 + '>!'
				globals.data_coins.setcoins(game.server, game.p1, globals.data_coins.getcoins(game.server, game.p1) - game.bet)
				globals.data_coins.setcoins(game.server, game.p2, globals.data_coins.getcoins(game.server, game.p2) + game.bet)
		await send_message(game.channel, message)
		Rps.instance().end_game(game)
