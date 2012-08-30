#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from shutil import copyfile as copy
import subprocess
import base64
import ConfigParser
from pwd import getpwnam
from getpass import getpass

def read_string():
	return raw_input()

if "czget.py" not in os.listdir("./"):
	print "Chyba! Pro instalaci se musíte přepnout do složky obsahující soubory programu"
	sys.exit(0)
home_folder = os.getenv("HOME")
uid = getpwnam(home_folder.split("/")[2])[2]
gid = getpwnam(home_folder.split("/")[2])[3]
if os.path.isdir("%s/.czgest" % home_folder):
	print "Aplikace je již nainstalována. Instalace se ukončí..."
	sys.exit(0)
else:
	# Check if pip is installed
	if os.path.isfile("/bin/pip") or os.path.isfile("/usr/bin/pip"):
		print "python-pip je nainstalován"
		# Install the requirements
		os.system("pip install -r requirements.pip")
	else:
		print "Pro instalaci závislostí je třeba doinstalovat python-pip. Nainstalujtejej a spusťte tento skript znovu, nebo doinstalujte závislosti ručně."
	# Make a program folder
	if not os.path.isdir("%s/.czget" % home_folder):
		os.mkdir(home_folder+"/.czget")
	# Initialize ConfigParser and make default file structure
	config = ConfigParser.RawConfigParser()
	config.add_section("CzGet")
	config.set("CzGet", "USERNAME", "")
	config.set("CzGet", "PASSWORD", "")
	config.set("CzGet", "SPEED_LIMIT", 0)
	config.set("CzGet", "DOWNDIR", "%s" % home_folder)
	# Ask sor running a "setup wizard"
	print """Přejete si spustit průvodce pro vytvoření konfiguračního souboru?
Bez toho bude nutné upravit %s/.czget/config ručně...""" % home_folder
	if raw_input("Zadejte A/N [defaultně = N]: ").lower() == "a":
		username = raw_input("Uživatelské jméno: ")
		while username == "": username = raw_input("Uživatelské jméno: ")
		config.set("CzGet", "USERNAME", username)
		password = getpass("Heslo: ")
		while password == "": password = raw_input("Heslo: ")
		config.set("CzGet", "PASSWORD", base64.b64encode(password))
		downdir = raw_input("Složka pro stahování [defaultně '%s/']: " % home_folder)
		if downdir != "" or os.path.isdir(downdir):
			config.set("CzGet", "DOWNDIR", downdir)
		speedlimit=raw_input("Limit stahování v B/s [0 = neomezeně]: ")
		if type(speedlimit) == int:
			config.set("CzGet", "SPEED_LIMIT", speedlimit)
		with open(home_folder+"/.czget/config", 'wb') as configfile:
			config.write(configfile)	
	else:
	# Create empty config file
		with open(home_folder+"/.czget/config", 'wb') as configfile:
			config.write(configfile)
			
	# Copy script file into a created directory
	copy("./czget.py", home_folder+"/.czget/czget.py")
	# Make ~/.czget/czget.py executable
	os.system("chmod +x ~/.czget/czget.py")
	# Copy blessings module to program directory
	copy("./blessings.py", home_folder+"/.czget/blessings.py")
	# Create ~/.bashrc alias
	open(home_folder+"/.bashrc", 'a').write("\nalias czget='~/.czget/czget.py'")
	# Change permissions to whole folder
	for dir, subdirs, files in os.walk("%s/.czget" % home_folder):
		os.chown(dir, uid, gid)
		for item in subdirs:
			os.chown(os.path.join(dir, item), uid, gid)
		for item in files:
			os.chown(os.path.join(dir, item), uid, gid)
	print "Instalace dokončena"
