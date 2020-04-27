#!/usr/bin/env python3

import os

import file_ops
from settings import server_settings

def get_eula_agreed(run_dir=os.path.dirname(os.path.realpath(__file__))):
	eula_path = os.path.join(run_dir,'eula.txt')
	if os.path.isfile(eula_path):
		with open(eula_path, 'r') as fp:
			contents = fp.read()
		if 'eula=false' in contents.lower():
			return False
		elif 'eula=true' in contents.lower():
			return True
	return False

launchwrapper_path = os.path.join('libraries',server_settings.launchwrapper)

def check_files(run_dir=os.path.dirname(os.path.realpath(__file__))):
	if not os.path.isfile(os.path.join(run_dir,server_settings.jarfile)):
		return False
	if not os.path.isfile(os.path.join(run_dir,launchwrapper_path)):
		return False
	return True

def dl_files(run_dir=os.path.dirname(os.path.realpath(__file__))):
	file_ops.download_file('https://s3.amazonaws.com/Minecraft.Download/versions/{mcver}/{jarfile}'.format(mcver=server_settings.mcver, jarfile=server_settings.jarfile), os.path.join(run_dir,server_settings.jarfile))
	file_ops.download_file('https://libraries.minecraft.net/{}'.format(server_settings.launchwrapper), os.path.join(run_dir,launchwrapper_path))

def check_eula(run_dir=os.path.dirname(os.path.realpath(__file__))):
	def prompt_eula():
		accept_vals = ['yes','true']
		env_var_name = 'minecraft_agree_eula'
		if os.getenv(env_var_name) is not None:
			if os.getenv(env_var_name) in accept_vals:
				return True
		return input('Type "yes" to indicate your agreement to Minecraft\'s EULA (https://account.mojang.com/documents/minecraft_eula), or press Ctrl+C to exit:\n').lower() in accept_vals
	# if eula.txt is missing or not true, prompt for agreement
	while not get_eula_agreed(run_dir=run_dir):
		if prompt_eula():
			with open(os.path.join(run_dir,'eula.txt'), 'w') as fp:
				fp.write('eula=true')


if __name__=="__main__":
	if not check_files():
		dl_files()
	check_eula()