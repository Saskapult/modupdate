#!/bin/env python3

import json
from pprint import pprint
import re
import requests
import wget
import os


modfile = "moddata.txt"
trackerfile = modfile.split(".")[0] + "_tracker.txt"
modDir = "mods" # Don't use ./

exreg = r"([^\/]*)$"
apithing = "https://api.cfwidget.com/minecraft/mc-mods/"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'} # Required to prevent 403


def main():
	print("Gathering important stuff, this might take a while")
	versionparam, mods = readData(modfile)
	mods.sort()
	nameLinks, notFound = getNameLinks(mods, versionparam)
	#pprint(nameLinks)
	print("Couldn't find:")
	pprint(notFound)
	downloadMods(nameLinks)
	print("\nDone!")


# Returns a list of mods to be downloaded
def readData(path):
	theFile = open(path)
	contents = theFile.readlines()
	theFile.close()
	
	filtered = []
	minfo = {}
	for line in contents:
		# Version info reader
		if line.startswith("{"):
			try:
				minfo = json.loads(line.strip())
			except ValueError as e:
				print("Version data could not be interperted: ")
				print(e)
				exit(1)
			continue
		
		# Comment filtration
		line = line.split('#',1)[0].strip()
		if not line:
			continue 
		line = re.search(exreg, line, re.M|re.I).group(1).strip()

		filtered.append(line)
	
	print("Read %i mods" % len(filtered))
	
	# Check that versionparams exist
	if len(minfo) == 0:
		print("ERROR: Version params are empty")
		exit(1)
	
	return minfo, filtered


# Gets the links to the files
# Returns a dictionary mapping the names to the links
def getNameLinks(modlist, version):
	# Build the name and id dict
	nameIdDict = {}
	notFound = {}
	for mod in modlist:
		print("Finding %s" % mod)
		
		# Retrieve the JSON data
		link = apithing + mod
		#print(link)
		jdata = getJSON(link)
		if "error" in jdata.keys():
			textyyy = mod + " - " + jdata["error"]
			print("ERROR: Failure retrieving %s" % textyyy)
			exit(1)

		# Get the file id
		mid = jdata["id"]
		fid = getFileId(jdata["files"], version)
		if fid == 0: # Was unable to find a file
			print("WARNING: Could not find %s" % mod)
			notFound[mod] = link
			continue
		
		# Retrieve the actual download link
		protodirectlink = "https://addons-ecs.forgesvc.net/api/v2/addon/%s/file/%s/download-url" % (mid, fid) # The link that gets the link
		directlink = requests.get(protodirectlink, headers=headers).text
		
		# Get the proper file name
		filename = directlink.split("/")
		filename = filename[len(filename)-1]
		
		# Make the entry
		nameIdDict[filename] = directlink
		
	return nameIdDict, notFound


# Sort out the downloading
def downloadMods(nameLinks):
	# Make mod dir if not exist
	if not os.path.exists(modDir):
		os.mkdir(modDir)

	# Load tracker
	oldlinks = {}
	if os.path.isfile(trackerfile):
		with open(trackerfile) as j:
			oldlinks = json.load(j)

	# Remove the removed stuff
	for modname in oldlinks.keys():
		if modname not in nameLinks.keys():
			print("Removing %s" % modname)
			loc = modDir + "/%s.jar" % modname
			os.remove(loc) # Remove old mod

	# Download loop
	for link in nameLinks.keys():
		loc = modDir + "/%s.jar" % link
		if link in oldlinks.keys():
			if nameLinks[link] == oldlinks[link]:
				continue # Skip if not new and no update available
			else:
				print("Updating %s" % link)
				os.remove(loc) # Remove old mod
		else:
			print("Downloading %s" % link) # New mod
		downloadFile(nameLinks[link], loc) # Download the stuff

	# Update tracker
	with open(trackerfile, "w") as t:
		json.dump(nameLinks, t)


# Finds a link to a mod file based on version specs
# Returns 0 if not found
def getFileId(files, version):
	fileid = 0
	outerAccuracy = 0
	outerFid = 0
	for release in ["release", "beta", "alpha"]:
		accuracy = 0

		# This *should* perfer the latest release because of the api ordering
		for filey in files:
			# Skip if not matching the release type
			if filey["type"] != release:
				continue 
			
			# Check version tags
			fireversions = filey["versions"]
			newAccuracy = 0
			#print("\tScanning %s" % filey["name"])
			for v in version:
				if v in fireversions:
					newAccuracy += version[v]
					#print("\t\tAdding %s because it has %s, total is %i" % (bonus, v, newAccuracy))
					#continue # Don't count multiple times
			
			# See if it's good
			#print(fireversions, " - ", newAccuracy)
			if newAccuracy > accuracy:
				fileid = filey["id"]
				accuracy = newAccuracy
			elif newAccuracy == accuracy and filey["id"] > fileid:
				fileid = filey["id"]
				accuracy = newAccuracy
		
		# Found a perfectly matching file
		if accuracy == sum(version.values()): # I HATE THIS
			print("\tPerfectly matched %s with id %s with accuracy %i/%i" % (release, fileid, accuracy, sum(version.values())))
			return fileid # It's as good as we will find
		
		# Found an imperfect match
		elif fileid != 0:
			print("\tMatched %s with id %s with accuracy %i/%i" % (release, fileid, accuracy, sum(version.values())))
			if outerAccuracy < accuracy:
				print("\treplacing outer")
				outerAccuracy = accuracy
				outerFid = fileid
		
		# Found nothing
		else:
			print("\tNo %s found" % release)
	
	# Failed to find a match
	if outerAccuracy == 0:
		return 0

	return outerFid


# Downloads a file
def downloadFile(url, out):
	print("DL: %s" % url)
	wget.download(url, out)
	print()


# Gets JSON data
def getJSON(url):
	r = requests.get(url)
	return r.json()


if __name__ == "__main__":
	main()

