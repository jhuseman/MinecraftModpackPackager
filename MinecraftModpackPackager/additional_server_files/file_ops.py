#!/usr/bin/env python

import os
import shutil

import requests

def copy_file(src, dest):
	"""copies the contents of a file into another file"""
	if not os.path.isdir(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest))
	shutil.copy2(src, dest)

def copy_directory(src, dest, exclude=[]):
	"""
	copy directory and its contents from one place (src) to another (dest)
	if dest does not exist, create the folder
	do not copy any files or directories specified in exclude
	"""
	def path_first_split(path):
		head, tail = os.path.split(path)
		if head=='':
			return (tail, '')
		else:
			first, rest = path_first_split(head)
			if tail=='':
				return (first, rest)
			else:
				return (first, os.path.join(rest, tail))
	if not os.path.isdir(dest):
		os.makedirs(dest)
	if False and len(exclude)==0: # temporarily disabled this case - just use my own implementation for this TODO: find more efficient implementation
		shutil.copytree(src, dest)
	else:
		exclude_split = [path_first_split(ex) for ex in exclude]
		exclude_dict = {}
		for first, rest in exclude_split:
			if not first in exclude_dict:
				exclude_dict[first] = []
			exclude_dict[first].append(rest)
		for first in exclude_dict:
			if '' in exclude_dict[first]:
				#don't copy this file/folder
				pass
			else:
				first_path = os.path.join(src, first)
				first_dest_path = os.path.join(dest, first)
				if os.path.isdir(first_path):
					#copy this with modified exclude list
					copy_directory(first_path, first_dest_path, exclude=exclude_dict[first])
		dont_recurse_norm = [ex[0] for ex in exclude_split]
		contents = os.listdir(src)
		for cont in contents:
			if not cont in dont_recurse_norm:
				cont_path = os.path.join(src, cont)
				cont_dest_path = os.path.join(dest, cont)
				if os.path.isdir(cont_path):
					copy_directory(cont_path, cont_dest_path)
				else:
					copy_file(cont_path, cont_dest_path)

def create_zip(directory, archive):
	"""create a zip archive containing the contents of a directory, with the filename specified in archive"""
	if not os.path.isdir(os.path.dirname(archive)):
		os.makedirs(os.path.dirname(archive))
	basename, ext = os.path.splitext(archive)
	shutil.make_archive(basename, 'zip', directory)
	if ext!='.zip':
		archive_name = basename+'.zip'
		os.rename(archive_name, archive)

def replace_in_file(filename, rep):
	"""replaces contents of filename matching keys in the given dict with the contents of the paired value in the dict"""
	with open(filename, 'r') as fp:
		file_contents = fp.read()
	for find in rep:
		file_contents = file_contents.replace(find, rep[find])
	with open(filename, 'w') as fp:
		fp.write(file_contents)

def download_file(url, filename):
	"""downloads the file at the specified url and saves it to the specified filename"""
	par_dir = os.path.dirname(filename)
	if not os.path.isdir(par_dir):
		if par_dir!='':
			os.makedirs(par_dir)
	r = requests.get(url, stream=True)
	with open(filename, 'wb') as fd:
		for chunk in r.iter_content(chunk_size=128):
			fd.write(chunk)
