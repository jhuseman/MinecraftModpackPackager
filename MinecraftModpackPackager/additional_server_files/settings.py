#!/usr/bin/env python3

###################################################
"""Configuration for ServerStart.py and setup.py"""
###################################################
from types import SimpleNamespace


# Pack specific settings
# Only edit this section if you know what you are doing
server_settings_dict = {
	"mcver":"{{[MCVER]}}", 
	"jarfile":"minecraft_server.{{[MCVER]}}.jar", 
	"launchwrapperversion":"{{[LAUNCHERVER]}}", 
	"launchwrapper":"net/minecraft/launchwrapper/{{[LAUNCHERVER]}}/launchwrapper-{{[LAUNCHERVER]}}.jar", 
	"forgejar":"{{[FORGEJAR]}}", 

	###################################################
	# Default arguments for JVM

	"javacmd":"java", 
	"max_ram":"2048M",        # -Xmx
	"java_parameters":["-XX:+UseParNewGC", "-XX:+CMSIncrementalPacing", "-XX:+CMSClassUnloadingEnabled", "-XX:ParallelGCThreads=5", "-XX:MinHeapFreeRatio=5", "-XX:MaxHeapFreeRatio=10"], 
}

server_settings = SimpleNamespace(**server_settings_dict)
