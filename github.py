import requests
import json
import getpass
import os
import util
from autoissue import injectNumber
from urlparse import urljoin


API_URL = 'https://api.github.com'
SETTINGS = 'settings.williames' #settings file
HEADERS = {'Content-type':'application/json'}
TOKEN_KEY = 'auth_token'

def getToken():
	val = getValue(TOKEN_KEY)
	if val is not None:
		return val
	
	#generate a token
	username = raw_input('Github username: ')
	password = getpass.getpass('Github password: ')

	url = urljoin(API_URL, 'authorizations')
	payload = {'note' : 'auto-issue-creator', 'scopes' : ['repo']}
	r = requests.post(url, auth = (username, password), data = json.dumps(payload),)


	# TODO error handling

	if r.ok:
		token = json.loads(r.text or r.content)['token']
		if not addProperty(TOKEN_KEY, token):
			print "Could not write authorization token to settings file. Please add the following line to " + SETTINGS + ":\n" + "auth_token " + token
		return token

def getValue(key):
	if os.path.exists(SETTINGS):
		with open(SETTINGS) as f:
			for line in f:
				if key in line:
					return line.split(" ", 1)[1].strip(" \n")
	return None
		
def addProperty(key, value):
	with open(SETTINGS, "a+") as sett: # Will create the file if it does not exist
		sett.write(key + " " + value + "\n")
		return True

	return False


def getRepo():
	val = getValue("repo")

	if val is not None:
		return val # return the repo saved in the settings file

	# Get the active git repo
	with open('.git/config') as f:
		for line in f:
			if "url = " in line:
				r = line.split("=")[1].split("github.com/")[1].split("/")[1].replace(".git\n", "")
	
	# Add to our settings file
	if r:
		addProperty("repo", r)
		return r

def getOwner():
	val = getValue("owner")
	if val is not None:
		return val # return the owner saved in the settings file


	# Get the active git repo
	with open('.git/config') as f:
		for line in f:
			if "url = " in line:
				r = line.split("=")[1].split("github.com/")[1].split("/")[0]

	# Add to our settings file
	if r:
		addProperty("owner", r)
		return r


def createIssues(issues):
	beforeIssues = getIssueNumberList()
	afterIssues = []

	for issue in issues:
		if issue.data['number'] is not None:
			afterIssues.append(issue.data['number'])
		else:
			number = createIssue(issue)
			# inject iss_number tag into TODO comment
			autoissue.injectNumber(issue, number)

	util.debug_print("before issues:\n", str(beforeIssues), "after issues:\n", str(afterIssues))

	removeIssuesInDiff(beforeIssues, afterIssues)


def createIssue(issue):
	print "CREATING ISSUE: ", issue.issue, " in file: ", issue.fileName, " on line: ", issue.line, " with label: ", issue.label

	title = "{} : {}".format(issue.fileName, issue.line)
	body = issue.issue
	assignee = getOwner()
	labels = [] if issue.label is None else [issue.label]
	
	data = {"title" : title, "body" : body, "state" : "open", "labels" : labels}
	
	url = urljoin(API_URL, "/".join(["repos", getOwner(), getRepo(), "issues"]))
	url = url + "?access_token=" + getToken()

	util.debug_print("Issue create request url =", url)

	r = requests.post(url, data = json.dumps(data), headers = HEADERS)

	if r.ok:
		print "SUCCESS"
		j = json.loads(r.text or r.content)
		return j['number']
	else:
		print "Not OK"
		print r.text
		print "{}:{}".format("Status", r.status_code)



def getIssueNumberList():
	list = []

	url = urljoin(API_URL, "/".join(["repos", getOwner(), getRepo(), "issues"]))
	url = url + "?access_token=" + getToken()

	r = requests.get(url)

	if r.ok:
		j = json.loads(r.text or r.content)
		for issue in j:
			list.append(issue['number'])
		return list
	#TODO: error handling
	else:
		print "Not OK"
		print r.text
		print "{}:{}".format("Status", r.status_code)
		return None

def removeIssuesInDiff(beforeIssues, afterIssues):
	def diff(a, b):
		b = set(b)
		return [aa for aa in a if aa not in b]
	
	data = {"state" : "closed"}
	
	for issue in diff(beforeIssues, afterIssues):
		url = urljoin(API_URL, "/".join(["repos", getOwner(), getRepo(), "issues", str(issue)]))
		url = url + "?access_token=" + getToken()
		r = requests.post(url, data = json.dumps(data), headers = HEADERS)
		if r.ok:
			print "Closed issue", issue