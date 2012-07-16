#!/usr/bin/env python
# -*- coding: utf-8 -*-
# CzGet - downloading from czshare.com using CLI
# Created by Kamil Hanus (ja [ at ] kamilhanus [ dot ] cz)
# Published under CC BY-NC-SA 3.0 http://creativecommons.org/licenses/by-nc-sa/3.0/

import re
import mechanize
import os
import sys, signal
from urllib2 import HTTPError, URLError
from blessing import Terminal
import time
import optparse


class CZshare():
	def delete_file_from_queue(self, code):
		self.br.open("http://czshare.com")
		self.br.select_form(nr=0)
		self.br["sm_[]"]=[code]
		self.br.submit()
	def get_time(self):
		 return time.strftime("%Y-%m-%d %H:%M:%S")
	def signal_handler(signal, frame):
		sys.exit(0)
	signal.signal(signal.SIGINT, signal_handler)
	def get_size(self, response):
		try:
			if int(response.info()["Content-Length"]) > 0:
				return response.info()["Content-Length"]
			else: return self.velikost(response)
		except: return 1
	def check_file(file_link):
		test=re.search("Stáhnout", file_link)
		print "test"+test
		if test != "Stáhnout":
			return False
		else:
			
			return True
	def check_links(self,test_response):
		if re.search('Stáhnout', test_response):
			return True
		else:
			return False
	def check_terminal_size(self):
		while self.term.height<20 or self.term.width<80:
			with self.term.location(0,0):
				print "Minimální velikost okna je 80x20 znaků"
				time.sleep(.5)
				self.term.location(0,0)
				for x in range(self.term.height):
					print self.term.width*" "
	def init_parser(self):
		self.parser = optparse.OptionParser(" %prog [prepinac] [parametr]")
		self.parser.add_option("-f", "--file", dest="file_path",
						  default=None, type="string",
						  help="Cesta k souboru s URL adresami")
		self.parser.add_option("-u", "--url", dest="url_address", default=None,
						  type="string", help="Adresa souboru ke stazeni")
		self.parser.add_option("-d", "--directory", dest="directory", default=None,
						  type="string", help="Cilova slozka")
		self.parser.add_option("-l", "--login", dest="uzivatelske_jmeno", default=None,
						  type="string")
		self.parser.add_option("-p", "--password", dest="heslo", default=None,
						  type="string")
		(self.options, self.args) = self.parser.parse_args()
	def parse_urls(self):
		if self.filename!=None:
			filename=re.sub("~/",self.HOME+"/",self.filename)
			if os.path.isfile(filename)==True:
				linksfile=open(filename,'r')
				self.content=linksfile.readlines()
				x=0
				for i in self.content:
					self.content[x]=re.sub("\n","",i)
					x+=1
				linksfile.close()
				return 1
				
			else:
				print "CHYBA - vstupní soubor neexistuje!"
				sys.exit(0)
		else:
			self.content=[self.url_address]
			return 0
	def update_remaining_time(self,size,speed,downloaded,finished, total_time):
		if finished==0:
			size=int(size)
			size_left=size-downloaded
			seconds=int(size_left/speed)
		else: seconds = int(total_time)
		
		if seconds>86400: #seconds are more than 24 hours :-O
			days=0
			hours=0
			while seconds > 86400:
				days+=1
				seconds-=86400
			if seconds>0:
				hours=int(seconds/3600)
			if finished==0: return " zbyva%s%dd%s%dh" % ((3-len(str(days)))*" ",days,(2-len(str(hours)))*" ", hours)
			else: return "%sza %dd%dh" % ((8-len(str(days))-len(str(hours)))*" ",days, hours)
		elif seconds>3600: #seconds are more than 60 minutes
			hours=0
			minutes=0
			while seconds > 3600:
				hours+=1
				seconds-=3600
			if seconds>0:
				minutes=int(seconds/60)
			if finished==0: return " zbyva%s%dh%s%dm" % ((3-len(str(hours)))*" ",hours,(2-len(str(minutes)))*" ", minutes)
			else: return "%sza %dh%dm" % ((8-len(str(hours))-len(str(minutes)))*" ",hours, minutes)
		elif seconds<=3600: #seconds are more than 60 seconds
			minutes=0
			secondas=0
			while seconds > 60:
				minutes+=1
				seconds-=60
			if seconds>0:
				secondas=seconds
			if finished==0: return " zbyva%s%dm%s%ds" % ((3-len(str(minutes)))*" ",minutes,(2-len(str(secondas)))*" ", secondas)
			else: return "%sza %dm%ds" % ((8-len(str(minutes))-len(str(secondas)))*" ",minutes, secondas)
	def update_speed(self,time1,time2,size):
		if time2-time1 >0:
			current_speed=int(size/(time2-time1))
		else:
			current_speed = size
		self.speed_list.pop(0)
		self.speed_list.append(current_speed)
		speeds=0
		for i in self.speed_list:
			speeds+=i
		current_speed=round(speeds/5.0,1)
		returned_value=current_speed
		if current_speed>=10**6:
			current_speed=round(current_speed/2**20,1)
			unit="M"
		elif current_speed>=10**3:
			current_speed=round(current_speed/2**10,1)
			unit="K"
		else:
			unit="B"
		speed="%d%s/s" % (int(current_speed),unit)
		return returned_value, speed
	def update_progress(self, percentage):
		space=self.term.width-41
		rows=int(round(percentage*(space/100.0),0))
		return "[%s%s%s]" % (rows*"=", ">", (space-rows)*" ")
	def update_current_size(self, size):# mezi kazde tri cislice prida mezeru
		size = str(size)
		divide_by=len(size)/3
		new_size=""
		if divide_by==0:
			new_size=size
		else:
			while divide_by > 0:
				new_size="%s %s" % (size[-3:],new_size)
				size=size[:-3]
				divide_by-=1
				if len(size)<3:
					new_size="%s %s" % (size,new_size)
		return " %s%s " % (new_size, (13-len(new_size))*" ")		
	def update_percentage(self, current_size, total_size):
		if total_size != 0:
			percentage=int((current_size/(int(total_size)*1.0))*100)
		else: percentage=0
		if percentage > 100: percentage = 100 #can't get the right size of file
		return percentage
	def test_login(self):
		time = self.get_time()
		sentence = "--%s-- Testuji prihlasovaci udaje... " % time
		print sentence
		#prihlaseni
		self.br=mechanize.Browser()
		try:
			self.br.open("http://czshare.com/index.php?pg=prihlasit")
		except HTTPError, e:
				print "Nastala chyba ",e.code
				sys.exit(0)
		except URLError, e:
				print "Nastala chyba ",e.reason
				sys.exit(0)
		
		self.br.select_form(nr=0)
		self.br["login-name"]=self.username
		self.br["login-password"]=self.password
		odpoved=self.br.submit()
		if re.search("Fronta", odpoved.read()):
			print self.term.move_up + sentence + " OK"
		else:
			print self.term.move_up + sentence + " error"
			sys.exit(0)	
	def good_night(self,start_time, end_time,size,name):
		total_time=int(round(end_time-start_time,1))
		if total_time >0: average_speed = size/total_time
		else: average_speed = 0
		print "%s (%dKB/s) - „%s“ uložen" % (self.get_time(),average_speed,name)
		
			
		self.update_remaining_time(1,1,1,1,total_time)
	def update_info_bar(self, size, current_size, temporary_size, time1, time2, status):
		if status == "init":
			current_percentage = 0
			current_speed = 0
			current_speed_str="0B/s"
			remaining_time = " zbyva NaN"
		else:
			current_percentage = self.update_percentage(current_size, size)
			current_speed = self.update_speed(time1,time2,temporary_size)
			current_speed_str = current_speed[1]
			current_speed = current_speed[0]
			if status == "finished":
				remaining_time = self.update_remaining_time(size, current_speed, current_size, 1, (time2-time1))
			else:
				remaining_time = self.update_remaining_time(size, current_speed, current_size, 0, 0)
			
		updated_current_size = self.update_current_size(current_size)
		progress_bar = self.update_progress(current_percentage)
		current_percentage_string = "%s%d%s" % ((3-len(str(current_percentage)))*" ",current_percentage,"%")
		current_speed_str = "%s%s" % ((6-len(current_speed_str))*" ", current_speed_str)
		remaining_time_str = "%s%s" % ((13-len(remaining_time))*" ", remaining_time)
		print self.term.move_up + (current_percentage_string + progress_bar + updated_current_size + current_speed_str + remaining_time_str)
	def download_file(self,url_address):
		print "--%s-- %s" % (self.get_time(), url_address)
		try:
			a=self.br.open(url_address)
		except HTTPError, e:
			print "Nastala chyba ",e.code
			sys.exit(0)
		except URLError, e:
				print "Nastala chyba ",e.reason
				sys.exit(0)
		print "Testuje se dostupnost souboru..."
		if self.check_links(self.br.response().read())==True:
			print self.term.move_up + "Testuje se dostupnost souboru... OK"
			nazev=re.search(r"<h1>*>([^>]*)", self.br.response().read()).group(1).split("<span")[0]
			self.br.select_form(nr=1)
			stahovani=self.br.submit()
			size=self.get_size(self.br.response())
			if int(size)>2**30:
				print "Délka: %s (%.1lfG) [%s]" % (size, int(size)/(2.0**30), self.br.response().info()["content-type"].split(";")[0])
			elif int(size)>2**20:
				print "Délka: %s (%.1lfM) [%s]" % (size, int(size)/(2.0**20), self.br.response().info()["content-type"].split(";")[0])
			elif int(size)>2**10:
				print "Délka: %s (%.1lfK) [%s]" % (size, int(size)/(2.0**10), self.br.response().info()["content-type"].split(";")[0])
			else:
				print "Délka: %s (%.1lfB) [%s]" % (size, int(size), self.br.response().info()["content-type"].split(";")[0])
			if self.downloadingToDir==True:
				print "Ukládám do: „%s%s“\n\n" % (self.options.directory,nazev)
			else:
				print "Ukládám do: „./%s“\n\n" % nazev
			current_size=0
			temporary_size=0	
			kod=self.br.geturl().split("&")[1][4:]
			soubor=open(self.HOME+"/"+nazev,'wb')
			self.update_info_bar(size,current_size, temporary_size, 0, 0, "init")
			start_of_downloading=round(time.time(),3)
			start_time=round(time.time(),15)
			end_time=0
			rychlost=0
			a=0
			temporary_size=0
			self.speed_list=[0,0,0,0,0]
			tmp = stahovani.read(8)
			while (tmp):
				soubor.write(tmp)
				soubor.flush()
				current_size+=len(tmp)
				temporary_size+=len(tmp)
				predchozi=0
				current_time=round(time.time(),10)
				if((current_time-start_time)>0.2):
					self.update_info_bar(size,current_size, temporary_size, start_time, current_time, 0)
					temporary_size=0
					start_time=round(time.time(),10)
				tmp = stahovani.read(8)
				a+=1
			end_of_downloading=round(time.time(),3)
			soubor.close()
			self.update_info_bar(size,current_size, temporary_size, start_of_downloading, end_of_downloading, "finished")
			print "%s (%s) - „%s“ uložen [%s]" % (self.get_time(), self.update_speed(start_of_downloading, end_of_downloading, int(size))[1], nazev, size)
			try:
				self.delete_file_from_queue(kod)
				print "Soubor byl smazán z fronty.\n"
			except:
				print "Soubor nelze odstranit z fronty.\n"
		else:
			print "--%s-- CHYBA 404: Not found\n" % self.get_time()
	def __init__(self):
		self.term = Terminal()
		self.check_terminal_size()
		self.init_parser()
		if (len(self.args) <= 3) and (self.options.heslo==None or self.options.uzivatelske_jmeno==None) :
			self.parser.error("Chybeji argumenty")
		if self.options.file_path != None and self.options.url_address != None:
			self.parser.error("Nelze zaroven zvolit url adresu a vstupni soubor")
		self.filename=self.options.file_path
		self.url_address=self.options.url_address
		self.username=self.options.uzivatelske_jmeno
		self.password=self.options.heslo
		self.HOME=os.getenv("HOME")
		self.downloadingToDir=False
		if self.options.directory != None and os.path.isdir(self.options.directory) == True:
			self.HOME = self.options.directory
			if self.HOME[-1:]=="/": self.HOME=self.HOME[:-1]
			self.downloadingToDir=True
		self.parse_urls()
		print "CzGet, stahovani z czshare.com pomoci CLI"
		self.test_login()
		self.speed_list=[1,1,1,1,1]
		dl_content=[]
		for i in self.content:
			self.download_file(i)

if __name__ == '__main__':
	CZshare()

