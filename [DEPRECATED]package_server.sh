#! /bin/bash

export modpack_dir=$(wslpath -u "C:\Users\jdhus\OneDrive\SyncedUserFolders\Documents\Curse\Minecraft\Instances\Just the Essentials (1)")

export modpack_name="JustTheEssentials"

export mcver="1.12.2"
export launcherver="1.12"

# download [version]-installer.jar from http://files.minecraftforge.net/ and place it in the forge_jars folder
export forge_version="forge-1.12.2-14.23.5.2824"

export forge_universal_jar="$forge_version-universal.jar"
export forge_install_jar="$forge_version-installer.jar"
export forge_install_path="./forge_jars/$forge_install_jar"
export forge_install_folder="./forge_jars/installs/$forge_version"

while [ ! -d "$forge_install_folder" ]; do
	mkdir -p $forge_install_folder
	echo ""
	echo ""
	echo ""
	echo ""
	echo "Forge $forge_version is not installed!"
	echo "Press [RETURN] to start installer,"
	echo "then copy the following path into the install folder:"
	echo ""
	realpath $forge_install_folder
	read
	java -jar $forge_install_path
done

export unique_time="$(date +"%y_%m_%d__%H_%M_%S")"
export version_id=$modpack_name.v.$unique_time
export temp_dir=./temp/$unique_time
export new_modpack_dir=$temp_dir/modpack
export packaged_loc=packages/$unique_time
export packaged_dir=$packaged_loc/$version_id
export packaged_zip_fname=$version_id.zip

export win_settings=$new_modpack_dir/settings.bat
export unix_settings=$new_modpack_dir/settings.sh

echo 'creating temporary directory "'$temp_dir'"...'
mkdir -p $temp_dir

echo 'creating modpack directory "'$new_modpack_dir'"...'
mkdir $new_modpack_dir
echo 'copying mod files from "'$modpack_dir'/." to "'$new_modpack_dir'/"...'
cp -r "$modpack_dir/." "$new_modpack_dir/"
echo 'deleting "'$new_modpack_dir'/.curseclient"...'
rm -f "$new_modpack_dir/.curseclient"
echo 'deleting "'$new_modpack_dir'/minecraftinstance.json"...'
rm -f "$new_modpack_dir/minecraftinstance.json"
echo 'deleting "'$new_modpack_dir'/mods/mod_list.json"...'
rm -f "$new_modpack_dir/mods/mod_list.json"

echo 'Removing troublesome mods listed in "remove_mods.txt"...'
while IFS= read -r mod; do
	echo "$mod"
	mv "$new_modpack_dir/mods/$mod.jar" "$new_modpack_dir/mods/$mod.jar.removed"
done < "remove_mods.txt"

echo 'copying forge installation from "'$forge_install_folder'" into "'$new_modpack_dir'/"...'
cp -r "$forge_install_folder/." "$new_modpack_dir/"
echo 'deleting "'$new_modpack_dir'/libraries/net/minecraft/launchwrapper/'$launcherver'/launchwrapper-'$launcherver'.jar"...'
rm -f "$new_modpack_dir/libraries/net/minecraft/launchwrapper/$launcherver/launchwrapper-$launcherver.jar"
echo 'creating "'$new_modpack_dir'/libraries/net/minecraft/launchwrapper/'$launcherver'/KEEP_FOLDER"...'
touch "$new_modpack_dir/libraries/net/minecraft/launchwrapper/$launcherver/KEEP_FOLDER"
echo 'deleting "'$new_modpack_dir'/minecraft_server.'$mcver'.jar"...'
rm -f "$new_modpack_dir/minecraft_server.$mcver.jar"

echo 'copying additional files into  "'$new_modpack_dir'/"...'
cp -r "./additional_server_files/." "$new_modpack_dir/"

echo 'modifying settings files to include correct versions...'
sed -i 's/{{\[FORGEJAR\]}}/'$forge_universal_jar'/g' $unix_settings
sed -i 's/{{\[FORGEJAR\]}}/'$forge_universal_jar'/g' $win_settings
sed -i 's/{{\[LAUNCHERVER\]}}/'$launcherver'/g' $unix_settings
sed -i 's/{{\[LAUNCHERVER\]}}/'$launcherver'/g' $win_settings
sed -i 's/{{\[MCVER\]}}/'$mcver'/g' $unix_settings
sed -i 's/{{\[MCVER\]}}/'$mcver'/g' $win_settings

echo 'creating packaged modpack directory "'$packaged_dir'"...'
mkdir -p $packaged_dir
echo 'copying mod files from "'$new_modpack_dir'/." to packaged modpack directory "'$packaged_dir'/"...'
cp -r "$new_modpack_dir/." "$packaged_dir/"

echo 'moving into packaged modpack directory "'$packaged_dir'" for compression...'
pushd $packaged_dir
echo 'compressing mod files from "'$packaged_dir'" into packaged modpack "'$packaged_loc'/'$packaged_zip_fname'"...'
zip -r ../$packaged_zip_fname . > /dev/null
echo 'moving back out of packaged modpack directory "'$packaged_dir'" after compression...'
popd

echo 'deleting temporary directory "'$temp_dir'"...'
rm -r $temp_dir

