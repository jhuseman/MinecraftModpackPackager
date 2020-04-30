#!/usr/bin/env python

import os
import shutil
import tempfile
import argparse

import subprocess
import json

from MinecraftModpackPackager import file_ops
from MinecraftModpackPackager import translate_wsl_paths

class modpack_packager(object):
	"""packages a Minecraft modpack into the respective client and server zip archives, for easy transfer to another computer"""
	def __init__(self, 
			modpack_dir=None, 
			packages_dir=None, 
			additional_server_files_dir=os.path.join(os.path.dirname(__file__),'additional_server_files'), 
			modpack_name=None, 
			docker_image_name=None,
			modpack_version=None, 
			remove_server_mods_fname=os.path.join(os.path.dirname(__file__),'remove_server_mods.json'), 
			client_info_fname=os.path.join(os.path.dirname(__file__),'client_loc_info.json'), 
		):
		"""initialize all variables needed by the package functions"""
		self.modpack_dir = modpack_dir
		self.packages_dir = packages_dir
		self.additional_server_files_dir = additional_server_files_dir
		self.modpack_name = modpack_name
		self.docker_image_name = docker_image_name
		self.modpack_version = modpack_version
		self.remove_server_mods_fname = remove_server_mods_fname
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
		if not os.path.isfile(self.client_info_fname):
			print('WARNING: Client info file "{}" does not exist')
		else:
			with open(self.client_info_fname, 'r') as fp:
				client_info = json.load(fp)
			overwrite_keys = [
				'additional_server_files_dir', 
				'remove_server_mods_fname', 
				'modpack_dir', 
				'packages_dir', 
				'modpack_name', 
				'docker_image_name', 
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
		self.additional_server_files_dir_native = translate_wsl_paths.translate_path_to_native(self.additional_server_files_dir)

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
		self.temp_client_config_dir_path = os.path.join(self.temp_client_overrides_dir_path,'config')
		self.temp_client_manifest_json_path = os.path.join(self.temp_client_dir,'manifest.json')
		self.temp_client_modlist_html_path = os.path.join(self.temp_client_dir,'modlist.html')

		self.forge_version = self.minecraftinstance["baseModLoader"]["filename"].replace('.jar','').replace('forge-','')
		self.forge_installer_filename = 'forge-{}-installer.jar'.format(self.forge_version)
		if self.forge_version.startswith('1.12.2') and int(self.forge_version[-4:])<=2838:
			self.forge_universal_filename = 'forge-{}-universal.jar'.format(self.forge_version)
		else:
			self.forge_universal_filename = 'forge-{}.jar'.format(self.forge_version)
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
	
	def install_forge(self):
		"""ensures the forge server version specified in minecraftinstance is installed where we can access it"""
		if not os.path.isfile(self.forge_installer_path):
			print("Downloading installer for forge {ver} (URL: {url})...".format(ver=self.forge_version,url=self.forge_installer_url))
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
				"saves",
				os.path.join("mods","mod_list.json"),
			]
		)
		if not self.remove_server_mods_fname is None:
			if not os.path.isfile(self.remove_server_mods_fname):
				print('WARNING: Removed mods list "{}" does not exist! Installing all mods to server...'.format(self.remove_server_mods_fname))
			else:
				print('Disabling troublesome mods listed in "{}"...'.format(self.remove_server_mods_fname))
				with open(self.remove_server_mods_fname, 'r') as fp:
					remove_mods = json.load(fp)
				for mod in remove_mods:
					mod_path_A = os.path.join(self.temp_server_dir, "mods", mod)
					mod_path_B = mod_path_A + '.jar'
					mod_paths = [mod_path_A, mod_path_B]
					for mod_path in mod_paths:
						if os.path.isfile(mod_path):
							mod_disabled_path = mod_path + ".disabled"
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
		file_ops.copy_directory(self.additional_server_files_dir_native, self.temp_server_dir)

		print('Modifying settings files to include correct versions...')
		settings_files = [
			'settings.bat', 
			'settings.sh', 
			'settings.py', 
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
	
	def package_docker_server(self):
		"""
		convert the server package directory into a docker image and push the image to a container registry
			skips upload if container registry not specified as part of docker_image_name
			requires docker (https://www.docker.com/) to be installed and Dockerfile included in root of additional_server_files_dir, else skips this step
			runs Dockerfile with build context directory in the root of the server package directory
		"""
		dockerfile_filename = os.path.join(self.package_server_dir, 'Dockerfile')
		print("Checking if Dockerfile exists...")
		if not os.path.isfile(dockerfile_filename):
			print("No Dockerfile found! Skipping docker packaging!")
			return
		print("Checking if docker is installed...")
		try:
			subprocess.check_call(['docker', '--version'])
		except subprocess.CalledProcessError:
			print("Docker installation not found! Skipping docker packaging!")
			return
		if self.docker_image_name is None:
			self.docker_image_name = self.modpack_name.lower()
		docker_tags = [
			'{name}:{version}'.format(name=self.docker_image_name, version=self.modpack_version),
			'{name}:{version}'.format(name=self.docker_image_name, version='latest'),
		]
		if len(docker_tags)<=0:
			print("No docker tag names listed! Skipping docker packaging!")
			return
		print('Building docker container "{name_ver}"...'.format(name_ver=docker_tags[0]))
		subprocess.check_call(['docker', 'build', '--rm', '-f', dockerfile_filename, '-t', docker_tags[0], self.package_server_dir], cwd=self.package_server_dir)
		print("Docker container built!")
		for tagname in docker_tags[1:]:
			print('Tagging build as "{tagname}"...'.format(tagname=tagname))
			subprocess.check_call(['docker', 'tag', docker_tags[0], tagname])
			print("Inage tagged!")
		for tagname in docker_tags:
			if '/' in tagname:
				print('Uploading docker image "{tagname}"...'.format(tagname=tagname))
				subprocess.check_call(['docker', 'push', tagname])
				print("Image uploaded!")
		print("Docker container packaging complete!")
	
	def cleanup(self):
		"""deletes the temporary files used during creation of packages"""
		print('Deleting temporary directory "{}"...'.format(self.temp_version_dir))
		shutil.rmtree(self.temp_version_dir)
		print('Temporary directory cleared!')
	
	def run(self):
		"""runs the entire packaging procedure in order, including prep, package_client, package_server, package_docker_server, and cleanup"""
		self.prep()
		self.package_client()
		self.package_server()
		self.package_docker_server()
		self.cleanup()

if __name__=='__main__':
	parser = argparse.ArgumentParser(description='TEST_DESCRIPTION')
	parser.add_argument('-j', '--client_info_fname',           dest='client_info_fname',           default=argparse.SUPPRESS, help='Filename of a JSON file containing settings.  For details, see example file "client_loc_info.json".  Values specified in the JSON file override those specified by command-line.')
	parser.add_argument('-r', '--remove_server_mods_fname',    dest='remove_server_mods_fname',    default=argparse.SUPPRESS, help='Filename of a JSON file containing a list of mods to remove for the server.  Should contain a list of filenames in the format ["ExampleMod1-1.12-1.0.1.jar", "ExampleMod2-1.12.2-3.2.01.jar"].')
	parser.add_argument('-d', '--modpack_dir',                 dest='modpack_dir',                 default=argparse.SUPPRESS, help='Path to the directory from which the modpack files should be copied.  On systems running Windows Subsystem for Linux (WSL), supports both WSL paths (/mnt/c/...) and Windows paths (C:\...).')
	parser.add_argument('-p', '--packages_dir',                dest='packages_dir',                default=argparse.SUPPRESS, help='Path to the directory in which the finished modpack packages should be created.  On systems running Windows Subsystem for Linux (WSL), supports both WSL paths (/mnt/c/...) and Windows paths (C:\...).')
	parser.add_argument('-a', '--additional_server_files_dir', dest='additional_server_files_dir', default=argparse.SUPPRESS, help='Path to the directory from which additional files for the server should be copied.  Defaults to the folder "additional_server_files" installed with the packager.  On systems running Windows Subsystem for Linux (WSL), supports both WSL paths (/mnt/c/...) and Windows paths (C:\...).')
	parser.add_argument('-n', '--modpack_name',                dest='modpack_name',                default=argparse.SUPPRESS, help='Name of the modpack used as a prefix for filenames and listed in client "manifest.json".  If not specified (here or in JSON file), defaults to the name specified in "minecraftinstance.json" in the modpack directory.')
	parser.add_argument('-v', '--modpack_version',             dest='modpack_version',             default=argparse.SUPPRESS, help='Version number of the modpack used as a suffix for filenames and listed in client "manifest.json".  If not specified (here or in JSON file), an error is encountered. #TODO: Implement auto-incrementing version numbers!') #TODO
	args = parser.parse_args()
	init_settings = args.__dict__
	modpack_packager(**init_settings).run()
