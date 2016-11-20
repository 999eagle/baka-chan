import logging, logging.handlers
import os, os.path
import sys

from platform_specific import PlatformSpecific
import globals

def set_up_logging(log_level=logging.INFO):
	plat = PlatformSpecific.inst()
	log_path = plat.convert_path('logs\\')
	if not os.path.isdir(log_path):
		os.mkdir(log_path)

	if globals.running_in_foreground or True:
		print_handler = logging.StreamHandler(sys.stdout)
		print_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
	else:
		print_handler = None

	# set up discord logger
	logger = logging.getLogger('discord')
	logger.setLevel(logging.DEBUG)
	logger.handlers.clear()
	handler = logging.handlers.TimedRotatingFileHandler(log_path + 'discord.log', when='midnight', backupCount=7, encoding='utf8')
	handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
	handler.setLevel(log_level)
	logger.addHandler(handler)
	if print_handler != None:
		logger.addHandler(print_handler)

	# set up baka logger
	logger = logging.getLogger('baka')
	logger.setLevel(logging.DEBUG)
	logger.handlers.clear()
	handler = logging.handlers.TimedRotatingFileHandler(log_path + 'baka.log', when='midnight', backupCount=7, encoding='utf8')
	handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
	handler.setLevel(log_level)
	logger.addHandler(handler)
	if print_handler != None:
		logger.addHandler(print_handler)

def log(message, level = logging.INFO):
	log = logging.getLogger('baka')
	log.log(level, message)

def log_debug(message):
	log(message, logging.DEBUG)

def log_info(message):
	log(message, logging.INFO)

def log_warning(message):
	log(message, logging.WARNING)

def log_error(message):
	log(message, logging.ERROR)

def shutdown():
	logging.shutdown()
