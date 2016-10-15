import platform
import sys
import os.path

static_instance = None

class PlatformSpecific(object):
	def __init__(self):
		if platform.system() == 'Windows':
			self.path_sep = '\\'
			if sys.maxsize > 2 ** 32:
				self.opus_path = 'bin\\libopus-0.x64.dll'
			else:
				self.opus_path = 'bin\\libopus-0.x86.dll'
		else:
			self.path_sep = '/'
			self.opus_path = 'libopus.so.0'

		self.base_path = os.path.dirname(os.path.realpath(__file__))
		if not self.base_path.endswith(self.path_sep):
			self.base_path += self.path_sep

		static_instance = self

	@classmethod
	def inst(cls):
		if static_instance == None:
			return PlatformSpecific()
		else:
			return static_instance

	def convert_path(self, path):
		path_seps = '/\\'
		p = path
		for s in path_seps:
			if s == self.path_sep:
				continue
			p = p.replace(s, self.path_sep)
		if not os.path.isabs(p):
			p = self.base_path + p
		return p
