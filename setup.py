#!/usr/bin/env python

import os

from distutils.core import setup
from MinecraftModpackPackager import version_number

add_package_files_multilevel = [[os.path.join(a[0].split(os.sep, 1)[1],b) for b in a[2]] for a in os.walk(os.path.join('MinecraftModpackPackager','additional_server_files'))]
add_package_files = [item for sublist in add_package_files_multilevel for item in sublist]

setup(name='MinecraftModpackPackager',
	version=version_number.modpack_packager_version,
	description='A script for packaging the mods in a custom TwitchApp Minecraft modpack into both a server package and a Twitch-submittable client package.',
	author='Joshua Huseman',
	author_email='jhuseman@alumni.nd.edu',
	url='https://github.com/jhuseman/MinecraftModpackPackager',
	packages=['MinecraftModpackPackager'],
	package_data={'MinecraftModpackPackager': ['client_loc_info.json', 'remove_server_mods.json']+add_package_files},
)
