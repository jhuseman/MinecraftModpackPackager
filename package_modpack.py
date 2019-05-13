#!/usr/bin/env python

import os
import shutil
import tempfile
import argparse

import subprocess
import json

import file_ops
import translate_wsl_paths

class modpack_packager(object):
	"""packages a Minecraft modpack into the respective client and server zip archives, for easy transfer to another computer"""
	def __init__(self, modpack_dir=None, packages_dir=None, modpack_name=None, modpack_version=None, client_info_fname=None):
		"""initialize all variables needed by the package functions"""
		self.modpack_dir = modpack_dir
		self.packages_dir = packages_dir
		self.modpack_name = modpack_name
		self.modpack_version = modpack_version
		self.client_info_fname = client_info_fname
		if not self.client_info_fname is None:
			print("Loading settings JSON file...")
			self.load_client_info()
		if self.modpack_version is None:
			print("Calculating next version number...")
			#TODO: auto-gen version if not set yet
			raise NotImplementedError("No version number specified, and cannot be auto-calculated!")
		if self.packages_dir is None:
			print("WARNING: Packages directory not set! Creating one in local directory...")
			self.packages_dir = os.path.join(os.curdir, 'packages')
		print("Modpack version number {version}".format(version=self.modpack_version))
	
	def prep(self):
		"""prepare the system for packaging the server and client"""
		print("Calculating path to minecraft instance...")
		self.calculate_initial_paths()
		print("Loading information from modpack instance...")
		self.load_minecraftinstance()
		print("Calculating paths for all files...")
		self.calculate_paths()
		print("Ensuring correct forge version is installed...")
		self.install_forge()
	
	def load_client_info(self):
		"""load in a JSON archive of settings for the installed client, and override preset settings"""
		with open(self.client_info_fname, 'r') as fp:
			client_info = json.load(fp)
		overwrite_keys = [
			'modpack_dir', 
			'packages_dir', 
			'modpack_name', 
			'modpack_version', 
		]
		for key in overwrite_keys:
			if key in client_info:
				if not client_info[key] is None:
					setattr(self, key, client_info[key])
	
	def calculate_initial_paths(self):
		"""calculate a few paths required by load_minecraftinstance"""
		if self.modpack_dir is None:
			raise Exception("No folder is specified for the modpack!")
		
		self.modpack_dir_native = translate_wsl_paths.translate_path_to_native(self.modpack_dir)
		self.packages_dir_native = translate_wsl_paths.translate_path_to_native(self.packages_dir)

		self.minecraftinstance_json_path = os.path.join(self.modpack_dir_native, 'minecraftinstance.json')
	
	def load_minecraftinstance(self):
		"""load data from the modpack's minecraftinstance.json file"""
		with open(self.minecraftinstance_json_path, 'r') as fp:
			self.minecraftinstance = json.load(fp)
		self.minecraftinstance["baseModLoader"]["versionDict"] = json.loads(self.minecraftinstance["baseModLoader"]["versionJson"])
		if self.modpack_name is None:
			self.modpack_name = self.minecraftinstance["name"]
	
	def calculate_paths(self):
		"""calculate all of the paths needed by the package functions"""
		self.config_dir_path = os.path.join(self.modpack_dir_native, 'config')

		# self.temp_dir = os.path.join(os.curdir, 'temp')
		self.temp_dir = os.path.join(tempfile.gettempdir(), 'mc_modpack_package')
		self.temp_version_dir = os.path.join(self.temp_dir, self.modpack_version)
		self.temp_client_dir = os.path.join(self.temp_version_dir, 'client')
		self.temp_server_dir = os.path.join(self.temp_version_dir, 'server')

		self.package_dir = os.path.join(self.packages_dir_native, self.modpack_version)
		self.package_client_dir = os.path.join(self.package_dir, '{name}_client_{version}'.format(name=self.modpack_name, version=self.modpack_version))
		self.package_server_dir = os.path.join(self.package_dir, '{name}_server_{version}'.format(name=self.modpack_name, version=self.modpack_version))
		self.package_client_zip_fname = '{name}_client_{version}.zip'.format(name=self.modpack_name, version=self.modpack_version)
		self.package_server_zip_fname = '{name}_server_{version}.zip'.format(name=self.modpack_name, version=self.modpack_version)
		self.package_client_zip_path = os.path.join(self.package_dir, self.package_client_zip_fname)
		self.package_server_zip_path = os.path.join(self.package_dir, self.package_server_zip_fname)

		self.temp_client_overrides_dir_path = os.path.join(self.temp_client_dir,'overrides')
		self.temp_client_config_dir_path = os.path.join(self.temp_client_overrides_dir_path,'client')
		self.temp_client_manifest_json_path = os.path.join(self.temp_client_dir,'mainfest.json')
		self.temp_client_modlist_html_path = os.path.join(self.temp_client_dir,'modlist.html')

		self.forge_version = self.minecraftinstance["baseModLoader"]["filename"].replace('.jar','').replace('forge-','')
		self.forge_installer_filename = 'forge-{}-installer.jar'.format(self.forge_version)
		self.forge_universal_filename = 'forge-{}-universal.jar'.format(self.forge_version)
		self.forge_installer_path = os.path.join(os.curdir, 'forge_jars', self.forge_installer_filename)
		# self.forge_install_dir_path = os.path.join(os.curdir, 'forge_jars', 'installs', self.forge_version)
		self.forge_install_dir_path = os.path.join(os.path.expanduser('~'), '.mc_forge_installs', 'forge-{}'.format(self.forge_version))
		self.forge_universal_path = os.path.join(self.forge_install_dir_path, self.forge_universal_filename)
		self.forge_installer_url = 'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{forge_version}/forge-{forge_version}-installer.jar'.format(forge_version=self.forge_version)
		self.launcher_wrapper_version = None
		for lib in self.minecraftinstance["baseModLoader"]["versionDict"]["libraries"]:
			if 'name' in lib:
				name = lib['name']
				name_split = name.split(':')
				if name_split[0]=='net.minecraft' and name_split[1]=='launchwrapper':
					self.launcher_wrapper_version = name_split[-1]
		if self.launcher_wrapper_version is None:
			raise Exception("Could not determine launchwrapper version!")
		self.minecraft_version = self.minecraftinstance["baseModLoader"]["minecraftVersion"]
		self.additional_server_files_path = 'additional_server_files'
	
	def install_forge(self):
		"""ensures the forge server version specified in minecraftinstance is installed where we can access it"""
		if not os.path.isfile(self.forge_installer_path):
			print("Downloading installer for forge {}...".format(self.forge_version))
			file_ops.download_file(self.forge_installer_url, self.forge_installer_path)
		if not os.path.isdir(self.forge_install_dir_path):
			os.makedirs(self.forge_install_dir_path)
		if not os.path.isfile(self.forge_universal_path):
			print('Installing forge {forge_version} into "{forge_install_dir_path}"...'.format(forge_version=self.forge_version,forge_install_dir_path=self.forge_install_dir_path))
			subprocess.check_call(['java', '-jar', os.path.abspath(self.forge_installer_path), '--installServer'], cwd=self.forge_install_dir_path)
			print("Forge installation complete!")

	def gen_manifest_json(self):
		"""generate the data for manifest.json in the client package"""
		files_list = []
		for addon in self.minecraftinstance["installedAddons"]:
			files_list.append({
				"projectID": addon["addonID"],
				"fileID": addon["installedFile"]["id"],
				"required": (addon["installedFile"]["FileNameOnDisk"][-4:]=='.jar')
			})
		return {
			"minecraft": {
				"version": self.minecraftinstance["baseModLoader"]["minecraftVersion"],
				"modLoaders": [
					{
						"id": self.minecraftinstance["baseModLoader"]["name"],
						"primary": True
					}
				]
			},
			"manifestType": "minecraftModpack",
			"manifestVersion": 1,
			"name": self.modpack_name,
			"version": self.modpack_version,
			"author": self.minecraftinstance["customAuthor"],
			"files": files_list,
			"overrides": "overrides"
		}

	def gen_modlist_html(self):
		"""generate the contents of modlist.html for the client package"""
		mods_list = ""
		for addon in self.minecraftinstance["installedAddons"]:
			mods_list = mods_list + '<li><a href="https://minecraft.curseforge.com/mc-mods/{id}">{name}</a></li>\r\n'.format(
					id=addon["addonID"], 
					name=addon["installedFile"]["fileName"], #TODO: find better way of representing this information
				)
		return "<ul>\r\n{mods_list}</ul>\r\n".format(mods_list=mods_list)
	
	def package_client(self):
		"""create the package directory and zip file for the client"""
		if os.path.isdir(self.temp_client_dir):
			print("Removing previous client temporary directory (Possibly from previous failed build?)...")
			shutil.rmtree(self.temp_client_dir)
		print("Creating client temporary directory...")
		os.makedirs(self.temp_client_dir)
		print("Creating client overrides directory...")
		os.makedirs(self.temp_client_overrides_dir_path)
		print("Copying client config directory...")
		file_ops.copy_directory(self.config_dir_path, self.temp_client_config_dir_path)
		print("Writing client manifest.json...")
		with open(self.temp_client_manifest_json_path, 'w') as fp:
			json.dump(self.gen_manifest_json(),fp, indent=2)
		print("Writing client modlist.html...")
		with open(self.temp_client_modlist_html_path, 'wb') as fp:
			fp.write(self.gen_modlist_html().encode('utf-8'))
		if os.path.isdir(self.package_client_dir):
			print("Removing previous client package directory (Possibly from previous failed build?)...")
			shutil.rmtree(self.package_client_dir)
		print('Copying client package into packages directory "{}"...'.format(self.package_client_dir))
		file_ops.copy_directory(self.temp_client_dir, self.package_client_dir)
		print('Compressing client package to "{}"...'.format(self.package_client_zip_path))
		file_ops.create_zip(self.package_client_dir, self.package_client_zip_path)
		print("Client package complete!")
	
	def package_server(self):
		"""create the package directory and zip file for the server"""
		if os.path.isdir(self.temp_server_dir):
			print("Removing previous server temporary directory (Possibly from previous failed build?)...")
			shutil.rmtree(self.temp_server_dir)
		print("Creating server temporary directory...")
		os.makedirs(self.temp_server_dir)
		print("Copying mod files from modpack instance...")
		file_ops.copy_directory(self.modpack_dir_native, self.temp_server_dir, 
			exclude=[
				".curseclient",
				"minecraftinstance.json",
				os.path.join("mods","mod_list.json"),
			]
		)
		remove_mods_json_path = 'remove_mods.json'
		if os.path.isfile(remove_mods_json_path):
			print('Disabling troublesome mods listed in "{}"...'.format(remove_mods_json_path))
			with open(remove_mods_json_path, 'r') as fp:
				remove_mods = json.load(fp)
			for mod in remove_mods:
				mod_path = os.path.join(self.temp_server_dir, "mods", "{}.jar".format(mod))
				mod_disabled_path = mod_path + ".disabled"
				if os.path.isfile(mod_path):
					os.rename(mod_path, mod_disabled_path)
		print('Copying forge installation from "{forge_install_dir_path}" into "{temp_server_dir}"...'.format(forge_install_dir_path = self.forge_install_dir_path, temp_server_dir = self.temp_server_dir))
		file_ops.copy_directory(self.forge_install_dir_path, self.temp_server_dir, 
			exclude=[
				os.path.join('libraries','net','minecraft','launchwrapper',self.launcher_wrapper_version,'launchwrapper-{}.jar'.format(self.launcher_wrapper_version)), 
				'minecraft_server.{}.jar'.format(self.minecraft_version), 
			]
		)
		with open(os.path.join(self.temp_server_dir,'libraries','net','minecraft','launchwrapper',self.launcher_wrapper_version,'KEEP_FOLDER'), 'w') as _:
			pass # Just creating this as a blank file

		print('Copying additional files into  "{}"...'.format(self.temp_server_dir))
		file_ops.copy_directory(self.additional_server_files_path, self.temp_server_dir)

		print('Modifying settings files to include correct versions...')
		settings_files = [
			'settings.bat', 
			'settings.sh', 
		]
		settings_keys = {
			'{{[FORGEJAR]}}':self.forge_universal_filename, 
			'{{[LAUNCHERVER]}}':self.launcher_wrapper_version, 
			'{{[MCVER]}}':self.minecraft_version, 
		}
		for fname in settings_files:
			file_ops.replace_in_file(os.path.join(self.temp_server_dir, fname), settings_keys)
		
		if os.path.isdir(self.package_server_dir):
			print("Removing previous server package directory (Possibly from previous failed build?)...")
			shutil.rmtree(self.package_server_dir)
		print('Copying server package into packages directory "{}"...'.format(self.package_server_dir))
		file_ops.copy_directory(self.temp_server_dir, self.package_server_dir)
		print('Compressing server package to "{}"...'.format(self.package_server_zip_path))
		file_ops.create_zip(self.package_server_dir, self.package_server_zip_path)
		print("Server package complete!")
	
	def cleanup(self):
		"""deletes the temporary files used during creation of packages"""
		print('Deleting temporary directory "{}"...'.format(self.temp_version_dir))
		shutil.rmtree(self.temp_version_dir)
		print('Temporary directory cleared!')

def run(**kwargs):
	packager = modpack_packager(**kwargs)
	packager.prep()
	packager.package_client()
	packager.package_server()
	packager.cleanup()

if __name__=='__main__':
	parser = argparse.ArgumentParser(description='TEST_DESCRIPTION')
	parser.add_argument('-j', '--client_info_fname', dest='client_info_fname', default=argparse.SUPPRESS, help='Filename of a JSON file containing settings.  For details, see example file "client_loc_info.json".  Values specified in the JSON file override those specified by command-line.')
	parser.add_argument('-d', '--modpack_dir',       dest='modpack_dir',       default=argparse.SUPPRESS, help='Path to the directory from which the modpack files should be copied.  On systems running Windows Subsystem for Linux (WSL), supports both WSL paths (/mnt/c/...) and Windows paths (C:\...).')
	parser.add_argument('-p', '--packages_dir',      dest='packages_dir',      default=argparse.SUPPRESS, help='Path to the directory in which the finished modpack packages should be created.  On systems running Windows Subsystem for Linux (WSL), supports both WSL paths (/mnt/c/...) and Windows paths (C:\...).')
	parser.add_argument('-n', '--modpack_name',      dest='modpack_name',      default=argparse.SUPPRESS, help='Name of the modpack used as a prefix for filenames and listed in client "manifest.json".  If not specified (here or in JSON file), defaults to the name specified in "minecraftinstance.json" in the modpack directory.')
	parser.add_argument('-v', '--modpack_version',   dest='modpack_version',   default=argparse.SUPPRESS, help='Version number of the modpack used as a suffix for filenames and listed in client "manifest.json".  If not specified (here or in JSON file), an error is encountered. #TODO: Implement auto-incrementing version numbers!') #TODO
	args = parser.parse_args()
	init_settings = args.__dict__
	if init_settings=={}:
		init_settings = {
			'modpack_dir':None, 
			'packages_dir':None, 
			'modpack_name':None, 
			'modpack_version':None, 
			'client_info_fname':'client_loc_info.json', 
		}
	run(**init_settings)