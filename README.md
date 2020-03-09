# redis-dupfilefinder.py
A small utility written in Python for finding duplicate files within given paths using methods found in Redis. Tested both undr Linux

## Requirements
* Python3
* redis-libraries (```pip install redis```)
* A redis-server. Can be started as user without password and it will work out-of-the-box

## Usage
1. Start a redis server instance for example using `redis-server` on Linux or the Linux-subsystem in Windows.

2. Run `python redis-dupfilefinder.py PATH1 PATH2 ... PATHn` or without arguments to list previously found duplicate files from database. The script can also be run with executable attribute set using the hashbang-property (#!/usr/bin/python) on most systems.

Example:

(to be filled in)

## Datatypes used
![](filehasher-redis-datatypes.svg)



