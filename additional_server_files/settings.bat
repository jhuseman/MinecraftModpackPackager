rem Do not touch
set MCVER={{[MCVER]}}
set JARFILE=minecraft_server.%MCVER%.jar
set LAUNCHWRAPPERVERSION={{[LAUNCHERVER]}}
set LAUNCHWRAPPER=net\minecraft\launchwrapper\%LAUNCHWRAPPERVERSION%\launchwrapper-%LAUNCHWRAPPERVERSION%.jar
set FORGEJAR={{[FORGEJAR]}}

rem can be changed by user
set MAX_RAM=2048M
set JAVA_PARAMETERS=-XX:+UseParNewGC -XX:+CMSIncrementalPacing -XX:+CMSClassUnloadingEnabled -XX:ParallelGCThreads=5 -XX:MinHeapFreeRatio=5 -XX:MaxHeapFreeRatio=10
