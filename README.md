# redis-dupfilefinder.py
A small utility written in Python for finding duplicate files within given paths using methods found in Redis.

## Datatypes used

@startuml
object filepaths
filepaths : <b>List</b> <i>paths</i>

object sizemap
sizemap : <b>Hashmap</b> size:<i>filesize[<i>path</i>]=<i>filesize</i>

object sizecount
sizecount : <b>Ordered set</b> <i>size</i>=<i>count</i>

object samesizes
samesizes : <b>List</b> <i>sizes</i>

object adler32
adler32 : <b>Hashmap</b> adler:<i>checksum</i>[<i>path</i>]=<i>filesize</i>

object adlercount
adlercount : <b>Ordered set</b> <i>size</i>=<i>count</i>

object sameadlers
sameadlers : <b>List</b> <i>adler32</i>

object md5sums
md5sums : <b>Hashmap</b> <i>MD5</i>[<i>path</i>]=<i>filesize</i>

object md5count
md5count : <b>Ordered set</b> <i>MD5</i>=<i>count</i>

object samemd5s
samemd5s : <b>List</b> <i>MD5</i>

object hashedsize
hashedsize : <b>Hashmap</b> <i>MD5</i>:size[size]=<i>filesize</i>

object duplicates
duplicates : <b>List</b> <i>MD5</i>

filepaths --> sizemap : store
filepaths -> sizecount : count
sizecount --> samesizes : n>1
note right of samesizes: ZRANGEBYSCORE sizecount 2 inf
note "adler32 checksum on equal size" as N1

N1 --> adler32 : calculate
N1 -> adlercount : count

samesizes --> N1
sizemap --> N1
adlercount --> sameadlers : collect n>1
note right of sameadlers: ZRANGEBYSCORE adlercount 2 inf
note "MD5 hash on identical adler32" as N2

sameadlers --> N2
adler32 --> N2

N2 --> md5sums : calculate
N2 -> md5count : count
md5count --> samemd5s : collect n>1
note right of samemd5s: ZRANGEBYSCORE md5count 2 inf

md5sums --> hashedsize
hashedsize --> duplicates
samemd5s --> duplicates : sort
samemd5s --> hashedsize
note right of duplicates: SORT samemd5s BY *:size->size ASC

note "Duplicate files grouped by MD5 and sorted by size" as result
md5sums --> result
duplicates --> result

@enduml


