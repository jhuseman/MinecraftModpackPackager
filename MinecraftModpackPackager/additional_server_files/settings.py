#!/usr/bin/env python3

###################################################
"""Configuration for ServerStart.py and setup.py"""
###################################################
# Pack specific settings
# Only edit this section if you know what you are doing
server_settings = {
	"MCVER":"{{[MCVER]}}", 
	"JARFILE":"minecraft_server.${MCVER}.jar", 
	"LAUNCHWRAPPERVERSION":"{{[LAUNCHERVER]}}", 
	"LAUNCHWRAPPER":"net/minecraft/launchwrapper/${LAUNCHWRAPPERVERSION}/launchwrapper-${LAUNCHWRAPPERVERSION}.jar", 
	"FORGEJAR":"{{[FORGEJAR]}}", 

	###################################################
	# Default arguments for JVM

	"JAVACMD":"java", 
	"MAX_RAM":"2048M",        # -Xmx
	"JAVA_PARAMETERS":"-XX:+UseParNewGC -XX:+CMSIncrementalPacing -XX:+CMSClassUnloadingEnabled -XX:ParallelGCThreads=5 -XX:MinHeapFreeRatio=5 -XX:MaxHeapFreeRatio=10", 
}
