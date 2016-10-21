from data import DataPermissions
from util import *
from errors import *

all_commands = []

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

	@classmethod
	def get_help(cls, req_message):
		text = ''
		for c in all_commands:
			if c.help != None and sender_has_permission(req_message, c.permission):
				text += '`{0}`: {1}\n'.format(c.full_usage(), c.help)
		return text

class StaticResponse:
	"""Decorator to create a bot-command that will always return the same, static response."""
	def __init__(self, *args, **kwargs):
		self.type = kwargs.get('type','image')
		self.response = args[0]
	def __call__(self, func):
		if self.type == 'image':
			async def wrapper(message, *_):
				await send_image(message.channel, self.response)
		else:
			async def wrapper(message, *_):
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

class ParseResult:
	def __init__(self, success = True, matched_arg = True, result = None):
		self.success = success
		self.matched_arg = matched_arg
		self.result = result

class CommandWrapper:
	"""Wraps the actual command function call and stores some metadata along with it."""
	def __init__(self, func, command_names, **kwargs):
		self.func = func
		self.command_names = command_names
		self.allow_private = kwargs.get('allow_private', False)
		self.help = kwargs.get('help', None)
		self.usage = kwargs.get('usage', None)
		self.permission = kwargs.get('permission', DataPermissions.Permission.none)

	def full_usage(self):
		usage_str = ''
		if self.usage != None:
			for argument in self.usage:
				usage_str += ' ' + self.generate_usage_str(argument)
		return '{0}{1}{2}'.format(globals.config.cmd_tag, self.command_names[0], usage_str)

	def parse_arg(self, raw_arg, usage):
		if isinstance(usage, str):
			if usage.startswith('<') and usage.endswith('>'):
				# usage is some argument --> needs to be parsed
				usage = usage[1:-1]
				if usage.startswith('@'):
					# usage is a mention
					if usage == '@user' and is_usermention(raw_arg):
						return ParseResult(result = MentionArgument(raw_arg))
					elif usage == '@role' and is_rolemention(raw_arg):
						return ParseResult(result = MentionArgument(raw_arg))
				else:
					split = usage.split(':')
					name = split[0].strip()
					type = split[1].strip()
					if type == 'str':
						return ParseResult(result = raw_arg)
					elif type == 'int' and is_int(raw_arg):
						return ParseResult(result = int(raw_arg))
					elif type == 'float' and is_float(raw_arg):
						return ParseResult(result = float(raw_arg))
			else:
				# usage is plain text and must match exactly
				if raw_arg == usage:
					return ParseResult()
		elif isinstance(usage, tuple):
			if usage[0] == 'optional':
				parse = self.parse_arg(raw_arg, usage[1])
				if not parse.success:
					return ParseResult(matched_arg = False)
				else:
					if parse.result == None:
						parse.result = True
					return parse
			elif usage[0] == 'oneof':
				list = usage[1:]
				for arg in list:
					parse = self.parse_arg(raw_arg, arg)
					if parse.success:
						if parse.result == None:
							parse.result = arg
						return parse
		return ParseResult(success = False)

	def generate_usage_str(self, usage):
		if isinstance(usage, str):
			if usage.startswith('<') and usage.endswith('>'):
				# usage is some argument --> needs to be parsed
				usage = usage[1:-1]
				if usage.startswith('@'):
					return '<' + usage + '>'
				else:
					split = usage.split(':')
					name = split[0].strip()
					type = split[1].strip()
					return '<' + name + '>'
			elif usage.startswith('*'):
				# usage is rest of arguments
				return usage[1:]
			else:
				# usage is plain text and must match exactly
				return usage
		elif isinstance(usage, tuple):
			if usage[0] == 'optional':
				return '[' + self.generate_usage_str(usage[1]) + ']'
			elif usage[0] == 'oneof':
				return '(' + ' | '.join([self.generate_usage_str(x) for x in usage[1:]]) + ')'

	async def __call__(self, message, split):
		# split is the split message content, split[0] is the command tag, split[1] is the command and split[2:] are the arguments
		# split[0] was already checked if execution reaches this point
		if split[1] not in self.command_names:
			return False

		raw_args = split[2:]
		parsed_args = []
		index = 0
		try:
			if self.usage != None:
				# match arguments with the usage and parse them
				for argument in self.usage:
					is_optional = False
					if isinstance(argument, tuple) and argument[0] == 'optional':
						is_optional = True
					if isinstance(argument, str) and argument.startswith('*'):
						for a in raw_args[index:]:
							parsed_args.append(a)
						index = len(raw_args)
						break
					if len(raw_args) <= index:
						if is_optional:
							raw_arg = ''
						else:
							raise ArgumentParseException()
					else:
						raw_arg = raw_args[index]
					parse = self.parse_arg(raw_arg, argument)
					if not parse.success:
						raise ArgumentParseException()
					if (parse.matched_arg and parse.result != None) or not parse.matched_arg:
							parsed_args.append(parse.result)
					if parse.matched_arg:
						index += 1
			if index < len(raw_args):
				raise ArgumentParseException()
			if sender_has_permission(message, self.permission):
				await self.func(message, *parsed_args)
			else:
				await send_message(message.channel, globals.message_no_permission)
			return True
		except ArgumentParseException:
			available_commands_same_name = [c for c in all_commands if split[1] in c.command_names and sender_has_permission(message, c.permission)]
			if len(available_commands_same_name) > available_commands_same_name.index(self) + 1:
				return False
			text = 'Usage:'
			for c in available_commands_same_name:
				if c.help == None:
					continue
				text += '\n`{0}`'.format(c.full_usage())
			await send_message(message.channel, text)
			return True
