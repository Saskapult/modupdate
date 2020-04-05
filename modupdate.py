#!/usr/bin/env python3

"""
Curseforge hates me but I found a workaround
This is it, my messterpiece

I should put the version in the modlist file
The regex thing needs work, it is not flexable
"""

import json
from pprint import pprint
import re
import requests
import wget
import os

modfile = "modlist.txt"
trackerfile = "modtracker.txt"
version = "1.14"
exreg = r"([^\/]*)$"
apithing = "https://api.cfwidget.com/minecraft/mc-mods/"
modDir = "mods" # Don't use ./

missingthing = []


def main():
	print("Gathering important stuff, this might take a while")
	links = getLinkdict(modfile)

	# Load tracker
	oldlinks = {}
	if os.path.isfile(trackerfile):
		with open(trackerfile) as j:
			oldlinks = json.load(j)
	
	# Make mod dir if not exist
	if not os.path.exists(modDir):
		os.mkdir(modDir)
	
	# Download loop
	for link in links.keys():
		loc =  modDir + "/%s.jar" % link
		if link in oldlinks.keys():
			if links[link] == oldlinks[link]:
				continue # Skip if not new and no update available
			else:
				print("Updating %s" % link)
				os.remove(loc) # Remove old mod
		else:
			print("Downloading new mod %s" % link) # New mod
		getFile(links[link], loc) # Download the stuff

	# Update tracker
	with open(trackerfile, "w") as t:
		json.dump(links, t)

	print()
	for missing in missingthing:
		print("We missed %s" % missing)

	print("\nDone!")


def getFile(url, out):
	print("DL: %s" % url)
	wget.download(url, out)
	print()


def getLinkdict(file):
	theFile = open(file)
	contents = theFile.readlines()
	theFile.close()
	# Build the name and id dict
	nameIdDict = {}
	for line in contents:
		# Skip if is comment
		if line.startswith("#") or not line.strip():
			continue 
		# Prepare name
		name = re.search(exreg, line, re.M|re.I).group(1).strip()
		
		print("Finding %s" % name)
		
		# Prepare id
		link = apithing + name
		if version != "":
			link += "?version=" + version
		
		print("Getting data from %s" % link)

		jdata = getJSON(link)
		if "error" in jdata.keys():
			print("NOT FOUND THING I HATE THIS")
			textyyy = name + " - " + jdata["error"]
			missingthing.append(textyyy)
			continue


		modid = jdata["id"]
		fileid = jdata["download"]["id"]

		protodirectlink = "https://addons-ecs.forgesvc.net/api/v2/addon/%s/file/%s/download-url" % (modid, fileid) # The link that gets the link
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'} # Required to prevent 403
		directlink = requests.get(protodirectlink, headers=headers).text
		# Make entry
		nameIdDict[name] = directlink
	return nameIdDict

def getJSON(url):
	r = requests.get(url)
	return r.json()


if __name__ == "__main__":
	main()

