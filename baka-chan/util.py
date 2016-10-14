import discord, discord.errors

import globals
import log
from platform_specific import PlatformSpecific

def is_int(s):
	try:
		int(s)
		return True
	except ValueError:
		return False

def is_mention(s:str):
	return s.startswith('<@') and s.endswith('>')

def is_usermention(s:str):
	if not is_mention(s):
		return False
	# user mentions are: <@id> for normal usernames and <@!id> for members with a nickname
	return (s[2] != '&' and is_int(s[2:-1])) or (s[2] == '!' and is_int(s[3:-1]))

def get_id_from_mention(s:str):
	if not is_mention(s):
		raise ValueError
	if is_int(s[2:-1]):
		return s[2:-1]
	else:
		return s[3:-1]

def is_rolemention(s:str):
	return is_mention(s) and s[2] == '&' and is_int(s[3:-1])

async def send_message(channel, message):
	if isinstance(channel, discord.Channel):
		log.log_debug('Sending message to channel {0} on {1}. Content: {2}'.format(channel.id, channel.server.id, message))
	elif isinstance(channel, discord.User):
		log.log_debug('Sending message to user {0}. Content: {1}'.format(channel.id, message))
	try:
		await globals.client.send_message(channel, message)
		return True
	except discord.errors.Forbidden:
		log.log_warning('Forbidden to speak in channel {0}({1}) on {2}({3})'.format(channel.name, channel.id, channel.server.name, channel.server.id))
		return False

images = {'pay_respects':('pay_respects.jpg',''),
          'poke':('poke.jpg','http://s15.postimg.org/a2515gqzf/poke.jpg'),
          'calmdown':('calmdown.jpg',''),
          'cover_up':('cover_up.jpg',''),
          'gtfo1':('gtfo1.jpg','http://s12.postimg.org/p2prv7c3x/gtfo1.jpg'),
          'gtfo2':('gtfo2.jpg',''),
          'strip':('strip.jpg',''),
          'thumbs_up1':('thumbs1.png',''),
          'thumbs_up2':('thumbs2.jpg',''),
          'thumbs_up3':('thumbs3.jpg',''),
          'wtf1':('wtf1.jpg',''),
          'wtf2':('wtf2.jpg',''),
          'wtf3':('wtf3.png',''),
          'you_aint_kawaii':('You aint kawaii.jpg',''),
          'lewd':('lewd.jpg',''),
          'boom':('','https://giphy.com/gifs/computer-gZBYbXHtVcYKs'),
          'notwork':('notwork.png','http://i.imgur.com/CA1RMf7.png'),
          'trustme':('trustme.png',''),
          'silver':('silver.gif',''),
          'slap':('slap1.gif','')}

async def send_image(channel, image):
	if isinstance(channel, discord.Channel):
		log.log_debug('Sending image to channel {0} on {1}. Key: {2}'.format(channel.id, channel.server.id, image))
	elif isinstance(channel, discord.User):
		log.log_debug('Sending image to user {0}. Key: {1}'.format(channel.id, message))
	send_directly = True
	if not image in images:
		return False
	try:
		data = images[image]
		if send_directly and data[0] != '':
				await globals.client.send_file(channel, PlatformSpecific.inst().convert_path('img\\' + data[0]))
				return True
		else:
			if data[1] != '':
				await globals.client.send_message(channel, data[1])
				return True
	except discord.errors.Forbidden:
		log.log_warning('Forbidden to speak in channel {0}({1}) on {2}({3})'.format(channel.name, channel.id, channel.server.name, channel.server.id))
	return False

def sender_has_permission(message, perm):
	if message.server == None:
		return True
	try:
		return globals.data_permissions.user_has_permission(message.server.id, message.author.id, perm)
	except ValueError:
		return False

def is_steam_user_id(user):
	return is_int(user) and len(str(user)) == 17