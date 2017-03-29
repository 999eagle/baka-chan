import aiohttp
import asyncio

import globals

class WolframAlphaAPI:
	API_SHORT_ANSWERS = 'https://api.wolframalpha.com/v1/result'

	def __init__(self, app_id, loop = None):
		self.app_id = app_id
		if loop == None:
			self.loop = asyncio.get_event_loop()
			self.own_loop = True
		else:
			self.loop = loop
			self.own_loop = False
		self.session = aiohttp.ClientSession(loop = loop)
	def __enter__(self):
		return self
	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.close()

	def close(self):
		self.session.close()
		if self.own_loop:
			self.loop.close()

	async def short_answer(self, input):
		async with self.session.get(WolframAlphaAPI.API_SHORT_ANSWERS, params = { 'appid': self.app_id, 'input': input }) as response:
			return await response.text()
