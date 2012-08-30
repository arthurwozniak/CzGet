#!/usr/bin/env python
# -*- coding: utf-8 -*-
# CzGet - downloading from czshare.com using CLI
# version 0.4
# Created by Kamil Hanus (ja [ at ] kamilhanus [ dot ] cz)
# Published under CC BY-NC-SA 3.0 http://creativecommons.org/licenses/by-nc-sa/3.0/

import os
import sys, signal
from urllib2 import HTTPError, URLError
from blessings import Terminal
import time
import optparse
import requests
from pyquery import PyQuery as pq
from base64 import b64decode, b64encode
import ConfigParser

def get_time():
	 return time.strftime("%Y-%m-%d %H:%M:%S")

def recalculate_size(value):
	if value >= 10**9: return "G", int(round(value/(2.0**30)))
	elif value >= 10**6: return "M", int(round(value/(2.0**20)))
	elif value >= 10**3: return "K", int(round(value/(2.0**10)))
	else: return "B", value

class status_bar_updater:
	
	def update_remaining_time(self,size,speed,downloaded,IsDownloadFinished, total_time):
		if not IsDownloadFinished:
			size=int(size)
			size_left=size-downloaded
			if speed < 1: speed = 1
			seconds=int(size_left/speed)
		else: seconds = int(total_time)
		
		def countIT(factor,seconds,shortcuts):
			"""This function obtains factor, which depends on value of 'seconds' variable. 
			   A 'shortcut' variable provides a letters for meaning of remaining time."""
			higher=0
			lower=0
			while seconds > factor:
				higher+=1
				seconds-=factor
			if seconds > 0 and factor > 60: lower=seconds/(factor/60)
			else: lower = seconds
			if IsDownloadFinished: return "%sza %d%s%d%s" % ((8-len(str(higher))-len(str(lower)))*" ",higher, shortcuts[0], lower, shortcuts[1])
			else: return " zbyva%s%d%s%s%d%s" % ((3-len(str(higher)))*" ",higher,shortcuts[0],(2-len(str(lower)))*" ", lower,shortcuts[1])
		
		if seconds>86400: #seconds are more than 24 hours :-O
			return countIT(86400, seconds,("d","h"))
		elif seconds>3600: #seconds are more than 60 minutes
			return countIT(3600, seconds,("h","m"))
		else: #seconds are more than 60 seconds
			return countIT(60, seconds,("m","s"))
	def update_speed(self,time1,time2,size):
		if time2-time1 >0:
			current_speed=int(size/(time2-time1))
		else:
			current_speed = size
		returned_value=current_speed
		unit, current_speed=recalculate_size(current_speed)
		speed="%d%s/s" % (int(current_speed),unit)
		return returned_value, speed
	def update_percentage(self, current_size, total_size):
		if total_size != 0: percentage=int((current_size/(total_size*1.0))*100)
		else: percentage=0
		if percentage > 100: percentage = 100 # :o)
		return percentage
		
	def update_progress(self, percentage, finished_size, total_size):
		space=self.term.width-41
		plus = int(round(self.update_percentage(finished_size, total_size)*(space/100.0),0))
		rows=int(round(percentage*(space/100.0),0))		
		if rows < 0: rows = 0
		if rows == 0: rows = plus
		return "[%s%s%s%s]" % (plus*"+", (rows-plus)*"=", ">", (space-rows)*" ")
		
	def update_current_size(self, size):# mezi kazde tri cislice prida mezeru
		size = str(size)
		divide_by = len(size)/3
		new_size = ""
		if not divide_by: new_size=size
		else:
			while divide_by:
				new_size="%s %s" % (size[-3:],new_size)
				size=size[:-3]
				divide_by-=1
				if len(size)<3:
					new_size="%s %s" % (size,new_size)
		return " %s%s " % (new_size, (13-len(new_size))*" ")		
		
	def __init__(self, total_size, finished_size, currently_downloaded, temporary_size, time1, time2, status, term, filename):
		""" tota_size = full size
			finished size = size of file before dofnloading ( only if continue option is true
			currently_donloaded = size of download since program start
			temporary_size = size of downloaded before statusbar refresh
			time1 = time of last refresh of statusbar if status != finished, else it is time whed downloading started
			time2 = time just before refresh of statusbar if status != finished, else it is time whed downloading finished
			term = self.term of CzShare class, otherwise statusbar resresh will not work """
		self.term = term
		if status == "init":
			self.speed_list=[1,1,1,1,1]
			current_percentage = 0
			current_speed = 0
			current_speed_str="0B/s"
			remaining_time = " zbyva NaN"
		else:
			current_percentage = self.update_percentage(currently_downloaded + finished_size, total_size) 	 	
			current_speed = self.update_speed(time1,time2,temporary_size)
			current_speed_str = current_speed[1]
			current_speed = current_speed[0]
			if status == "finished":
				remaining_time = self.update_remaining_time(total_size, current_speed, currently_downloaded, True, (time2-time1))
			else:
				remaining_time = self.update_remaining_time(total_size-finished_size, current_speed, currently_downloaded, False, 0)
			
		updated_current_size = self.update_current_size(currently_downloaded + finished_size)
		progress_bar = self.update_progress(current_percentage, finished_size, total_size)
		current_percentage_string = "%s%d%s" % ((3-len(str(current_percentage)))*" ",current_percentage,"%")
		current_speed_str = "%s%s" % ((6-len(current_speed_str))*" ", current_speed_str)
		remaining_time_str = "%s%s" % ((13-len(remaining_time))*" ", remaining_time)
		print self.term.move_up + (current_percentage_string + progress_bar + updated_current_size + current_speed_str + remaining_time_str)
		if status == "finished":
			print "%s (%s) - „%s“ uložen [%s]" % (get_time(), self.update_speed(time1, time2, total_size)[1], filename, total_size)
class CZshare():
	
	def changeConfig(self, config_path, new_name, new_pass, new_dir, new_limit):
		newConfig = ConfigParser.RawConfigParser()
		newConfig.read(config_path)
		if new_pass:new_pass=b64encode(new_pass)
		valueList = {"username":new_name, "password":new_pass, "downdir": new_dir, "speed_limit":new_limit}
		for item in valueList:
			if valueList[item] or valueList[item] == 0:
				newConfig.set("CzGet", "%s" % item, "%s" % valueList[item])
		with open(config_path, 'wb') as configfile:
			newConfig.write(configfile)

	def showCredit(self, credit):
		print "Zbývající kredit: %.1lf GB" % (credit/(10.0**9))
		
	def delete_file_from_queue(self, code):
		data={"sm_[]":code, "smazat_profi":"Smazat"} # makes data dict including code enabling file delete
		response = requests.post("https://czshare.com/index.php", data=data, cookies=self.cookies) # sends request for file delete
		if response.content.find("Odkazy na soubory byly úspěšně smazány.") != -1: return True # If file was succesfully deleted, return True
		else: return False # Else return False
		
	def get_session_cookies(self):
		login_data={'trvale': 'on', 'login-name': self.username, 'login-password': self.password, 'Prihlasit': 'Přihlásit SSL'} # Dict of login data
		cookies = requests.post("https://czshare.com/index.php", data=login_data) #Post login data to obtain response including seassion cookies
		return cookies.cookies, cookies.text # returns session cookies and page source code
		
	def recalculate_credit(self, credit_string):
		""" From credit string removes last two unit chars. Also replaces "," for "." and converts value into bytes."""
		credit = int(float("%s.%s" % (credit_string.split(",")[0], credit_string.split(",")[1][:-2]))*(10**9))
		return credit
		
	def signal_handler(signal, frame):
		sys.exit(0)
	signal.signal(signal.SIGINT, signal_handler)

	def check_link(self,url_address):
		file_response = requests.get(url_address, cookies=self.cookies) # download file page with cookies
		# If returned code is 200 (page is OK) and file is available, returns True and page source as PyQuery object
		if file_response.status_code == 200 and pq(file_response.content)("div#parameters") != []:
			return True, pq(file_response.content)
		else: return False, None
	def check_terminal_size(self):
		while self.term.height<20 or self.term.width<80:
			with self.term.location(0,0):
				print "Minimální velikost okna je 80x20 znaků"
				time.sleep(.5)
				self.term.location(0,0)
				for x in range(self.term.height):
					print self.term.width*" "
	def init_parser(self,HOME):
		self.parser = optparse.OptionParser(" %prog [prepinac] [parametr]")
		self.parser.add_option("-f", "--file", dest="file_path",
						  default=None, type="string",
						  help="Cesta k souboru s URL adresami")
		self.parser.add_option("-u", "--url", dest="url_address", default=None,
						  type="string", help="Adresa souboru ke stazeni")
		self.parser.add_option("-d", "--directory", dest="directory", default=None,
						  type="string", help="Cilova slozka")
		self.parser.add_option("-l", "--login", dest="user_name", default=None,
						  type="string")
		self.parser.add_option("-p", "--password", dest="password", default=None,
						  type="string")
		self.parser.add_option("-c", "--config_file", dest="config", default=HOME+"/.czget/config",
						  type="string", help="Cesta ke konfiguracnimu souboru")
		self.parser.add_option("-C", "--credit", dest="credit", default=None,
						  action="store_true", help="Zobrazit zbyvajici kredit")
		self.parser.add_option("-s", "--speed-limit", dest="speed_limit", default=None,
						  type="int", help="Omezi rychlost stahovani na danou hodnotu. Neomezene = 0")
		self.parser.add_option("-D", "--disable-speed-limit", dest="speed_limit_disable", default=False,
						  action="store_true", help="Zakaze omezeni rychlosti")
		self.parser.add_option("-O", "--output-file", dest="output_file", default=None,
						  type="string", help="Nazev vystupniho souboru. Nelze pouzit pri stahovani ze souboru.")
		self.parser.add_option("--change-username", dest="new_username", default=None,
						  type="string", help="Nove uzivatelske jmeno.")
		self.parser.add_option("--change-password", dest="new_password", default=None,
						  type="string", help="Nove heslo.")
		self.parser.add_option("--change-directory", dest="new_directory", default=None,
						  type="string", help="Nova slozka pro ukladani.")
		self.parser.add_option("--change-limit", dest="new_limit", default=None,
						  type="int", help="Nova hodnota omezeni rychlosti.")
		self.parser.add_option("--continue", dest="resume_download", default=False,
						  action="store_true", help="Pokracovat ve stahovani pozastavenych souboru.")
		(self.options, self.args) = self.parser.parse_args()
	def parse_urls(self):
		if self.filename:
			filename=re.sub("~/",self.home+"/",self.filename)
			if os.path.isfile(filename):
				self.content=open(filename,'r').readlines()
				x=0
				for x,i in enumerate(self.content):self.content[x]=re.sub("\n","",i)
			else:
				print "CHYBA - vstupní soubor neexistuje!"
				sys.exit(0)
		else: self.content=[self.url_address]

	def test_login(self):
		sentence = "--%s-- Testuji prihlasovaci udaje... " % get_time()
		print sentence
		self.cookies, login_response=self.get_session_cookies() # Get cookies and source code of returned page
		login_response = pq(login_response)	# Makes pq object from returned page source
		# Tries to fetch user ID on returned page
		try:
			int(login_response("a.btn")("span")[1].text.split(":")[1][1:])
			login_success = True
		except:
			login_success = False
		if login_success:
			print self.term.move_up + sentence + "OK"
			self.credit=self.recalculate_credit(login_response("div.credit")("strong")[0].text)
		else:
			print self.term.move_up + sentence + "chyba"
			sys.exit(0)	
	def download_file(self,url_address):
		print "--%s-- %s" % (get_time(), url_address)
		print "Testuje se dostupnost souboru..."
		file_availability, file_page_content = self.check_link(url_address)
		if file_availability:
			print self.term.move_up + "Testuje se dostupnost souboru... OK"
			nazev=file_page_content("div#parameters")("a")[0].text # Gets file name from <a> in div with id #parameters
			file_code=file_page_content.find("input")[3].value
			file_id=file_page_content.find("input")[2].value
			
			file_content=requests.post("https://czshare.com/profi_down.php", data={"id":file_id, "code":file_code}, cookies = self.cookies, prefetch=False)
			finished_size = 0
			currently_downloaded = 0
			total_size = int(file_content.headers["content-length"])
			if "error.php" in file_content.url:
				print "Soubor není momentálně dostupný. Zkuste to později."
			else:
				if self.resume_download and os.path.isfile("%s/%s" % (self.directory, nazev)):
					self.delete_file_from_queue(file_content.url.split("&")[1][4:])
					finished_size = os.path.getsize("%s/%s" % (self.directory, nazev))
					if total_size > finished_size:
						file_content=requests.post("https://czshare.com/profi_down.php", data={"id":file_id, "code":file_code}, cookies = self.cookies,
						prefetch=False, headers = {"Range" : "bytes=%d-%s" % (finished_size, str(total_size)) })
				else: self.resume_download = False
				# Delete file from queue
				if self.delete_file_from_queue(file_content.url.split("&")[1][4:]):
					print "Soubor byl smazán z fronty.\n"
				else: print "Soubor nelze odstranit z fronty.\n"
				download_size=int(file_content.headers["content-length"])
				speedShort=recalculate_size(total_size)
				if self.resume_download:
					# calculate full size
					speedShort1=recalculate_size(download_size)
					print "Délka: %d (%s%s), %s (%s%s) zbývá [%s]" % (total_size, speedShort[1], speedShort[0], download_size, speedShort1[1], speedShort1[0], file_content.headers["content-type"])
				else:	
					print "Délka: %d (%d%s) [%s]" % (total_size, int(speedShort[1]), speedShort[0], file_content.headers["content-type"])
				if download_size <= self.credit:
					if self.url_address and self.output_file_name:
						nazev = self.output_file_name
					nazev = nazev.encode("utf-8")
					open_method = 'wb'
					if self.resume_download: open_method = 'ab'
					file=open("%s/%s" % (self.directory, nazev), open_method)
					print "Ukládám do: „%s/%s“\n\n" % (self.directory,nazev)
					temporary_size=0
					# Workaround for modified files which size si bigger than size of file on server.
					if download_size < 0: download_size = total_size
					status_bar_updater(total_size, finished_size, currently_downloaded, temporary_size, 0, 0, "init", self.term, None)
					start_of_downloading=round(time.time(),3)
					start_time=round(time.time(),3)
					if finished_size < total_size:
						end_time=0
						temporary_size=0
						self.speed_list=[0,0,0,0,0]
						read_bytes=20
						if self.speed_limit_enable:
							if read_bytes > self.speed_limit: read_bytes = self.speed_limit
							limit_start_time=round(time.time(),3)
							limit_size=0
						tmp = file_content.raw.read(read_bytes)
						while (tmp):
							file.write(tmp)
							file.flush()
							currently_downloaded+=len(tmp)
							temporary_size+=len(tmp)
							current_time=round(time.time(),3)
							if((current_time-start_time)>0.2):
								status_bar_updater(total_size, finished_size, currently_downloaded, temporary_size, start_time, current_time, 0, self.term, None)
								temporary_size=0
								start_time=round(time.time(),3)
							if self.speed_limit_enable:
								limit_size +=len(tmp)
								limit_stop_time = time.time()
								if limit_size >=self.speed_limit and (limit_stop_time-limit_start_time)<1.0:
									time.sleep(1-(limit_stop_time - limit_start_time))
									limit_size = 0
									limit_start_time=time.time()
							tmp = file_content.raw.read(read_bytes)# RasPi was limited by this value to down speed 10K/s when reading 8B, so there is a hypotetic ratio 1200
					
					end_of_downloading=round(time.time(),3)
					file.close()
					status_bar_updater(total_size, finished_size, currently_downloaded, temporary_size, start_of_downloading, end_of_downloading, "finished", self.term, nazev)
				else:
					print "--%s-- CHYBA : Nemáte dostatečný kredit\n" % get_time()
		else: print "--%s-- CHYBA 404: Not found\n" % get_time()
	def __init__(self):
		self.home=os.getenv("HOME")
		self.term = Terminal()
		self.check_terminal_size()
		self.init_parser(self.home)
		# Change config file if needed
		self.changeConfig(self.options.config, self.options.new_username, self.options.new_password,
							self.options.new_directory, self.options.new_limit)
		self.filename=self.options.file_path
		self.url_address=self.options.url_address
		self.speed_limit=self.options.speed_limit
		self.output_file_name = self.options.output_file
		if self.filename and self.url_address:
			self.parser.error("Nelze zaroven zvolit url adresu a vstupni soubor")
		# Set path to config file [ /home/username/.czget/config setted defaultly]
		if os.path.isfile(self.options.config):
			self.config = self.options.config
		else:
			self.config = "%s/.czget/config" % self.home
		# Initialize ConfigParser
		config = ConfigParser.RawConfigParser()
		# Open config file
		config.read(self.config)
		# Get login values from config file
		self.username = config.get("CzGet", "username")
		self.password = b64decode(config.get("CzGet", "password"))
		if self.options.user_name:
			self.username = self.options.user_name
		if self.options.password:
			self.password = self.options.password
		self.speed_limit_enable = type(self.speed_limit) == int
		if not self.options.speed_limit_disable and not self.speed_limit:
			if self.speed_limit == None and config.get("CzGet", "speed_limit"):
				self.speed_limit = config.get("CzGet", "speed_limit")
			if type(self.speed_limit) != int:
				self.speed_limit = 0
			if self.speed_limit > 0:
				self.speed_limit_enable = True
		self.resume_download = self.options.resume_download
		if self.options.directory and os.path.isdir(self.options.directory):
			self.directory = self.options.directory
			if self.directory[-1:] == "/":
				self.home=self.directory[:-1]
		else:
			if os.path.isdir(config.get("CzGet", "downdir")):
				self.directory = config.get("CzGet", "downdir")
			else: self.directory=self.home
		self.parse_urls()
		print "CzGet, stahovani z czshare.com pomoci CLI"
		self.test_login()
		if self.options.credit:
			self.showCredit(self.credit)
		if not self.filename and not self.url_address:
			sys.exit(0)
		for i in self.content:
			self.download_file(i)

if __name__ == '__main__':
	CZshare()

