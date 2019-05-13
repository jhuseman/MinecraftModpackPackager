#!/usr/bin/env python

from distutils.core import setup
from MinecraftModpackPackager import version_number

setup(name='MinecraftModpackPackager',
	version=version_number.modpack_packager_version,
	description='A script for packaging the mods in a custom TwitchApp Minecraft modpack into both a server package and a Twitch-submittable client package.',
	author='Joshua Huseman',
	author_email='jhuseman@alumni.nd.edu',
	url='https://github.com/jhuseman/MinecraftModpackPackager',
	packages=['MinecraftModpackPackager'],
)