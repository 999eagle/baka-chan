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
from errors import *

class GitHubAPI:
	API_BASE = 'https://api.github.com/'
	API_REPO = API_BASE + 'repos/{repo_name}'
	API_TAGS = API_REPO + '/tags'
	API_TREE = API_REPO + '/git/trees/{tree}'
	API_COMMIT = API_REPO + '/commits/{commit}'
	API_BLOB = API_REPO + '/git/blobs/{blob}'
	API_ISSUES = API_REPO + '/issues'

	def __init__(self, loop = None):
		if loop == None:
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

	async def _download_blob(self, repo_name, blob, file_mode, destination):
		log.log_debug('GitHubAPI: Get blob {0} from repo {1}'.format(blob, repo_name))
		blob_url = GitHubAPI.API_BLOB.format(repo_name = repo_name, blob = blob)
		async with self.session.get(blob_url) as blob_resp:
			blob_text = await blob_resp.text()
			log.log_debug('GitHubAPI: Saving blob {0} to {1} with mode {2}'.format(blob, destination, file_mode[-3:]))
			# sadly, blobs aren't returned as binary data, but instead wrapped in a json object encoded in base64
			# thus we can't use any streams here
			blob_json = json.loads(blob_text)
		flags = os.O_WRONLY | os.O_CREAT
		if os.name == 'nt':
			flags |= os.O_BINARY
		mode = int(file_mode[-3:], base = 8)
		with os.fdopen(os.open(destination, flags, mode), 'wb') as f:
			f.write(base64.b64decode(blob_json['content']))

	async def download_tree(self, repo_name, tree, destination):
		destination = self._check_path_dir(destination)
		log.log_debug('GitHubAPI: Get tree {0} from repo {1}'.format(tree, repo_name))
		tree_url = GitHubAPI.API_TREE.format(repo_name = repo_name, tree = tree)
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
				await self.download_tree(repo_name, item_sha, item_dest)
			elif item['type'] == 'blob':
				# download file blob
				await self._download_blob(repo_name, item_sha, item['mode'], item_dest)
				if item['path'] == '.gitmodules':
					# parse .gitmodules file and save the data for returning
					modules = self._parse_gitmodules(item_dest)
			elif item['type'] == 'commit':
				# write commit sha for submodule into a file, it'll be resolved and downloaded by the caller of _download_tree
				with open(item_dest, 'w') as f:
					f.write(item['sha'])
		return modules

	async def download_commit(self, repo_name, commit, destination):
		destination = self._check_path_dir(destination)
		log.log_debug('GitHubAPI: Get commit {0} from repo {1}'.format(commit, repo_name))
		commit_url = GitHubAPI.API_COMMIT.format(repo_name = repo_name, commit = commit)
		async with self.session.get(commit_url) as commit_resp:
			commit_text = await commit_resp.text()
			log.log_debug('GitHubAPI: Get commit {0} returned {1}'.format(commit, commit_text))
			commit_json = json.loads(commit_text)
		if 'message' in commit_json:
			raise GitHubAPIException('Commit not found: {0}'.format(commit_json['message']))
		elif 'commit' not in commit_json:
			raise GitHubAPIException('Commit not found')
		tree_sha = commit_json['commit']['tree']['sha']
		# download the tree
		modules = await self.download_tree(repo_name, tree_sha, destination)
		# download the submodules in that tree
		if modules != None:
			for module in modules:
				module_dest = destination + module['path']
				with open(module_dest, 'r') as f:
					module_commit = f.read()
				os.remove(module_dest)
				log.log_debug('GitHubAPI: Downloading {0}@{1} to {2} for commit {3}'.format(module['repo'], module_commit, module['path'], commit))
				await self.download_commit(module['repo'], module_commit, module_dest)

	async def download_tag(self, repo_name, tag_name, destination):
		destination = self._check_path_dir(destination)
		log.log_debug('GitHubAPI: Get tags from repo {0}'.format(repo_name))
		tags_url = GitHubAPI.API_TAGS.format(repo_name = repo_name)
		async with self.session.get(tags_url) as tags_resp:
			tags_text = await tags_resp.text()
			log.log_debug('GitHubAPI: Get tags returned {0}'.format(tags_text))
			tags_json = json.loads(tags_text)
		tag = [x for x in tags_json if x['name'] == tag_name]
		if len(tag) == 0:
			raise GitHubAPIException('Tag not found')
		tag = tag[0]
		commit_sha = tag['commit']['sha']
		await self.download_commit(repo_name, commit_sha, destination)

	def _parse_gitmodules(self, path):
		modules = []
		parser = configparser.ConfigParser()
		parser.read(path)
		url_pattern = re.compile(r'https?:\/\/(www\.)?github\.com\/(?P<repo>[A-Za-z0-9]*\/[A-Za-z0-9]*)\.git')
		for sect_name in parser.sections():
			sect = parser[sect_name]
			modules.append({'path': sect['path'], 'repo': url_pattern.search(sect['url']).group('repo')})
		return modules

	async def create_issue(self, repo_name, title, body, labels = None):
		log.log_debug('GitHubAPI: Creating new issue in repo {0}'.format(repo_name))
		issue_url = GitHubAPI.API_ISSUES.format(repo_name = repo_name)
		issue_post_data = { 'title': title, 'body': body }
		if labels != None:
			issue_post_data['labels'] = labels
		async with self.session.post(issue_url, data = json.dumps(issue_post_data)) as issue_post_resp:
			issue_text = await issue_post_resp.text()
			log.log_debug('GitHubAPI: Create issue returned {0}'.format(issue_text))
			issue_json = json.loads(issue_text)
		return issue_json['html_url']
