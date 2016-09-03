#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys  # for setting encoding
from sys import stdin				#For reading Userinput from STDIN
import getpass # for reading password from stdin
import os # for writing file to disk
from os.path import expanduser # for getting the home directory

import requests # for making HTTP requests
from bs4 import BeautifulSoup # for parsing html

from multiprocessing import Pool # for multi threading
from multiprocessing.dummy import Pool as ThreadPool  # for multi threading

import string
import re # for regular expressions

def getValidFilename(sString):
	"""
	Take a string and return a valid filename constructed from the string.
	Uses a whitelist approach: any characters not present in valid_chars are
	removed. Also spaces are replaced with underscores.

	Note: this method may produce invalid filenames such as ``, `.` or `..`
	When I use this method I prepend a date string like '2009_01_15_19_46_32_'
	and append a file extension like '.txt', so I avoid the potential of using
	an invalid filename.
	:param sString: the string to be converted
	:return: the converted string
	"""
	sString = sString.encode('utf-8')
	sString = sString.replace("&", "und")
	sString = sString.replace("ä", "ae")
	sString = sString.replace("Ä", "Ae")
	sString = sString.replace("ö", "oe")
	sString = sString.replace("Ö", "Oe")
	sString = sString.replace("ü", "ue")
	sString = sString.replace("Ü", "Ue")
	sString = sString.replace("ß", "ss")

	valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
	sNewFilename = ''.join(c for c in sString if c in valid_chars)
	sNewFilename = sNewFilename.replace(' ', '_')  # I don't like spaces in filenames.

	return sNewFilename

def createDirectory(sDirectoryPath):
	"""
	Create the directory located at sDirectoryPath if not existing
	:param sDirectoryPath: the path to the new directory
	:return: the path to the directory
	"""
	sDirectoryPath = os.path.join(expanduser("~"), "Downloads" + os.sep + sDirectoryPath)
	if not os.path.exists(sDirectoryPath):
		os.makedirs(sDirectoryPath)
	return sDirectoryPath

def writeFileToDisk(oFile, sFilePath, sFileName):
	"""
	Write a downloaded file to the path provided
	:param oFile: the binary which shall be written to the filesystem
	:param sFilepath: the directory where it shall be written to
	:param sFileName: the name of the file
	:return:
	"""
	sPath = createDirectory(sFilePath)
	# change directory to the path
	os.chdir(sPath)

	with open(sFileName, 'wb') as f:
		try:
			f.write(oFile.content)
			print "Writing file " + sFileName + " to the directory " + sPath
		except :  # whatever reader errors you care about
			print "There was an error writing file " + sFileName


def getFileNameAndLinkFromCategory(sUrl, oSession, bCreateSectionFolders):
	"""
	Download all files from a category to the destination.
	:param sUrl: the url of the site which will be downloaded
	:param oSession: session object which contains a valid user session
	:param bCreateSectionFolders: true if file shall be written to subdirectories, false if all files should be in same folder
	:return: a list containing a list (sFileDirectory, oSession, sFileName, sDownloadUrl) for every file
	"""
	oResponse = oSession.get(sUrl)
	lFilesToDownload = [] # the list containing the files which shall be downloaded

	# parse the HTML site
	oParsed = BeautifulSoup(oResponse.content, 'html.parser')

	# check if the plugins was found
	if oParsed.getText().find("Datensatz kann nicht in der Datenbanktabelle course gefunden werden") != -1:
		print "######## Couldn't download the section with the url " + sUrl
		return []

	# the div containing all interesting parts
	oCourseContent = oParsed.find("div", class_="course-content")

	# the name of the course
	oCourseName = oCourseContent.find("h2", class_="stpheadingblock")
	sCourseName = "CourseDownloaded"
	if oCourseName != None:
		sCourseName = oCourseName.text
		# remove ( from coursename
		iCourseNameEnd = sCourseName.find("(")
		if iCourseNameEnd != -1:
			sCourseName = sCourseName[:iCourseNameEnd]
			sCourseName = sCourseName.strip()
	else:
		sCourseName = str(oParsed.title.text)

	sCourseName = getValidFilename(sCourseName)

	# the files in the course
	oAllFilesIgnoringSections = oCourseContent.find_all("div", class_="activityinstance")
	oSections = oCourseContent.find_all("li", class_="section")

	# for every section a folder will be created. All files of a section will be stored in that folder
	for oActSection in oSections:

		oSectionName = oActSection.find("h3", class_="sectionname")
		if oSectionName == None:
			continue

		sSectionName = oSectionName.text
		if bCreateSectionFolders == True:
			sFileDirectory = getValidFilename(sCourseName) + os.sep + getValidFilename(sSectionName)
		else:
			sFileDirectory = getValidFilename(sCourseName)

		oFiles = oActSection.find_all("div", class_="activityinstance")

		# image is the only possibility to recognize the file type
		""" e.g.:
		<div class="activityinstance">
		<a class="" href="https://ecampus.fhstp.ac.at/mod/assign/view.php?id=251343" onclick="">
		<img alt=" " class="iconlarge activityicon" role="presentation"
		src="https://ecampus.fhstp.ac.at/theme/image.php/formal_white/assign/1450337389/icon"/>
		<span class="instancename">Delivery Group D<span class="accesshide "> Aufgabe</span></span></a></div>
		"""
		# source of Aufgabe/Abgabe https://ecampus.fhstp.ac.at/theme/image.php/formal_white/assign/1450337389/icon
		# source of Url https://ecampus.fhstp.ac.at/theme/image.php/formal_white/url/1450337389/icon
		# source of messages e.g. Kursnachrichten https://ecampus.fhstp.ac.at/theme/image.php/formal_white/forum/1450337389/icon

		bStop = False
		for oActFile in oFiles:
			if bStop == True:
				break

			sActFile = str(oActFile)
			oUrl = oActFile.find("a")

			# get download url
			sDownloadUrl = oUrl['href']

			# find out filename
			sFileName = oUrl.text

			# find out type of the file with the imagesrc
			iImageSrcBegin = sActFile.find("src=\"")
			iImageSrcEnd = -1
			if iImageSrcBegin != -1:
				iImageSrcEnd = sActFile.find("\"/>", iImageSrcBegin + 7)
			if iImageSrcBegin == -1 or iImageSrcEnd == -1:
				print "Couldn't find the type of the file"
				bStop = True

			sImageSrc = sActFile[iImageSrcBegin + 5: iImageSrcEnd]

			# blacklist for filetypes which we are not interested in
			# filetype is determined from the image url
			lBlackList = ['theme/image.php/formal_white/assign/1450337389']
			lBlackList.append('theme/image.php/formal_white/url/1450337389')
			lBlackList.append('theme/image.php/formal_white/forum/1450337389')

			bInterestingDownload = True

			for sActItem in lBlackList:
				if sImageSrc.find(sActItem) != -1:
					bInterestingDownload = False
					break

			# there is a special case when the teacher put a folder to the course page
			if sImageSrc.find("theme/image.php/formal_white/folder/1450337389/icon") != -1:
				# visit the directory page and get all file links and names there
				oSpecialDirectoryResponse = oSession.get(sDownloadUrl)
				oParsedSpecialDirectoryResponse = BeautifulSoup(oSpecialDirectoryResponse.content, 'html.parser')
				oSepcialDirectoryCourseContent = oParsedSpecialDirectoryResponse.find("div", class_="foldertree")
				oUrls = oSepcialDirectoryCourseContent.find_all("a")

				for oActUrl in oUrls:
					sFileName =  oActUrl.text
					sDownloadUrl = oActUrl['href']
					lFilesToDownload.append([sFileDirectory, oSession, sFileName, sDownloadUrl])
				continue

			if bInterestingDownload == True:
				lFilesToDownload.append([sFileDirectory, oSession, sFileName, sDownloadUrl])

	return lFilesToDownload



def downloadFile(lFile):
	"""
	Download the file contained in the lFile list
	http://stackoverflow.com/questions/34503412/download-and-save-pdf-file-with-python-requests-module
	:param lFile: a list containing sCourseName, oSession, sFileName, sDownloadUrl
	:return: a list containing the binary, filename and coursename, none if it didn't work
	"""

	sFileDirectory = lFile[0]
	oSession = lFile[1]
	sFileName = lFile[2]
	sDownloadUrl = lFile[3]

	# download the file
	oDownloadedFile = oSession.get(sDownloadUrl, stream=True)

	if oDownloadedFile.status_code == 200 and 'content-disposition' in oDownloadedFile.headers.keys():
		# check the headers of the file containing the original file name
		sDownloadHeader = oDownloadedFile.headers['content-disposition']  # inline; filename="20151104_LV-DB_SS2016_MIS-2_GCC2.pdf"

		iOriginalFilenameBegin = sDownloadHeader.find("filename=\"")
		iOriginalFilenameEnd = -1
		if iOriginalFilenameBegin != -1:
			iOriginalFilenameEnd = sDownloadHeader.find("\"", iOriginalFilenameBegin + 11)

		if iOriginalFilenameBegin != -1 and iOriginalFilenameEnd != -1:
			sOriginalFilename = sDownloadHeader[iOriginalFilenameBegin + 10: iOriginalFilenameEnd]
			sFileEnding = sOriginalFilename.split(".")[-1]
			if len(sOriginalFilename.split(".")[-1]) > 0:
				sFileName = getValidFilename(sFileName) + "." + sFileEnding

		return [oDownloadedFile, sFileName, sFileDirectory]

	print "There was an error downloading file " + sFileName + " with the URL " + sDownloadUrl

	return



def login(sUrl, sUsername, sPassword, headers, proxies):
	"""
	Method to login on moodle website
	:param sUrl: base url to the website
	:param sUsername: username to login to website
	:param sPassword: password to login to website
	:param headers: The header - user-agent string which gets send with the HTTPS request
	:return: Session object who persists cookies across all requests made from the Session instance.
			it allows you to persist certain parameters across requests.
			Return None if there is an error
	"""
	# http://docs.python-requests.org/en/latest/user/advanced/#session-objects
	oSession = requests.Session()
	payload = {'username': sUsername,'password': sPassword}

	#POST-Request with: user=YOURMAILADDRESS&pass=YOURPASSWORD&login=Einloggen
	#r = oSession.post(sUrl + '/login/index.php', data = payload, headers = headers, verify=False, proxies = proxies) # with proxy
	r = oSession.post(sUrl + '/login/index.php', data=payload, headers=headers, verify=False)

	##Test if login was successfull
	if r.text.find("Sie sind nicht angemeldet.") != -1:
		print("Login was not successfull - the provided username or password may be wrong!\n")
		return None

	return oSession

def main():

	# configure the program to use utf8 encoding
	reload(sys)
	sys.setdefaultencoding('utf8')

	print "#### Welcome to the MoodleDownloader!\n"
	sUsername = raw_input("Enter you username: ")
	sPassword = getpass.getpass('Enter password: ')

	keepProgramRunning = True
	bCreateSectionFolders = True # if this variable is set to false all files will be written to the course folder and no subdirectories will be created

	while keepProgramRunning:
		print "* Enter a url of a site containing a course page which you want to download. (e.g. https://moodle.university.ac.at/course/view.php?id=1234)"
		print "* Type true or false if you want to change that section folders should be created. Current: " + str(bCreateSectionFolders)
		print "* Exit the program by typing exit\n"

		sUserInput = raw_input("Your url: ")

		if sUserInput == "exit":
			print "GoodBye!"
			keepProgramRunning = False
		elif sUserInput.upper() == "TRUE":
			bCreateSectionFolders = True
		elif sUserInput.upper() == "FALSE":
			bCreateSectionFolders = False

		else:
			# check if input is a url containing the /course/view.php part
			sCategoryUrl = sUserInput.strip()
			iUrlEndPosition = sCategoryUrl.find("/course/view.php?id=")
			if iUrlEndPosition == -1:
				print "The url provided by you has is not containing what the program is looking for."
				print "e.g. https://moodle.university.ac.at/course/view.php?id=1234"
				continue

			sUrl = sCategoryUrl[:iUrlEndPosition]

			headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
			# proxy can be used if necessary, at the moment commented out in the login function
			proxies = {
				'http': 'http://127.0.0.1:8080',
				'https': 'http://127.0.0.1:8080',
			}
			oSession = login(sUrl, sUsername,sPassword,headers, proxies)

			if oSession == None:
				return # end program if there was an error loging in

			lFilesToDownload = getFileNameAndLinkFromCategory(sCategoryUrl, oSession, bCreateSectionFolders)

			# Make the Pool of workers
			pool = ThreadPool(7)
			# Open the urls in their own threads
			# and return the results
			lDownloadedFiles = pool.map(downloadFile, lFilesToDownload)

			#close the pool and wait for the work to finish
			pool.close()
			pool.join()

			# write the downloaded files to disk
			for lActFile in lDownloadedFiles:
				if lActFile == None:
					continue
				oBinary = lActFile[0]
				sFilename = lActFile[1]
				sFileDirectory = lActFile[2]

				writeFileToDisk(oBinary,sFileDirectory,sFilename)
			print "\n\n"

if  __name__ =='__main__':
	main()