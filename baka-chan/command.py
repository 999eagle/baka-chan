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
		impl = CommandWrapper(func, self.command_names, **self.kwargs)
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

class MentionArgument:
	def __init__(self, mention):
		self.mention = mention
		self.id = get_id_from_mention(mention)
		if self.mention[2] == '!':
			self.type = 'user'
			self.nickname = True
		elif self.mention[2] == '&':
			self.type = 'role'
		else:
			self.type = 'user'
			self.nickname = False

class CommandWrapper:
	"""Wraps the actual command function call and stores some metadata along with it."""
	def __init__(self, func, command_names, **kwargs):
		self.func = func
		self.command_names = command_names
		self.allow_private = kwargs.get('allow_private', False)
		self.help = kwargs.get('help', None)
		self.usage = kwargs.get('usage', None)
		self.permission = kwargs.get('permission', DataPermissions.Permission.none)

	def parse_arg(self, raw_arg, usage):
		if isinstance(usage, str):
			if usage.startswith('<') and usage.endswith('>'):
				# usage is some argument --> needs to be parsed
				usage = usage[1:-1]
				if usage.startswith('@'):
					# usage is a mention
					if usage == '@user' and is_usermention(raw_arg):
						return (True, MentionArgument(raw_arg))
					elif usage == '@role' and is_rolemention(raw_arg):
						return (True, MentionArgument(raw_arg))
				else:
					split = usage.split(':')
					name = split[0].strip()
					type = split[1].strip()
					if type == 'str':
						return (True, raw_arg)
					elif type == 'int' and is_int(raw_arg):
						return (True, int(raw_arg))
			else:
				# usage is plain text and must match exactly
				if raw_arg == usage:
					return (True, usage)
		elif isinstance(usage, tuple):
			if usage[0] == 'optional':
				parse = self.parse_arg(raw_arg, usage[1])
				if not parse[0]:
					return (True, None)
				else:
					return parse
		return (False, -1)

	async def __call__(self, message, split):
		# split is the split message content, split[0] is the command tag, split[1] is the command and split[2:] are the arguments
		# split[0] was already checked if execution reaches this point
		if split[1] in self.command_names:
			raw_args = split[2:]
			args = []
			index = 0
			can_call = True
			if self.usage != None:
				for argument in self.usage:
					if len(raw_args) <= index:
						can_call = False
						break
					parse = self.parse_arg(raw_args[index], argument)
					if not parse[0]:
						if parse[1] == -1:
							can_call = False
							break
						elif parse[1] == 0:
							continue
					if parse[1] != argument:
						args.append(parse[1])
					index += 1
			await self.func(message, *args)
			return True
		else:
			return False
