#!/usr/bin/env python

import os
import subprocess

def is_win_path(path):
	if len(path)==0:
		return False
	first_char = path[0]
	rem_path = path[1:]
	if first_char in ['/']:
		return False
	elif first_char in ['\\']:
		return True
	else:
		if len(rem_path)==0:
			return False
		second_char = rem_path[0]
		rem_rem_path = rem_path[1:]
		if second_char in [':']:
			if len(rem_rem_path)==0:
				return True
			third_char = rem_rem_path[0]
			rem_rem_rem_path = rem_rem_path[1:]
			if third_char in ['\\', '/']:
				return True
			else:
				return False
		elif second_char in ['/']:
			return False
		elif second_char in ['\\']:
			return True
		else:
			return False
	return False

def is_wsl_path(path):
	if path[:5]=='/mnt/':
		if path[5:][:1] in ['/','']:
			return False
		if path[6:][:1] in ['/','']:
			return True
	return False

def is_running_win():
	if os.name in ['nt']:
		return True
	return False

def is_running_wsl():
	if is_running_win():
		return False
	if os.name in ['posix']:
		if 'microsoft' in os.uname().release.lower():
			return True
		if 'microsoft' in os.uname().version.lower():
			return True
	return False

def translate_wsl_to_win(path):
	try:
		return subprocess.check_output(['bash','-c',"wslpath -w '{}'".format(path)]).decode('utf-8').replace('\n','')
	except subprocess.CalledProcessError:
		print('WARNING: wslpath call could not translate path "{}"! Using untranslated path!'.format(path))
		return path

def translate_win_to_wsl(path):
	try:
		return subprocess.check_output(['bash','-c',"wslpath -u '{}'".format(path)]).decode('utf-8').replace('\n','')
	except subprocess.CalledProcessError:
		print('WARNING: wslpath call could not translate path "{}"! Using untranslated path!'.format(path))
		return path

def translate_path_to_native(path):
	if is_win_path(path) and is_running_wsl():
		return translate_win_to_wsl(path)
	elif is_wsl_path(path) and is_running_win():
		return translate_wsl_to_win(path)
	return path