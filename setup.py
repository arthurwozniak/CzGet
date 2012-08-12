#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from shutil import copyfile as copy
import subprocess
import base64

def read_string():
	return raw_input()

if "czget.py" not in os.listdir("./"):
	print "Chyba! Pro instalaci se musíte přepnout do složky obsahující soubory programu"
	sys.exit(0)
home_folder = os.getenv("HOME")
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
	# Ask sor running a "setup wizard"
	print """Přejete si spustit průvodce pro vytvoření konfiguračního souboru?
Bez toho bude nutné upravit %s/.czget/config ručně...""" % home_folder
	if raw_input("Zadejte A/N [defaultně]: ").lower() == "a":
		file = open(home_folder+"/.czget/config", 'w')
		username = raw_input("Uživatelské jméno: ")
		while username == "": username = raw_input("Uživatelské jméno: ")
		file.write("USERNAME=%s\n" % username)
		password = raw_input("Heslo: ")
		while password == "": password = raw_input("Heslo: ")
		file.write("PASSWORD="+base64.b64encode(password)+"\n")
		downdir = raw_input("Složka pro stahování [defaultně '%s/']: " % home_folder)
		if downdir == "" or not os.path.isdir(downdir):
			downdir = home_folder
		file.write("DOWNDIR=%s\n" % downdir)
		speedlimit=raw_input("Limit stahování v B/s [0 = neomezeně]: ")
		if type(speedlimit) != type(0):
			speedlimit = 0
		file.write("SPEED_LIMIT=%d\n" % speedlimit)
		file.close()
	else:
		# Copy empty config file into program directory
		copy("./config", home_folder+"/.czget/config")
	# Copy script file into a created directory
	copy("./czget.py", home_folder+"/.czget/czget.py")
	# Make ~/.czget/czget.py executable
	os.system("chmod +x ~/.czget/czget.py")
	# Copy blessings module to program directory
	copy("./blessings.py", home_folder+"/.czget/blessings.py")
	# Create ~/.bashrc alias
	open(home_folder+"/.bashrc", 'a').write("\nalias czget='~/.czget/czget.py'")
	print "Instalace dokončena"
