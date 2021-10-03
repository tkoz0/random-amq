'''
Creates a JSON database file of info about links to AMQ videos/mp3s. Writes to
STDOUT an object mapping link to the following object:
{
    "animeEng":
    "animeRomaji":
    "annId":
    "songName":
    "artist":
    "type":
    "length":
    "latestDate":
    "annSongId":
}
Each item is a list of all values found in the input data. The "length" property
is a list of floating point, "annId" is a list of integer, and all the others
are lists of string. The exception is "latestDate" which is a string
representing the most recent date associated with a file containing the link.
Dates are parsed from filenames.

Usage: make_link_db.py <input_dirs...>

Finds all input files to parse and include as much information as possible.
Sometimes names of animes/songs may change so the format supports duplicates.
'''

import json
import os
import re
import sys

inputs = [os.path.normpath(f) for f in sys.argv[1:]]

while True: # BFS to get all files
    dirs = [f for f in inputs if os.path.isdir(f)]
    files = [f for f in inputs if os.path.isfile(f)]
    if len(dirs) == 0: break # done expanding dirs
    files += sum([[d+'/'+f for f in os.listdir(d)] for d in dirs],[])
    inputs = files

for f in inputs:
    assert os.path.isfile(f)

re_date1 = re.compile(r'(\d{4})-(\d\d)-(\d\d)')
re_date2 = re.compile(r'(\d{4})(\d\d)(\d\d)')

database = dict() # object to write at end

# inserts new link, does nothing if already in database
def insert_link(db,link):
    assert link
    if link in db: return
    db[link] = dict()
    db[link]['animeEng'] = []
    db[link]['animeRomaji'] = []
    db[link]['annId'] = []
    db[link]['songName'] = []
    db[link]['artist'] = []
    db[link]['type'] = []
    db[link]['length'] = []
    db[link]['latestDate'] = None
    db[link]['annSongId'] = []

# inserts new info for a link, assumes link is already in database
def insert_info(db,link,attr,value):
    if attr == 'type' and value == 'Insert Song':
        value = 'Insert'
    if attr == 'latestDate':
        current = db[link][attr]
        if value and (current is None or value > current):
            db[link][attr] = value
    else:
        if value not in db[link][attr]:
            db[link][attr].append(value)

# expand library dump
def process_expand_library(db,data,date):
    # data is a list with 1 object per anime
    for anime_obj in data:
        annId = anime_obj['annId']
        animeEng = anime_obj['name']
        for song_obj in anime_obj['songs']:
            annSongId = song_obj['annSongId']
            songName = song_obj['name']
            type_ = ['Opening','Ending','Insert'][song_obj['type']-1]
            if type_ != 'Insert':
                type_ += ' %d'%song_obj['number']
            artist = song_obj['artist']
            for link in song_obj['examples'].values():
                insert_link(db,link)
                insert_info(db,link,'annId',annId)
                insert_info(db,link,'animeEng',animeEng)
                insert_info(db,link,'annSongId',annSongId)
                insert_info(db,link,'songName',songName)
                insert_info(db,link,'type',type_)
                insert_info(db,link,'artist',artist)
                insert_info(db,link,'latestDate',date)

# attribute mapping for song list only files
attr_map = \
{
    'animeEng': ['animeEng','animeEnglish'],
    'animeRomaji': ['animeRomaji'],
    'annId': ['annId'],
    'songName': ['songName'],
    'artist': ['artist'],
    'type': ['type'],
    'length': ['length','videoLength']
}

attr_links = ['linkMp3','linkVideo','linkWebm']

# song list only
def process_songs_lite(db,data,date):
    for song_obj in data:
        extracted = dict()
        for attr in attr_map:
            for source_attr in attr_map[attr]:
                if source_attr in song_obj:
                    extracted[attr] = song_obj[source_attr]
                    break
        links = []
        for attr in attr_links:
            if attr in song_obj:
                links.append(song_obj[attr])
        for link in links:
            if not link: continue
            insert_link(db,link)
            for attr in extracted:
                insert_info(db,link,attr,extracted[attr])
            insert_info(db,link,'latestDate',date)

# attribute mapping for some of the full data
attr_map_full = \
{
    'annId': 'annId',
    'songName': 'name',
    'artist': 'artist',
    'type': 'type',
    'length': 'videoLength'
}

# song list with player data
def process_songs_full(db,data,date):
    for song_obj in data:
        extracted = dict()
        extracted['animeEng'] = song_obj['anime']['english']
        extracted['animeRomaji'] = song_obj['anime']['romaji']
        for attr in attr_map_full:
            source = attr_map_full[attr]
            if source in song_obj:
                extracted[attr] = song_obj[source]
        links = sum([list(v.values()) for v in song_obj['urls'].values()],[])
        for link in links:
            if not link: continue
            insert_link(db,link)
            for attr in extracted:
                insert_info(db,link,attr,extracted[attr])
            insert_info(db,link,'latestDate',date)

# tries to get date from filename, otherwise none
def extract_date(f):
    match1 = re_date1.search(f)
    match2 = re_date2.search(f)
    if match1:
        yyyy,mm,dd = match1.groups()
    elif match2:
        yyyy,mm,dd = match2.groups()
    else:
        return None
    assert int(yyyy) in range(2015,2030)
    assert int(mm) in range(1,13)
    assert int(dd) in range(1,32)
    return '-'.join([yyyy,mm,dd])

# read f and add new contents to db object
def process_file(db,f):
    filename = os.path.basename(f)
    date = extract_date(filename)
    data = json.loads(open(f,'r').read())
    assert type(data) == list
    if data[0] == 'command': # expand library dump
        assert len(data) == 2
        process_expand_library(db,data[1]['data']['questions'],date)
    elif 'gameMode' in data[0]: # full song data
        process_songs_full(db,data,date)
    else: # song list only
        process_songs_lite(db,data,date)

errors = 0
for f in inputs:
    try:
        sys.stderr.write(f'Loading file: {f}\n')
        process_file(database,f)
    except Exception as e:
        errors += 1
        sys.stderr.write(f'Error processing: {f}\n')
        sys.stderr.write(f'{type(e).__name__}: {e}\n')

sys.stderr.write(f'{errors} error(s)')

# output compact json to STDOUT
print(json.dumps(database,separators=(',',':')))
