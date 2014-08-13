#!/usr/bin/python
#from os import listdir, path
import os, argparse, re

#global vars
blacklist = [".git", "autoissue.py", "github.py", "README.md", "util.py", "settings.williames", ".gitignore"] #blacklist for file/dir names
startToken = "TODO"
endToken = "ODOT"

#issue class, just has the content and lineNumber fields right now.
class Issue:
	def __init__(self, title, issueContent, lineNumber, fileName, label):
		self.data = {}
		self.title = title
		self.issue = issueContent
		self.line = lineNumber
		self.fileName = fileName
		self.label = label

	def __str__(self):
		return "Issue: {}\n\tIssue#: {}\n\tFile: {}\n\tLine: {}\n\tLabels: {}\n\tContent: {}\n".format(self.title, self.data['number'], self.fileName, self.line, self.label, self.issue)


#Function that gets all of the files (and folders) in a folder
def getFiles(directory):
	#List all sub-directories and files
	fileList = []
	blacklisted = False

	for d in os.listdir(directory):
		d = directory + "/" + d #make the format actually work for our function calls

		#print d, os.path.isdir(d) #debug

		#if the "file" is a directory...
		if os.path.isdir(d) and not ".git" in d: #we never want .git files; excluded to prevent stdout pollution
			for file in getFiles(d): #recursively iterate through the subfolders
				fileList.append(file)

		#otherwise the file is indeed a file (excluding the current file, autoissue.py)
		#make sure our file isn't blacklisted before actually adding it to the list
		else:
			#iterate through our blacklist
			for black in blacklist:
				if black in d:
					blacklisted = True

			if not blacklisted:
				fileList.append(d)

			else:
				print "Excluded file (blacklist): ", d



	#return list of actual files to open
	return fileList



### NEW FUNCTIONS

def getIssues():
	issueList = []
	files =	getFiles(dir)


	for file in files:
		for fileIssues in findIssuesInFile(file):
			issueList.append(fileIssues)



	print "\n\n\n\n ISSUES TO BE ADDED TO THE REPO:"
	for issue in issueList:
		print issue.title, "\n", issue.issue, "in \n", issue.fileName, "on line ", issue.line, "with label(s): ", issue.label, "\n\n"


	return issueList

# returns a list of the Issues in this file
def findIssuesInFile(file):
	lineNumber = 0
	issueList = []

	with open(file, 'r') as f:
		data = f.readlines()

	print "Searching for issues in:", file, "(lines: {})".format(len(data))

	while lineNumber < len(data):
		issueString = ""
		if startToken in data[lineNumber] or "FIXME" in data[lineNumber]:
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
			issueList.append(parseIssueFromRawComment(issueString, startingLine, file))
		lineNumber += 1
	return issueList


# returns an Issue
def parseIssueFromRawComment(comment, line, file):
	data = {}
	#title
	#issueContent
	#lineNumber
	#fileName
	#label
	tags_regex = "\[(.*?)\]"
	r = re.compile(tags_regex)
	tags = r.findall(comment)

	# If no [title:] tag is specified, then the first line is autmatically the title
	for tag in tags:
		if ":" not in tag:
			# This is the issue number tag
			data['number'] = int(tag) # Should eventually check to be sure there are only numbers in here
		else:
			t, v = tag.split(":")
			#print "TAG:", t, "VALUE:", v
			if t.lower() == "title":
				title = v
			elif t.lower() == "label":
				labels = [x.strip() for x in v.split(",")]

	if title is None:
		title = comment.split("\n")[0]

	content = re.sub(tags_regex, "", comment)
	content = re.sub("(//(\s*)TODO)|(/\*(\s*)TODO)|(\*/)", "", content).strip()
	#print "CONTENT:", content
	issue = Issue(title, content, line, file, labels)
	issue.data = data
	return issue


def debug_add(base, addition):
	print base, "+", addition
	return base + addition

### END NEW FUNCTIONS




#Function which takes a file and returns a list of Issues
def lookForIssue(file):
	#local variables
	lineNumber = 1
	issueList = []

	with open(file) as f:
		print "Searching for ", startToken, " in: ", file
		for line in f:
			if startToken in line:
				iss = generateIssue(line, lineNumber, file)
				issueList.append(iss)
				lineNumber = 0;

			lineNumber += 1

	return issueList


#function that parses out the portion enclosed in the TODO ... ODOT in the string and returns the completed obj
def generateIssue(issueText, lineNumber, fileName):
	args = ["@title", "@label", "@iss_number"]
	label = None
	title = None
	number = None

	#search for any sort of arguments in the todo
	splitString = issueText.split(" ") #tokenize the input string to try to find args
	for arg in args:
		for token in splitString:
			if arg in token:
				if arg is "@title":
					title = token.split(":")[1]
					print "arg found! ", arg, ": ", title
				elif arg is "@label":
					label = token.split(":")[1]
					print "arg found! ", arg, ": ", label
				else:
					number = int(token.split(":")[1])
					print "arg found!", arg, ":", number


	startIndex = issueText.index(startToken) + len(startToken)
	endIndex = issueText.index(endToken)
	issue = Issue(title, issueText[startIndex:endIndex], lineNumber, fileName, label)
	issue.data['number'] = number
	return issue

#returns the list of issues in a specific directory (and all children), or "." by default
def getIssueList(dir = "."):
	#local variables
	issueList = []
	files =	getFiles(dir)


	for file in files:
		for issue in lookForIssue(file):
			issueList.append(issue)



	print "\n\n\n\n ISSUES TO BE ADDED TO THE REPO:"
	for issue in issueList:
		print issue.title, "\n", issue.issue, "in \n", issue.fileName, "on line ", issue.line, "with label(s): ", issue.label, "\n\n"


	return issueList

def injectNumber(issue, number):
	with open(issue.fileName, 'r') as file:
		data = file.readlines()

	lineNumber = issue.line - 1
	line = data[lineNumber]
	startIndex = line.index(startToken) + len(startToken)
	print "Before:", data[lineNumber]
	data[lineNumber] = data[lineNumber][:startIndex+1] + "@iss_number:" + str(number) + " " + data[lineNumber][startIndex:]
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


	#issueList = getIssueList()
	#createIssues(issueList, debug)

	issueList = getIssues()
	createIssues(issueList, debug)

if __name__ == "__main__":
    #main()
	comment = "/*TODO [title:Title][label:bug, wontfix][56] This is the issue thing*/"
	print parseIssueFromRawComment(comment, 0, "test")
