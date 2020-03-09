#!/usr/bin/python
#
# redis-dupfilefinder.py - Redis example  by Kåre Hampf <khampf@users.sourceforge.com>
#

import hashlib
import os
import redis
import sys
import zlib

r = redis.Redis(
    host='localhost',
    port=6379,
    password='')


def adler32(fname):
    checksum = 0
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            checksum = zlib.adler32(chunk, checksum)
    return checksum

# (Stack Overflow, Generating an MD5 checksum of a file,
# https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file#3431838
# [2020-03-09])
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# (Stack Overflow, Text Progress Bar in the Console,
# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
# [2020-03-09])
def progressbar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printend="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printend)
    # Print New Line on Complete
    if iteration == total:
        print()


def printdups():
    print('Based on MD5 checksums, %d groups are duplicates' % r.zcount('md5count', 2, 'inf'))
    for md5key in r.lrange('duplicatehashes', 0, -1):
        filesize: int = int(r.hvals(md5key)[0])
        print("=== MD5:%s bytes:%d ===" % (md5key.decode('utf-8'), filesize))
        for md5filepath in r.hgetall(md5key):
            print(md5filepath.decode('utf-8'))


if len(sys.argv) == 1:
    printdups()
    exit(0)

# Flush everything in redis db
r.flushall()

print('Scan initiated')
for arg in sys.argv[1:]:
    print('Recursively collecting files in \"' + arg + '\"')
    for dirpath, dirnames, files in os.walk(arg, followlinks=False):
        for filename in files:
            filepath = os.path.abspath(os.path.join(dirpath, filename))
            if os.path.isfile(filepath):
                r.lpush('filepaths', filepath)
                print('\r%s' % filepath[0:80], end="\r")

pathcount = r.llen('filepaths')
print('Collected %d paths in list' % pathcount)

print('Determining file sizes...')
progress = 0
for filepath in r.lrange('filepaths', 0, -1):
    size: int = os.path.getsize(filepath)
    if size > 0:  # ignore empty files
        sizekey = 'size:%d' % size
        r.zincrby('sizecount', 1, sizekey)
        r.hset(sizekey, filepath, size)  # redundant size but hasmaps needs field=value

    # Update Progress Bar
    progress = progress + 1
    progressbar(progress, pathcount, prefix='Progress:', suffix='Complete', length=50)

duplicates = r.zcount('sizecount', 2, 'inf')
print('Based on file size, %d groups might be duplicates' % duplicates)
if duplicates == 0:
    exit(0)

print('Quick comparison using adler32 checksums...')
samesizes = r.zrangebyscore('sizecount', 2, 'inf')
progress = 0
for sizekey in samesizes:
    size: int = int(sizekey.decode('utf-8')[len('size:'):])
    for filepath in r.hgetall(sizekey):
        adlerkey = "adler:%08x" % adler32(filepath)
        r.zincrby('adlercount', 1, adlerkey)
        r.hset(adlerkey, filepath, size)

    # Update Progress Bar
    progress = progress + 1
    progressbar(progress, len(samesizes), prefix='Progress:', suffix='Complete', length=50)

duplicates = r.zcount('adlercount', 2, 'inf')
print('Based on adler32 checksums, %d groups might be duplicates' % duplicates)
if duplicates == 0:
    exit(0)

print('Thorough comparison using MD5 hashes...')
sameadlers = r.zrangebyscore('adlercount', 2, 'inf')
progress = 0
for adlerkey in sameadlers:
    size: int = int(r.hvals(adlerkey)[0])  # grab size from first field value
    for filepath in r.hgetall(adlerkey):
        md5sum = md5(filepath)
        r.zincrby('md5count', 1, md5sum)
        r.hset(md5sum, filepath, size)

    # Update Progress Bar
    progress = progress + 1
    progressbar(progress, len(sameadlers), prefix='Progress:', suffix='Complete', length=50)

# get duplicate hashes
samemd5s = r.zrangebyscore('md5count', 2, 'inf')

# add hashes to a list
for md5sum in samemd5s:
    size: int = int(r.hvals(md5sum)[0])  # grab size from first field value
    r.lpush('samemd5s', md5sum)  # add to list
    r.hset('%s:size' % md5sum.decode('utf-8'), 'size', size)  # store size for sorting by

# sort hash list by file sizes in external key
r.sort('samemd5s', by='*:size->size', desc=False, store='duplicatehashes')

printdups()
print('Invoke without parameters to print results again')
