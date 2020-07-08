import sys
import datetime
import re
import urllib.parse
import configparser
import requests
from bs4 import BeautifulSoup

config = configparser.ConfigParser() # Настройки
config.read("settings.ini")

baseurl = config["MySpace"]["baseurl"]

# Бот
s = requests.session()
headers = {'content-type': 'application/x-www-form-urlencoded'}

def logIn(login, password):
	payload_login = "username={}&password={}&login=".format(urllib.parse.quote(login), urllib.parse.quote(password))
	s.request("POST", baseurl + "/login.php", data=payload_login, headers=headers)

def getBlogs(userId):
	r = s.request("GET", baseurl + "/blog.php?id={}".format(userId))
	bs = BeautifulSoup(r.text, features="html.parser")
	cropLen = len("/blog.php?id={}&b=".format(userId))
	return [int(a.get("href")[cropLen:])
		for a in bs.select('div.box.blog>a')]

def postBlog(title, text):
	payload_blog = "user=1&title={}&corpus={}".format(urllib.parse.quote(title), urllib.parse.quote(text))
	s.request("POST", baseurl + "/blogWrite.php", data=payload_blog, headers=headers)

def editBlog(userId, blogId, title, text):
	payload_blog = "user={}&title={}&corpus={}".format(userId, urllib.parse.quote(title), urllib.parse.quote(text))
	s.request("POST", baseurl + "/blogUpdate.php?id={}&b={}".format(userId, blogId), data=payload_blog, headers=headers)

def removeBlog(userId, blogId):
	s.request("GET", baseurl + "/blogDelete.php?id={}&b={}".format(userId, blogId))

def acceptFwiendRequest(fwiendId):
	s.request("GET", baseurl + "/accept.php?id={}".format(fwiendId))

def getFwiendsRequests(id):
	r = s.request("GET", baseurl + "/requests.php?id={}".format(id))
	bs = BeautifulSoup(r.text, features="html.parser")
	return [int(a.get("href")[len("index.php?id="):])
		for a in bs.select('div.friendRequests>a')]

def logOut():
	s.post(baseurl + "/logout.php")

def saveConfig():
	with open('settings.ini', 'w') as configfile:
		config.write(configfile)

def shutDown():
	saveConfig()
	logOut()
	sys.exit(0)

logIn(config["MySpace"]["email"], config["MySpace"]["password"])

for fwiend in getFwiendsRequests(config["MySpace"]["id"]):
	print("New fwiend request:", fwiend)
	acceptFwiendRequest(fwiend)

# Постинг лягух ниже
posted_today = int(config["General"]["posted_today"]) == 1
if (datetime.datetime.today().weekday() != 2): # если не среда
	print("It's not wednesday, my dudes... Not yet!")
	if (posted_today): # если лягуху вчера запостили то можно снять флаг
		config["General"]["posted_today"] = str(0)
	shutDown()
elif (posted_today): # если среда, но лягушку уже постили
	print("It's wednesday, my dudes, but I've send a frog or toad today!")
	shutDown()

print("It's wednesday, my dudes! AAAAAAAAAAAAAAAAAAAAAAAAAAAAA!")

if (len(getBlogs(config["MySpace"]["id"])) == int(config["MySpace"]["max_posts"])):
	removeBlog(config["MySpace"]["id"], config["MySpace"]["delete_on_overflow"])

content_line = ""
with open("posts.txt", "r") as f:
	lines = f.readlines()
	content_line = lines.pop(int(config["General"]["last_post"]))

config["General"]["last_post"] = str(int(config["General"]["last_post"]) + 1)

post_title = "Wednesday post №{}".format(config["General"]["last_post"])

with open(config["General"]["archive"], "a") as f:
	f.write("{} ({}): {}".format(post_title, datetime.datetime.now().strftime("%H:%M %a %b %d %Y"), content_line))

postBlog(post_title, content_line)

config["General"]["posted_today"] = str(1)
shutDown()
