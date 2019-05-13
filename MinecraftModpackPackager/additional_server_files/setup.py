#!/usr/bin/env python3

#TODO: translate everything into python!

# # # # # # cd "$(dirname "$0")"
# # # # # # . ./settings.sh

# # # # # # mkdir -p $(dirname libraries/${LAUNCHWRAPPER})

# # # # # # which wget
# # # # # # if [ $? -eq 0 ]; then
# # # # # # 	wget -O ${JARFILE} https://s3.amazonaws.com/Minecraft.Download/versions/${MCVER}/${JARFILE}
# # # # # # 	wget -O libraries/${LAUNCHWRAPPER} https://libraries.minecraft.net/${LAUNCHWRAPPER}
# # # # # # else
# # # # # # 	which curl
# # # # # # 	if [ $? -eq 0 ]; then
# # # # # # 		curl -o ${JARFILE} https://s3.amazonaws.com/Minecraft.Download/versions/${MCVER}/minecraft_server.${MCVER}.jar
# # # # # # 			curl -o libraries/${LAUNCHWRAPPER} https://libraries.minecraft.net/${LAUNCHWRAPPER}
# # # # # # 	else
# # # # # # 		echo "Neither wget or curl were found on your system. Please install one and try again"
# # # # # # 	fi
# # # # # # fi

# # # # # # # cleaner code
# # # # # # eula_false() {
# # # # # # 	grep -q 'eula=false' eula.txt
# # # # # # 	return $?
# # # # # # }
# # # # # # # if eula.txt is missing inform user and start MC to create eula.txt
# # # # # # if [ ! -f eula.txt ] || eula_false ; then
# # # # # # 	echo "Type \"yes\" to indicate your agreement to Minecraft's EULA (https://account.mojang.com/documents/minecraft_eula)."
# # # # # # 	read eula_accepted
# # # # # # 	if [[ $eula_accepted = "yes" ]] ; then
# # # # # # 		echo "eula=true" > eula.txt
# # # # # # 	fi
# # # # # # fi
