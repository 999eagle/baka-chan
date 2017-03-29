import shutil
import traceback
import sys
import os
import subprocess

import globals
from github_api import GitHubAPI
from util import *
from errors import *

class Updater:
	def __init__(self, loop = None):
		self.github = GitHubAPI(loop)
		self.loop = self.github.loop

	def close(self):
		self.github.close()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.close()

	async def update_from_github_repo(self, status_channel, tag, auto_restart):
		log.log_info('Updating from GitHub repo. Commit/Tag: {0}'.format(tag))
		await send_message(status_channel, 'Updating...')
		try:
			try:
				await self.github.download_tag(globals.config.github_update_repo, tag, os.path.realpath(os.path.abspath('update')))
			except GitHubAPIException:
				log.log_info('Couldn\'t download tag, trying to download commit')
				await self.github.download_commit(globals.config.github_update_repo, tag, os.path.realpath(os.path.abspath('update')))
			log.log_info('Content from GitHub repo downloaded')
			await send_message(status_channel, 'Content downloaded')
			python_exec = os.path.abspath(sys.executable)
			log.log_info('Installing required packages for update')
			pip_proc = subprocess.Popen([python_exec, '-m', 'pip', 'install', '--quiet', '-r', os.path.realpath(os.path.abspath(os.path.join('update','baka-chan','requirements.txt')))])
			while pip_proc.returncode == None:
				pip_proc.poll()
				await asyncio.sleep(0.2)
			if pip_proc.returncode != 0:
				raise Exception('Installing requirements with pip failed. Returncode: {0}'.format(pip_proc.returncode))
			log.log_info('Required packages installed')
			await send_message(status_channel, 'Required packages installed')
			dest_path = os.path.realpath(os.path.abspath('.'))
			src_path = os.path.realpath(os.path.abspath(os.path.join('update', 'baka-chan')))
			log.log_info('Copying files')
			self._copy_files(src_path, dest_path)
			if auto_restart:
				log.log_info('Files copied, Restarting...')
				await send_message(status_channel, 'Files copied, restarting...')
				globals.restart_on_exit = True
				await globals.client.logout()
			else:
				log.log_info('Files copied, please restart manually')
				await send_message(status_channel, 'Files copied, please restart manually')
		except:
			text = traceback.format_exc()
			log.log_error(text)
			await send_message(status_channel, 'Failed')
		finally:
			shutil.rmtree('update')

	def _copy_files(self, src, dest):
		for f in os.listdir(src):
			path = os.path.join(src, f)
			if os.path.isfile(path):
				shutil.copy(path, dest)
		for f in os.listdir(src):
			path = os.path.join(src, f)
			if os.path.isdir(path):
				self._copy_files(path, os.path.join(dest, f))
