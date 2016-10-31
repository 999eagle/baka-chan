import aiohttp
import asyncio
import json
import os
import os.path
import base64
import configparser
import re

import globals
import log
import platform_specific

class GitHubAPI:
	API_BASE = 'https://api.github.com/'
	API_REPO = API_BASE + 'repos/{repo_name}'
	API_TAGS = API_REPO + '/tags'
	API_TREE = API_REPO + '/git/trees/{tree}'
	API_COMMIT = API_REPO + '/commits/{commit}'
	API_BLOB = API_REPO + '/git/blobs/{blob}'

	def __init__(self, loop = None):
		if self.loop == None:
			self.loop = asyncio.get_event_loop()
			self.own_loop = True
		else:
			self.loop = loop
			self.own_loop = False
		self.headers = { 'Authorization': 'token {0}'.format(globals.config.github_login_token)}
		self.session = aiohttp.ClientSession(loop = loop, headers = self.headers)
		self.path_sep = platform_specific.PlatformSpecific.inst().path_sep

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.close()

	def close(self):
		self.session.close()
		if self.own_loop:
			self.loop.close()

	def _check_path_dir(self, path):
		if not path.endswith(self.path_sep):
			path += self.path_sep
		if not os.path.exists(path):
			os.mkdir(path)
		return path

	async def _download_blob(self, repo_name, blob, destination):
		log.log_debug('GitHubAPI: Get blob {0} from repo {1}'.format(blob, repo_name))
		blob_url = Updater.API_BLOB.format(repo_name = repo_name, blob = blob)
		async with self.session.get(blob_url) as blob_resp:
			log.log_debug('GitHubAPI: Saving blob {0} to {1}'.format(blob, destination))
			# sadly, blobs aren't returned as binary data, but instead wrapped in a json object encoded in base64
			# thus we can't use any streams here
			blob_json = json.loads(await blob_resp.text())
			with open(destination, 'wb') as f:
				f.write(base64.b64decode(blob_json['content']))

	async def _download_tree(self, repo_name, tree, destination):
		destination = self._check_path_dir(destination)
		log.log_debug('GitHubAPI: Get tree {0} from repo {1}'.format(tree, repo_name))
		tree_url = Updater.API_TREE.format(repo_name = repo_name, tree = tree)
		async with self.session.get(tree_url) as tree_resp:
			tree_text = await tree_resp.text()
			log.log_debug('GitHubAPI: Get tree {0} returned {1}'.format(tree, tree_text))
			tree_json = json.loads(tree_text)

		modules = None
		for item in tree_json['tree']:
			item_dest = destination + item['path']
			item_sha = item['sha']
			if item['type'] == 'tree':
				# download subtree
				await self._download_tree(repo_name, item_sha, item_dest)
			elif item['type'] == 'blob':
				# download file blob
				await self._download_blob(repo_name, item_sha, item_dest)
				if item['path'] == '.gitmodules':
					# parse .gitmodules file and save the data for returning
					modules = self._parse_gitmodules(item_dest)
			elif item['type'] == 'commit':
				# write commit sha for submodule into a file, it'll be resolved and downloaded by the caller of _download_tree
				with open(item_dest, 'w') as f:
					f.write(item['sha'])
		return modules

	async def _download_commit(self, repo_name, commit, destination):
		destination = self._check_path_dir(destination)
		log.log_debug('GitHubAPI: Get commit {0} from repo {1}'.format(commit, repo_name))
		commit_url = Updater.API_COMMIT.format(repo_name = repo_name, commit = commit)
		async with self.session.get(commit_url) as commit_resp:
			commit_text = await commit_resp.text()
			log.log_debug('GitHubAPI: Get commit {0} returned {1}'.format(commit, commit_text))
			commit_json = json.loads(commit_text)
		tree_sha = commit_json['commit']['tree']['sha']
		# download the tree
		modules = await self._download_tree(repo_name, tree_sha, destination)
		# download the submodules in that tree
		if modules != None:
			for module in modules:
				module_dest = destination + module['path']
				with open(module_dest, 'r') as f:
					module_commit = f.read()
				os.remove(module_dest)
				log.log_debug('GitHubAPI: Downloading {0}@{1} to {2} for commit {3}'.format(module['repo'], module_commit, module['path'], commit))
				await self._download_commit(module['repo'], module_commit, module_dest)

	async def _download_tag(self, repo_name, tag_name, destination):
		destination = self._check_path_dir(destination)
		log.log_debug('GitHubAPI: Get tags from repo {0}'.format(repo_name))
		tags_url = Updater.API_TAGS.format(repo_name = repo_name)
		async with self.session.get(tags_url) as tags_resp:
			tags_text = await tags_resp.text()
			log.log_debug('GitHubAPI: Get tags returned {0}'.format(tags_text))
			tags_json = json.loads(tags_text)
		for tag in tags_json:
			if tag['name'] == tag_name:
				commit_sha = tag['commit']['sha']
				await self._download_commit(repo_name, commit_sha, destination)
				break

	def _parse_gitmodules(self, path):
		modules = []
		parser = configparser.ConfigParser()
		parser.read(path)
		url_pattern = re.compile(r'https?:\/\/(www\.)?github\.com\/(?P<repo>[A-Za-z0-9]*\/[A-Za-z0-9]*)\.git')
		for sect_name in parser.sections():
			sect = parser[sect_name]
			modules.append({'path': sect['path'], 'repo': url_pattern.search(sect['url']).group('repo')})
		return modules