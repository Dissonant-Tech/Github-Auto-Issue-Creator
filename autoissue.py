#!/usr/bin/python
#from os import listdir, path
import os, argparse, re
from util import debug_print

#global vars
blacklist = [".git", "autoissue.py*", "github.py*", "README.md", "util.py*", "settings.williames", ".gitignore", "setup", "*.DS_Store", "test/parsingtests", "test.py*"] #blacklist for file/dir names (added .DS_Store because super annoying)
startToken = "TODO"
endToken = "ODOT"

#issue class, just has the content and lineNumber fields right now.
class Issue:
	def __init__(self, title, issueContent, lineNumber, fileName, label, inum):
		self.data = {}
		self.title = title
		self.issue = issueContent
		self.line = lineNumber
		self.fileName = fileName
		self.label = label
		self.issue_num = inum

	def __str__(self):
		return "Issue: {}\n\tIssue#: {}\n\tFile: {}\n\tLine: {}\n\tLabels: {}\n\tContent: {}\n".format(self.title, self.issue_num, self.fileName, self.line, self.label, self.issue)

	def __cmp__(self, other):
		return self.title == other.title \
		and self.issue == other.issue \
		and	self.line  == other.line \
		and	self.fileName  == other.fileName \
		and	self.label == other.label \
		and	self.issue_num == other.issue_num \

def blacklistToRegex():
	return [path.replace("*", "(.*)") for path in blacklist]

#Function that gets all of the files (and folders) in a folder
def getFiles(directory):
	#List all sub-directories and files
	fileList = []
	blacklisted = False

	for d in os.listdir(directory):
		d = directory + "/" + d #make the format actually work for our function calls

		print "Checking blacklist for", d.replace("./", "")
		if any([re.match(pattern + "$", d.replace("./", "")) is not None for pattern in blacklistToRegex()]):
			print "Blacklisted."
		else:
			#if the "file" is a directory...
			if os.path.isdir(d) and not ".git" in d: #we never want .git files; excluded to prevent stdout pollution
				for file in getFiles(d): #recursively iterate through the subfolders
					fileList.append(file)

			#otherwise the file is indeed a file (excluding the current file, autoissue.py)
			#make sure our file isn't blacklisted before actually adding it to the list
			else:
				if d not in blacklist:
					fileList.append(d)
	#return list of actual files to open
	return fileList

# returns a list of the Issues in this file
def findIssuesInFile(file):
	lineNumber = 0
	issueList = []

	with open(file, 'r') as f:
		data = f.readlines()

	debug_print("Searching for issues in:", file, "(lines: {})".format(len(data)))

	while lineNumber < len(data):
		issueString = ""
		if startToken in data[lineNumber]:
			if data[lineNumber].strip().startswith("//"):
				startingLine = lineNumber
				issueString += data[lineNumber]
				lineNumber += 1
				while lineNumber < len(data):
					line = data[lineNumber]
					if line.strip(): # if the line is not empty
						if line.startswith("//"):
							issueString += line
						else:
							lineNumber -= 1 # since we increment outside of this loop
							break
					lineNumber += 1
			elif data[lineNumber].strip().startswith("/*"):
				startingLine = lineNumber
				issueString += data[lineNumber]
				if not issueString.strip().endswith("*/"):
					lineNumber += 1
					while lineNumber < len(data):
						line = data[lineNumber]
						if line.strip():
							issueString += line
							if line.strip().endswith("*/"):
								break
						lineNumber += 1
			else:
				lineNumber += 1
				break
			issueList.append(parseIssueFromRawComment(issueString, startingLine, file))
		lineNumber += 1
	return issueList


# returns an Issue
def parseIssueFromRawComment(comment, line, file):
	data = {}
	title = None
	labels = []
	inum = None
	tags_regex = "\[(.*?)\]"
	r = re.compile(tags_regex)
	tags = r.findall(comment)

	# If no [title:] tag is specified, then the first line is autmatically the title
	for tag in tags:
		if ":" not in tag:
			# This is the issue number tag
			inum = int(tag) # Should eventually check to be sure there are only numbers in here
		else:
			t, v = tag.split(":")
			#print "TAG:", t, "VALUE:", v
			if t.lower() == "title":
				title = v
			elif t.lower() == "label":
				labels = [x.strip() for x in v.split(",")]

	if title is None:
		title = "*AutoIssue* " + comment.split("\n")[0] # Make the title the first line of the comment

	content = re.sub(tags_regex, "", comment)
	content = re.sub("(//(\s*)TODO)|(/\*(\s*)TODO)|(\*/)", "", content).strip()
	issue = Issue(title, content, line + 1, file, labels, inum)
	issue.data = data
	return issue


def debug_add(base, addition):
	print base, "+", addition
	return base + addition


def injectNumber(issue, number):
	with open(issue.fileName, 'r') as file:
		data = file.readlines()

	lineNumber = issue.line - 1
	line = data[lineNumber]
	startIndex = line.index(startToken) + len(startToken)
	print "Before:", data[lineNumber]
	data[lineNumber] = data[lineNumber][:startIndex+1] + "[" + str(number) + "]" + data[lineNumber][startIndex:]
	print "After:", data[lineNumber]

	with open(issue.fileName, 'w') as file:
		file.writelines(data)

def main():
	from github import createIssues
	parser = argparse.ArgumentParser(description="Auto-Issue-Creator argument parser")
	parser.add_argument("-s", "--start", help="the token that begins the TODO: (ie. 'TODO')")
	parser.add_argument("-d", "--debug", action='store_true', help="enable debug mode (no POSTing to github)")

	args = vars(parser.parse_args())

	if args["start"] != None:
		global startToken #set scope
		startToken = args["start"]
		print "Starting token set as: ", startToken
	else:
		print "Using default starting token: ", startToken

	#see if we're in debug mode
	if args["debug"]:
		debug = True
		print "Debug mode enabled"
	else:
		debug = False

	getBlacklist()

	#issueList = getIssueList()
	#createIssues(issueList, debug)

	issueList = getIssues()
	createIssues(issueList, debug)

if __name__ == "__main__":
    #main()
	getBlacklist()
	print getFiles(".")
	#print blacklistToRegex()
