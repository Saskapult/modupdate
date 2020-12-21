#!/bin/env python3

import json
from pprint import pprint
import re
import requests
import wget
import os
import sys


modDir = "mods" # Don't use ./

# Required to prevent 403 with twitch api
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}


def main():	
	# Set up modlist file and the tracker file
	if len(sys.argv) >= 2:
		modfile = sys.argv[1]
		print("Using specified modfile %s" % sys.argv[1])
	else:
		modfile = "moddata.txt"
	trackerfile = modfile.split(".")[0] + "_tracker.txt"

	# Get some good stuff
	versionparam, mods = readData(modfile)
	mods.sort()
	
	# Try to get mod pids but fall back to using the name if can't find
	numMods = len(mods)
	mids = []
	print("Finding project ids, this may take a while")
	for i in range(0, numMods):
		print("Found %i/%i" % (i, numMods), end="\r")
		pid = getProjectID(mods[i])
		if pid != 0:
			mids.append(pid)
		else:
			print("Could not find pid of %s, using fallback" % mods[i])
			mids.append(mods[i])
	print("Found %i/%i" % (numMods, numMods))

	nameLinks, notFound = getNameLinks(mods, versionparam)
	#pprint(nameLinks)
	print("Couldn't find files for:")
	pprint(notFound)
	downloadMods(nameLinks, trackerfile)
	print("\nDone!")


# Returns a list of mods to be downloaded
def readData(path):
	theFile = open(path)
	lines = theFile.readlines()
	theFile.close()
	
	filtered = []
	minfo = {}
	i = 0
	while i < len(lines):
		line = lines[i]
		# Read versionparam variable
		if line.startswith("versionparam"):
			jsonstr = line.split["= "][1]
			# Loop until all json is read
			bdiff = jsonstr.count("{") - jsonstr.count("}") # num '{' minus num '}'
			loopcount = 0
			while bdiff != 0:
				newline = lines[i+loopcount]
				bdiff += newline.count("{") - newline.count("}")
				loopcount += 1
				if loopcount > 10: # Don't loop forever
					print("Read more than 10 lines if json, assuming error")
					exit(1)
			# Try to interpert the json
			try:
				minfo = json.loads(jsonstr.strip())
			except ValueError as e:
				print("Version data could not be interperted: ")
				print(e)
				exit(1)
			continue
		
		# Comment filtration
		line = line.split('#',1)[0].strip()
		if not line:
			continue 
		line = re.search(r"([^\/]*)$", line, re.M|re.I).group(1).strip()

		filtered.append(line)
	
	print("Read %i mods" % len(filtered))
	
	# Check that versionparams exist
	if len(minfo) == 0:
		print("ERROR: Version params are empty")
		exit(1)
	
	return minfo, filtered


# Gets the project ID associated with the mod
# Returns 0 if mod is not found
# This prevents some cfwidget api stuff from becoming confused
def getProjectID(url):
	modname = linkEnd(url)
	link = "https://addons-ecs.forgesvc.net/api/v2/addon/search?gameId=432&index=0&pageSize=255&searchFilter=%s&sectionId=6&sort=0" % modname
	search = getJSON(link)

	# Try to find matching link
	for result in search:
		if result["slug"] == modname:
			return result["id"] # Found it!
	# Nothing found
	return 0


# Gets the links to the files
# Mods can contain name strings or project ids or both
# Returns a dictionary mapping the names to the links
def getNameLinks(mods, version):
	# Build the name and id dict
	nameIdDict = {}
	notFound = {}
	for mod in mods:
		print("Finding %s" % mod)
		
		# Retrieve the JSON data
		link = "https://api.cfwidget.com/minecraft/mc-mods/" + str(mod)
		jdata = getJSON(link)
		if "error" in jdata.keys():
			textyyy = mod + " - " + jdata["error"]
			print("ERROR: Failure retrieving %s" % textyyy)
			exit(1)

		# Get the file id
		mid = jdata["id"]
		fid = getFileId(jdata["files"], version)
		if fid == 0: # Was unable to find a file
			print("WARNING: Could not find file for %s" % mod)
			notFound[mod] = link
			continue
		
		# Retrieve the actual download link
		protodirectlink = "https://addons-ecs.forgesvc.net/api/v2/addon/%s/file/%s/download-url" % (mid, fid) # The link that gets the link
		directlink = requests.get(protodirectlink, headers=headers).text
		
		# Get the proper file name
		filename = linkEnd(directlink)
		
		# Make the entry
		nameIdDict[filename] = directlink
		
	return nameIdDict, notFound


# Sort out the downloading
def downloadMods(nameLinks, trackerfile):
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


# Get the text after the link's last "/"
def linkEnd(url):
	filename = url.split("/")
	filename = filename[len(filename)-1]
	return filename.strip()


# Downloads a file
def downloadFile(url, out):
	print("DL: %s" % url)
	wget.download(url, out)
	print()


# Gets JSON data
def getJSON(url):
	r = requests.get(url, headers=headers)
	if r.status_code != 200:
		print("Problem accessing %s, response %i" % (url, r.status_code))
		exit(1)
	return r.json()


if __name__ == "__main__":
	main()

