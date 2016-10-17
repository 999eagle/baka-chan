import discord, discord.errors
import os
import platform
import subprocess
import asyncio
import random
import time
import re

import globals
import log
from platform_specific import PlatformSpecific
from data import DataPermissions

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

image_counts = {'fu': 2, 'gtfo': 3, 'thumbs_up': 4, 'wtf': 4}
images = {'boom':('','https://giphy.com/gifs/computer-gZBYbXHtVcYKs'),
          'calmdown':('calmdown.jpg',''),
          'cover_up':('cover_up.jpg',''),
          'fu1':('fu1.jpg',''),
          'fu2':('fu2.jpg',''),
          'gtfo1':('gtfo1.jpg','http://s12.postimg.org/p2prv7c3x/gtfo1.jpg'),
          'gtfo2':('gtfo2.jpg',''),
          'gtfo3':('gtfo3.jpg',''),
          'lewd':('lewd.jpg',''),
          'lewdapprove':('lewdbutiapprove.jpg',''),
          'notwork':('notwork.jpg','http://i.imgur.com/CA1RMf7.png'),
          'pay_respects':('pay_respects.jpg',''),
          'poke':('poke.jpg','http://s15.postimg.org/a2515gqzf/poke.jpg'),
          'thumbs_up1':('thumbs1.jpg',''),
          'thumbs_up2':('thumbs2.jpg',''),
          'thumbs_up3':('thumbs3.jpg',''),
          'thumbs_up4':('thumbs4.jpg',''),
          'trustme':('trustme.jpg',''),
          'wtf1':('wtf1.jpg',''),
          'wtf2':('wtf2.jpg',''),
          'wtf3':('wtf3.jpg',''),
          'wtf4':('wtf4.jpg',''),
          'you_aint_kawaii':('You_aint_kawaii.jpg',''),
          }

async def send_image(channel, image):
	if isinstance(channel, discord.Channel):
		log.log_debug('Sending image to channel {0} on {1}. Key: {2}'.format(channel.id, channel.server.id, image))
	elif isinstance(channel, discord.User):
		log.log_debug('Sending image to user {0}. Key: {1}'.format(channel.id, message))
	send_directly = True
	if not image in images:
		raise NameError('No image with that key found')
	try:
		data = images[image]
		if (send_directly and data[0] != '') or data[1] == '':
				await globals.client.send_file(channel, PlatformSpecific.inst().convert_path('img\\' + data[0]))
				return True
		else:
			await globals.client.send_message(channel, data[1])
			return True
	except discord.errors.Forbidden:
		log.log_warning('Forbidden to speak in channel {0}({1}) on {2}({3})'.format(channel.name, channel.id, channel.server.name, channel.server.id))
	return False

async def send_random_image(channel, image):
	if image not in image_counts:
		raise NameError('No randomizable image with that key found')
	index = random.randint(1, image_counts[image])
	return await send_image(channel, image + str(index))


def sender_has_permission(message, perm):
	if message.server == None or perm == DataPermissions.Permission.none:
		return True
	try:
		return globals.data_permissions.user_has_permission(message.server.id, message.author.id, perm)
	except ValueError:
		return False

def is_steam_user_id(user):
	return is_int(user) and len(str(user)) == 17

async def ping(host):
	""" Returns True if host responds to a single ping request."""
	ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"
	command = "ping " + ping_str + " " + host
	start = time.time()
	proc = subprocess.Popen(command, stdout = subprocess.PIPE)
	while proc.poll() == None:
		await asyncio.sleep(.02) # poll every 20 ms for completion of ping
	end = time.time()
	if proc.returncode != 0:
		return -1 # host unreachable / doesn't reply to ping
	stdout = proc.communicate()[0].decode('utf-8')
	log.log_debug('Received ping reply: ' + stdout)
	ping_time = end - start
	if platform.system().lower() == "windows":
		pattern = re.compile('Average = (?P<time>[0-9]+)ms')
	else:
		pattern = re.compile('rtt min/avg/max/mdev = [0-9]+\\.[0-9]+/(?P<time>[0-9]+)\\.[0-9]+/.+/.+ ms')
	result = pattern.search(stdout)
	if result != None:
		ping_time = int(result.groups('time')[0])
	return ping_time
