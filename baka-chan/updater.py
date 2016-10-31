import globals
from github_api import GitHubAPI

class Updater:
	def __init__(self, loop = None):
		self.github = GitHubAPI(loop)

	def close(self):
		self.github.close()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.close()

	async def update_from_github_repo(self, tag):
		await self.github._download_tag(globals.config.github_repo, tag, 'update')
