#!/usr/bin/env python3

"""
Curseforge hates me but I found a workaround
This is it, my messterpiece

Todo:
Manual version spec
Delete removed mods
"""

import json
from pprint import pprint
import re
import requests
import wget
import os
from termcolor import colored

modfile = "modlist.txt"
trackerfile = "modtracker.txt"
modDir = "mods" # Don't use ./
versionparam = {"1.14.4":2, "Forge":1} # Preferred terms should be weighted more highly

exreg = r"([^\/]*)$"
apithing = "https://api.cfwidget.com/minecraft/mc-mods/"


def main():
	print("Gathering important stuff, this might take a while")
	mods = readMods(modfile)
	nameLinks = getNameLinks(mods, versionparam)
	pprint(nameLinks)
	downloadMods(nameLinks)

	print("\nDone!")


def downloadMods(nameLinks):
	# Make mod dir if not exist
	if not os.path.exists(modDir):
		os.mkdir(modDir)

	# Load tracker
	oldlinks = {}
	if os.path.isfile(trackerfile):
		with open(trackerfile) as j:
			oldlinks = json.load(j)

	# Download loop
	for link in nameLinks.keys():
		loc =  modDir + "/%s.jar" % link
		if link in oldlinks.keys():
			if nameLinks[link] == oldlinks[link]:
				continue # Skip if not new and no update available
			else:
				print("Updating %s" % link)
				os.remove(loc) # Remove old mod
		else:
			print("Downloading new mod %s" % link) # New mod
		downloadFile(nameLinks[link], loc) # Download the stuff

	# Update tracker
	with open(trackerfile, "w") as t:
		json.dump(nameLinks, t)


# Downloads a file
def downloadFile(url, out):
	print("DL: %s" % url)
	wget.download(url, out)
	print()


# Returns a list of mods to be downloaded
def readMods(path):
	theFile = open(path)
	contents = theFile.readlines()
	theFile.close()
	filtered = []
	for line in contents:
		line = line.split('#',1)[0].strip()
		if not line:
			continue 
		line = re.search(exreg, line, re.M|re.I).group(1).strip()
		filtered.append(line)
	return filtered


# It's easy
def errorMsg(msg):
	print(colored(msg, 'red'))


# Gets the links to the files
# Returns a dictionary mapping the names to the links
def getNameLinks(modlist, version):
	# Build the name and id dict
	nameIdDict = {}
	for mod in modlist:
		print("Finding %s" % mod)
		# Prepare id
		link = apithing + mod
		#print("Getting data from %s" % link)
		jdata = getJSON(link)
		if "error" in jdata.keys():
			print("")
			textyyy = mod + " - " + jdata["error"]
			errorMsg("Could not find %s" % textyyy)
			continue
		# Make entry
		mid = jdata["id"]
		fid = getFileId(jdata["files"], version)
		# Retrieve the actual download link
		protodirectlink = "https://addons-ecs.forgesvc.net/api/v2/addon/%s/file/%s/download-url" % (mid, fid) # The link that gets the link
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'} # Required to prevent 403
		directlink = requests.get(protodirectlink, headers=headers).text
		nameIdDict[mod] = directlink
		
	return nameIdDict


# Finds a link to a mod file based on version specs
def getFileId(files, version):
	fileid = 0 # should use date uploaded
	outerAccuracy = 0
	outerFid = 0
	for release in ["release", "beta", "alpha"]:
		accuracy = 0
		for filey in files:
			if filey["type"] != release:
				continue # Skip if not matching the release type
			fireversions = filey["versions"]
			newAccuracy = 0

			#print("\tScanning %s" % filey["name"])
			for v in version:
				if v in fireversions:
					newAccuracy += versionparam[version]
					#print("\t\tAdding %s because it has %s, total is %i" % (bonus, v, newAccuracy))
					continue # Don't count multiple times
				
			#print(fireversions, " - ", newAccuracy)
			if newAccuracy > accuracy:
				fileid = filey["id"]
				accuracy = newAccuracy
			elif newAccuracy == accuracy and filey["id"] > fileid:
				fileid = filey["id"]
				accuracy = newAccuracy
		if accuracy == sum(version.values()): # I HATE THIS
			print("\tPerfectly matched %s with id %s with accuracy %i/%i" % (release, fileid, accuracy, sum(version.values())))
			return fileid # It's as good as we will find
		elif fileid != 0:
			print("\tMatched %s with id %s with accuracy %i/%i" % (release, fileid, accuracy, len(version)))
			if outerAccuracy < accuracy:
				print("\treplacing outer")
				outerAccuracy = accuracy
				outerFid = fileid
		else:
			print("\tNo %s found" % release)
	return outerFid
	

# It gets JSON data
def getJSON(url):
	r = requests.get(url)
	return r.json()


if __name__ == "__main__":
	main()

