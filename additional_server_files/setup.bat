call settings.bat

mkdir libraries\net\minecraft\launchwrapper\%LAUNCHWRAPPERVERSION%

libraries\wget.exe -O %JARFILE% https://s3.amazonaws.com/Minecraft.Download/versions/%MCVER%/%JARFILE%
libraries\wget.exe -O libraries\%LAUNCHWRAPPER% https://libraries.minecraft.net/net/minecraft/launchwrapper/%LAUNCHWRAPPERVERSION%/launchwrapper-%LAUNCHWRAPPERVERSION%.jar


set eula_missing=T
if exist eula.txt (
	set eula_missing=F
	find "eula=false" eula.txt 1 > NUL 2>&1
	if %ERRORLEVEL% EQU 0 (
		set eula_missing=T
	)
)
set eula_accepted=NO
if "%eula_missing%"=="T" (
	echo Type "yes" to indicate your agreement to Minecraft's EULA ^(https://account.mojang.com/documents/minecraft_eula^).
	set /P eula_accepted=
)
if "%eula_accepted%"=="yes" (
	echo eula=true > eula.txt
)