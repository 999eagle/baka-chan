from data import DataPermissions
from util import *

all_commands = []
help = []

class Helptext:
	"""Decorator to add a helptext to a command. May only be applied """
	def __init__(self, *args, **kwargs):
		self.perm = kwargs.get('permission',DataPermissions.Permission.none)
		self.before_text = kwargs.get('before_text')
		self.after_text = kwargs.get('after_text')
		self.text = args[0]
		if len(args) > 1:
			self.command = args[1]
		else:
			self.command = ''

	def __call__(self, func):
		if isinstance(func, CommandWrapper):
			cmd = func.command_names[0]
			if self.command != '':
				cmd += ' ' + self.command
			self.command = cmd
			help.append(self)
		return func

	@classmethod
	def get_help(cls, req_message):
		text = ''
		for h in help:
			if sender_has_permission(req_message, h.perm):
				if h.before_text != None:
					text += h.before_text + '\n'
				text += '`{0}`: {1}\n'.format(h.command, h.text)
				if h.after_text != None:
					text += h.after_text + '\n'
		return text

class Command:
	"""Decorator to mark a function as bot command."""
	def __init__(self, *args, **kwargs):
		self.command_names = args
		self.kwargs = kwargs

	def __call__(self, func):

		async def wrapper(message, split):
			if split[1] in self.command_names:
				await func(message, split[2:])
				return True
			else:
				return False
		impl = CommandWrapper(wrapper, self.command_names, **self.kwargs)
		all_commands.append(impl)
		return impl

	@classmethod
	async def execute(cls, message, split, **kwargs):
		private = kwargs.get('private', False)
		for c in all_commands:
			if not private or c.allow_private:
				result = await c(message, split)
				if result:
					return True
		return False

class StaticResponse:
	"""Decorator to create a bot-command that will always return the same, static response."""
	def __init__(self, *args, **kwargs):
		self.type = kwargs.get('type','image')
		self.response = args[0]
	def __call__(self, func):
		if self.type == 'image':
			async def wrapper(message, args):
				await send_image(message.channel, self.response)
		else:
			async def wrapper(message, args):
				await send_message(message.channel, self.response)
		return wrapper

class CommandWrapper:
	"""Wraps the actual command function call and stores some metadata along with it."""
	def __init__(self, func, command_names, **kwargs):
		self.func = func
		self.command_names = command_names
		self.allow_private = kwargs.get('allow_private', False)

	def __call__(self, message, split):
		return self.func(message, split)
