CzGET Version 0.4
=====

About
-----
This program allows you to download files from czshare.com using only CLI. Programs is still under development and bugs may be included. If you will found one, please, send me an email to address ja [at] kamilhanus [dot] cz

Requires
-----
 - Blessings 1.5 (included)
 - python-pip (not included) *
 - requests
 - pyquery

* If you will install requests and pyquery yourself, you don't need pip installer.

Instalation
-----

Open terminal, move to folder with extracted files, run __./setup.py__ and follow the instructions.
After this you have o reload your session or run

    source ~/.bashrc

Usage
-----

IF YOU HAVE CONFIG FILE, THE LOGIN INFORMATION ARE UNNECESSARY!

    czget -l username -p password -u url_address
    czget -l username -p password -u url_address -d directory
    czget -l username -p password -f file_path 
    czget -C
    czget -u url_address -O name

 - username = Username on czshare.com
 - password = Password to your account on czshare.com
 - url_address = Address of downloading file
 - file_path = File in yours computer with download links. One link per line.
 - directory = Directory where you want store downloaded files. (Default directory = your HOME dir)
 - name = Different output name
 
 and much more... For more info, please run

     czget --help

Issues
-----
If your download speed does not match your 'real' download capacity, try to increase variable read_bytes in down_file function. Program does refresh very often and your CPU is too slow for that. It is necesarry at RaspberryPi.

Changelog
-----

Version 0.4
 - Improved setup file
 - Added function for resume download
 - Added function for post-installation user information change

Version 0.3
 - Mechanize was replaced with Requests
 - Simple speed limitter
 - Checking of credit size
 - Password is stored encoded (Only base64, but its enough for unwanted visitors.)
 - Downloading file with different name. Does not work with downloading from file list
 - Simple program installer
 - Fixed program crash while file has some special unicode chars

Version 0.2
 - Choosing of own download directory
 - Deleting files from queue
 - Improved UI to look like wget
 - Better download speed meter

Version 0.1
 - Basic download functions
 - Not published :)

Thanks to
-----
 - Eben Upton for making RaspberryPi. Without it I will not had need to write this program.
 - Eric Rose for writting a Blessings module for python. It made making of this program easier.
 - @starenka for his advices ;)
