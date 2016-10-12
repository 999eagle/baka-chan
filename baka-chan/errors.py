class BakaException(Exception):
	@property
	def text(self):
		if len(self.args) >= 1:
			return self.args[0]
		else:
			return ''

class InvalidConfigException(BakaException):
	pass

class ConfigNotLoadedException(BakaException):
	pass

class InvalidSettingException(BakaException):
	pass