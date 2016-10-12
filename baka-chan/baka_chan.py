#
# Baka-chan v0.4
# main entry point
#

import os
import traceback
import discord, discord.opus
import asyncio
import datetime

import globals
import log
import config
from errors import *
from platform_specific import PlatformSpecific

def sigterm_received():
	log.log_debug('Received SIGTERM')
	if globals.client.is_logged_in:
		asyncio.ensure_future(globals.client.logout())

def cleanup():
	# TODO: save/clean stuff if needed
	# THIS MUST NOT RAISE ANY EXCEPTIONS!
	pass

def main():
	log.log_info('Baka-chan {0} started'.format(globals.version_str))
	# load configuration and set up logging according to that
	globals.init()
	globals.config.load()
	log.set_up_logging(globals.config.log_level)
	log.log_debug('Configuration loaded')

	# Only set handler for SIGTERM on linux, will do nothing useful on windows
	if os.name != 'nt':
		import signal
		signal.signal(signal.SIGTERM, sigterm_received)
		log.log_debug('SIGTERM handler set')

	# Load libopus for voice functionality
	discord.opus.load_opus(PlatformSpecific.inst().opus_path)
	log.log_debug('libopus loaded')

	# import the file containing event hooks
	import client_events
	log.log_debug('Discord events hooked')

	# needed to wake up the event loop periodically
	# without this the KeyboardInterrupt would not arrive
	async def wakeup():
		while True:
			await asyncio.sleep(1)
	asyncio.ensure_future(wakeup())
	log.log_debug('Async wakeup running')

	# load APIs
	globals.api_steam.load_api()
	log.log_debug('Steam API loaded')

	print('Press Ctrl+C to exit')
	globals.start_time = datetime.datetime.now()
	# now run the discord client
	loop = globals.client.loop
	try:
		loop.run_until_complete(globals.client.start(globals.config.discord_token))
	except KeyboardInterrupt:
		# Ctrl+C pressed: gracefully exit by logging out
		loop.run_until_complete(globals.client.logout())
	except discord.LoginFailure:
		log.log_error('Couldn\'t log in to discord')
	finally:
		# gather all async tasks and cancel them
		pending = asyncio.Task.all_tasks()
		gathered = asyncio.gather(*pending)
		try:
			gathered.cancel()
			loop.run_until_complete(gathered)
			gathered.exception()
		except:
			pass
		# close the event loop in the end
		loop.close()

	cleanup()
	log.log_info('Baka-chan {0} stopping'.format(globals.version_str))

if __name__ == '__main__':
	# Absolute first thing to do: set up default logging (log_level: INFO)
	log.set_up_logging()
	try:
		# Now run the main
		main()
	except:
		# Any uncaught exceptions will be logged
		text = 'A critical error was encountered and the bot couldn\'t recover.\nDetails:\n'
		text += traceback.format_exc()
		log.log_error(text)
		cleanup()