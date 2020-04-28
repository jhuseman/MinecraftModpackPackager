#!/usr/bin/env python3

import os
import shutil

import ServerStart
import LogHandler
import file_ops

class docker_starter(object):
	def __init__(self):
		self.log_handler = LogHandler.log_handler()
	
	def prep_fs(self):
		def link_file(src, dest):
			print('"{src}" -> "{dest}"'.format(src=src,dest=dest))
			if os.path.exists(dest):
				if os.path.isdir(dest):
					shutil.rmtree(dest)
				else:
					os.remove(dest)
			os.symlink(os.path.abspath(src), os.path.abspath(dest))
		
		link_contents = [('/mc','.')]
		for src,dest in link_contents:
			if os.path.exists(src):
				if os.path.isdir(src):
					print('Linking files in "{src}" to "{dest}"...'.format(src=src,dest=dest))
					for fn in os.listdir(src):
						link_file(os.path.join(src,fn), os.path.join(dest,fn))
				else:
					print('Linking file "{src}" to "{dest}"...'.format(src=src,dest=dest))
					link_file(src, dest)
	
	def post_run(self):
		backup_target_envvar = 'backup_target'
		backup_files_envvar = 'backup_files'
		backup_target = os.getenv(backup_target_envvar)
		backup_files_env = os.getenv(backup_files_envvar)
		if backup_target is not None:
			print('Backing up files to "{backup_target}"...'.format(backup_target=backup_target))
			if backup_files_env is None:
				backup_files = [
					'eula.txt',
					'world',
					'journeymap',
					'config',
					'server-icon.png',
					'server.properties',
					'usercache.json',
					'usernamecache.json',
					'whitelist.json',
					'banned-players.json',
					'banned-ips.json',
				]
			else:
				backup_files = backup_files_env.split(';')
			if not os.path.isdir(backup_target):
				if os.path.exists(backup_target):
					return
				os.makedirs(backup_target)
			for fname in backup_files:
				src=fname
				if os.path.isabs(fname):
					dest=os.path.join(backup_target,os.curdir+fname)
				else:
					dest=os.path.join(backup_target,fname)
				if os.path.exists(src):
					if os.path.isdir(src):
						print('Backing up files in "{src}" to "{dest}"...'.format(src=src,dest=dest))
						file_ops.copy_directory(src, dest)
					else:
						print('Backing up file "{src}" to "{dest}"...'.format(src=src,dest=dest))
						file_ops.copy_file(src, dest)
	
	def run_game(self):
		ServerStart.main(log_handler=self.log_handler)
	
	def run(self):
		self.prep_fs()
		self.run_game()
		self.post_run()

if __name__=="__main__":
	docker_starter().run()
