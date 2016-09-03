# Moodle Downloader

Moodle Downloader is a python script created for easily downloading moodle course pages.
You need to have the credentials and the url to the course page which you want to download.
The program will login to moodle and visit the course page.
All files at the course page will be downloaded to your HOME/Download  directory

## Installation

The program is written in python 2 under Linux.
Therefore you need a working python2 environment. [python2]

### Prerequisites
Also the following libraries need to be installed with python **pip**:

* **pip install beautifulsoup4**    # provides simple methods for navigating, searching, modifying and parsing of a HTML DOM tree
* **pip install requests**    #  is a simple HTTP library for Python
* **pip install multiprocessing** # a library for threads



### Install program

To run the script your system has to fulfill the rerequisities listed above.

* Download the Main.py file

You can run the programm by typing
```sh
$ python Main.py
```

## Usage
The program is a console application.
After starting a menu similar to this will be shown:
```sh
#### Welcome to the MoodleDownloader!

Enter you username:
```

Inside there you can enter your credentials.
After you entered your credentials the program will ask you for a url to a course page.

## Authors

* **Christoph**


   [python2]: <https://www.python.org/downloads/>
