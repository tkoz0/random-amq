'''
Tool for creating a link database using JSON files exported from the scripts.
The exported JSON files ideally should have a date in the name (YYYYMMDD or
YYYY-MM-DD) so the latest information available can be used since names in the
database can be changed. The result is written to STDOUT as a JSON file. This
output is a dictionary mapping the mp3/webm link to an information object:
{
    # Anime names
    "animeEnglish": str,
    "animeRomaji": str,
    "animeExpandLibrary": str, # The name from expand library
    "altAnswers": List[str], # All valid answers for this link
    # Anime IDs
    "idAnn": int,
    "idMal": int,
    "idKitsu": int,
    "idAnilist": int,
    # Anime info
    "animeType": str, # "TV", "movie", "OVA", "ONA", "special"
    "animeScoreAnn": float,
    "animeSeason": str, # Formatted like "Fall 2021"
    "animeTags": List[str],
    "animeGenres": List[str],
    # Song info
    "annSongId": int, # AMQ specific song ID ? (from expand library dumps)
    "songName": str,
    "songArtist": str,
    "songType": str, # Formatted like "Opening 1", "Ending 10", "Insert"
    "songLength": float,
    "difficulty": int,
    "dates": { "property": "date", ... }
}
Most of these are self-explanatory. The "dates" property is a mapping of the
other properties to the latest date for which that data was found. This is why
having dates in the input files is helpful so that the most recent available
data can be identified. The default value is null (None in Python3), used when
the data is not found. If some data is found from a file without a date, then
the date of that data will be null.

To use this script, run the command:

python3 make_link_db_v2.py [files and directories ...] > output_file

All directories will be processed recursively and data will be collected from
every input file found.

Currently, adding to an existing database file is not supported. The script only
needs to run once to create the database and it is not prohibitively expensive
for realistic amounts of data currently.

TODO support adding to an existing database file
'''

from itertools import chain
from typing import Any, Dict, Iterator, List, Pattern, Union
import json
import os
import re
import sys

def walk_files(dir: str) -> Iterator[str]:
    '''
    Given a directory, returns an iterator of all full file paths inside it.
    '''
    return chain.from_iterable((root+'/'+file for file in files)
        for root,_,files in os.walk(dir))

# Regular expressions to search for in filenames
DATE_FORMATS : List[Pattern[str]] = \
[
    re.compile(r'(\d{4})-(\d\d)-(\d\d)'),
    re.compile(r'(\d{4})(\d\d)(\d\d)')
]

# Ranges for valid dates (output a warning for dates outside this range)
DATE_YMIN = 2017
DATE_YMAX = 2030
DATE_MMIN = 1
DATE_MMAX = 12
DATE_DMIN = 1
DATE_DMAX = 31

def check_date(date: str) -> bool:
    '''
    Checks the range of the given date using the above variables. The date
    format used is "YYYY-MM-DD".
    '''
    y,m,d = map(int,date.split('-'))
    return DATE_YMIN <= y <= DATE_YMAX and DATE_MMIN <= m <= DATE_MMAX \
        and DATE_DMIN <= d <= DATE_DMAX

# Attributes in the output data (except the special attribute "dates")
OUTPUT_ATTR : List[str] = \
[
    'animeEnglish',
    'animeRomaji',
    'animeExpandLibrary',
    'altAnswers',
    'idAnn',
    'idMal',
    'idKitsu',
    'idAnilist',
    'animeType',
    'animeScoreAnn',
    'animeSeason',
    'animeTags',
    'animeGenres',
    'annSongId',
    'songName',
    'songArtist',
    'songType',
    'songLength',
    'difficulty'
]

# Destination attributes to the pattern for identifying the value
ATTR_MAPPING_APPROVALS : Dict[str,Pattern[str]] = \
{
    "animeEnglish": re.compile(r'\*\*Anime:\*\* (.+)'),
    "songName"    : re.compile(r'\*\*Song:\*\* (.+)'),
    "songArtist"  : re.compile(r'\*\*Artist:\*\* (.+)'),
    "songType"    : re.compile(r'\*\*Song Type:\*\* (.+)')
}

APPROVALS_LINK_RE : Pattern[str] = re.compile(r'\*\*Link:\*\* <(.+)>')
VIDEO_LINK_RE     : Pattern[str] = re.compile(r'https?://.+/.+')

# Source to output mapping for attributes in song list lite files
ATTR_MAPPING_SONGS_LITE : Dict[str,str] = \
{
    'animeEnglish': 'animeEnglish',
    'animeRomaji' : 'animeRomaji',
    'annId'       : 'idAnn',
    'songName'    : 'songName',
    'artist'      : 'songArtist',
    'type'        : 'songType',
    'videoLength' : 'songLength',
    'animeEng'    : 'animeEnglish',
    'songDuration': 'songLength'
}

# Source to output mapping for attributes in song list full files
# The source attributes with a . require double dictionary access
ATTR_MAPPING_SONGS_FULL: Dict[str,str] = \
{
    'name'             : 'songName',
    'artist'           : 'songArtist',
    'anime.english'    : 'animeEnglish',
    'anime.romaji'     : 'animeRomaji',
    'annId'            : 'idAnn',
    'type'             : 'songType',
    'siteIds.annId'    : 'idAnn',
    'siteIds.malId'    : 'idMal',
    'siteIds.kitsuId'  : 'idKitsu',
    'siteIds.aniListId': 'idAnilist',
    'difficulty'       : 'difficulty',
    'animeType'        : 'animeType',
    'animeScore'       : 'animeScoreAnn',
    'vintage'          : 'animeSeason',
    'tags'             : 'animeTags',
    'genre'            : 'animeGenres',
    'altAnswers'       : 'altAnswers',
    'videoLength'      : 'songLength'
}

# Source attributes for links in song list lite files
LINKS_SONGS_LITE : List[str] = ['linkWebm', 'linkMP3', 'LinkVideo', 'LinkMp3']

'''
Songs full URLs contained in "urls" attribute, mapping site ("openingsmoe" or
"catbox") to a mapping of resolution (0 for mp3) to url.

Expand library URLs are contained in the "examples" attribute, which maps a
resolution or "mp3" to the url.
'''

def insert_info(db: Dict[str,dict], links: List[str],
                attr: str, value: Any, date: Union[str,None]):
    '''
    Adds an attribute with given value to the links specified. If the data
    already exists, it is replaced only if a later date is provided (or any date
    if no date is associated with the existing data).)
    '''
    for link in links: # ensure default null values are in the database
        if link not in db:
            db[link] = dict()
            for attr_ in OUTPUT_ATTR:
                db[link][attr_] = None
            db[link]['dates'] = dict()
            for attr_ in OUTPUT_ATTR: # null date for each attribute
                db[link]['dates'][attr_] = None
    for link in links:
        old_date = db[link]['dates'][attr]
        if old_date is None: # for comparing dates as str
            old_date = ''
        if db[link][attr] is None or \
            (date is not None and date > old_date):
            db[link][attr] = value
            db[link]['dates'][attr] = date

def add_approvals(db: Dict[str,dict], data: dict):
    '''
    Add link info from dumps of the #approvals channel on the discord. Dates are
    determined from the message dates in the dump rather than the filename.

    (Most) messages from the Komugi bot will have a neat format listing the
    english anime name, song name, song artist, song type, and video link.
    '''
    for i,message in enumerate(data['messages']):
        date = message['timestamp'][:10]
        if not check_date(date):
            sys.stderr.write(f'    Message {i} has date {date}, skipping\n')
            continue
        text = message['content'].splitlines()
        if len(text) == 0: # get from embed
            if len(message['embeds']) == 0:
                sys.stderr.write(f'    Failed to get text from message {i}\n')
                continue
            text = message['embeds'][0]['description'].splitlines()
        link : Union[None,str] = None
        for line in text: # find link
            match = APPROVALS_LINK_RE.fullmatch(line)
            if match:
                link = match.group(1)
                break
        if link is None:
            sys.stderr.write(f'    Failed to get link for message {i}\n')
            continue
        if not VIDEO_LINK_RE.fullmatch(link):
            sys.stderr.write(f'    Invalid link in message {i}: {link}\n')
            continue
        for dest in ATTR_MAPPING_APPROVALS:
            pattern = ATTR_MAPPING_APPROVALS[dest]
            for line in text: # find data
                match = pattern.fullmatch(line)
                if match:
                    insert_info(db,[link],dest,match.group(1),date)
                    break

def add_songs_lite(db: Dict[str,dict], data: List[Dict[str,Any]],
                    date: Union[str,None]):
    '''
    Add link info from song list files. Should be successful if it runs without
    exceptions.

    Attribute mapping (source -> database):
    animeEnglish -> animeEnglish
    animeRomaji -> animeRomaji
    annId -> idAnn
    songName -> songName
    artist -> songArtist
    type -> songType
    videoLength -> songLength
    (old ones)
    animeEng -> animeEnglish
    songDuration -> songLength

    Links: linkWebm, linkMP3, LinkVideo, LinkMp3
    '''
    for song in data:
        links = [song[attr] for attr in LINKS_SONGS_LITE if attr in song]
        for src,dest in ATTR_MAPPING_SONGS_LITE.items():
            if src not in song:
                continue
            insert_info(db,links,dest,song[src],date)

def add_songs_full(db: Dict[str,dict], data: List[Dict[str,Any]],
                    date: Union[str,None]):
    '''
    Add link info from full song list files. Should be successful if it runs
    without exceptions.

    Attribute mapping (source -> database):
    name -> songName
    artist -> songArtist
    anime.english -> animeEnglish
    anime.romaji -> animeRomaji
    annId -> idAnn
    type -> songType
    siteIds.annId -> idAnn
    siteIds.malId -> idMal
    siteIds.kitsuId -> idKitsu
    siteIds.aniListId -> idAnilist
    difficulty -> difficulty
    animeType -> animeType
    animeScore -> animeScoreAnn
    vintage -> animeSeason
    tags -> animeTags
    genre -> animeGenres
    altAnswers -> altAnswers
    videoLength -> songLength

    Links: the "urls" attribute is a map of site to resolution to url
    '''
    for song in data:
        links = sum([list(song['urls'][site].values())
                        for site in song['urls']],[])
        for src,dest in ATTR_MAPPING_SONGS_FULL.items():
            if '.' in src: # double access with 2 keys
                k1,k2 = src.split('.')
                if k1 in song and k2 in song[k1]:
                    insert_info(db,links,dest,song[k1][k2],date)
            elif src in song:
                insert_info(db,links,dest,song[src],date)

def add_exp_lib(db: Dict[str,dict], data: List[Any], date: Union[str,None]):
    '''
    Add link info from expand library dumps. Should be successful if it runs
    without exceptions.

    Attribute mapping (for anime) (source -> database):
    annId -> idAnn
    name -> animeExpandLibrary

    Attribute mapping (for songs) (source -> database):
    annSongId -> annSongId
    name -> songName
    type,number -> songType (requires conversion of 2 attributes)
    artist -> songArtist

    Links: the "examples" attribute maps resolution to url
    '''
    data = data[1]['data']['questions'] # main part of the data
    for anime in data:
        annId = anime['annId']
        animeName = anime['name']
        for song in anime['songs']:
            type_ = ['Opening','Ending','Insert'][song['type']-1]
            if type_ != 'Insert':
                number = song['number']
                type_ = f'{type_} {number}'
            links = song['examples'].values()
            insert_info(db,links,'idAnn',annId,date)
            insert_info(db,links,'animeExpandLibrary',animeName,date)
            insert_info(db,links,'annSongId',song['annSongId'],date)
            insert_info(db,links,'songName',song['name'],date)
            insert_info(db,links,'songType',type_,date)
            insert_info(db,links,'songArtist',song['artist'],date)

# Set to False for debugging so the script fails completely on error
HANDLE_EXCEPTIONS = True

def add_from_file(db: Dict[str,Any], file: str):
    sys.stderr.write(f'Processing file: {file}\n')

    data = json.loads(open(file,'r').read())

    if type(data) == dict: # expect discord channel export
        try:
            add_approvals(db,data)
        except Exception as e:
            if HANDLE_EXCEPTIONS:
                sys.stderr.write(f'    Failed parsing as approvals channel'
                                    'dump\n')
                sys.stderr.write(f'    {type(e)}: {str(e)}\n')
            else:
                raise e
        return

    elif type(data) != list or len(data) == 0:
        sys.stderr.write(f'    Not a JSON list\n')
        return

    # Extract date from filename
    date : Union[str,None] = None
    for fmt in DATE_FORMATS:
        match = fmt.search(file)
        if not match:
            continue
        date_ = '-'.join(match.groups())
        if not check_date(date_):
            sys.stderr.write(f'    Date {date_} out of range, not using\n')
            continue
        date = date_
        break

    # No date
    if date is None:
        sys.stderr.write(f'    Unable to extract date\n')

    # Determine the type of file
    if data[0] == 'command':
        try:
            add_exp_lib(db,data,date)
        except Exception as e:
            if HANDLE_EXCEPTIONS:
                sys.stderr.write(f'    Failed parsing as expand library dump\n')
                sys.stderr.write(f'    {type(e)}: {str(e)}\n')
            else:
                raise e
    elif 'players' in data[0]:
        try:
            add_songs_full(db,data,date)
        except Exception as e:
            if HANDLE_EXCEPTIONS:
                sys.stderr.write(f'    Failed parsing as song list full\n')
                sys.stderr.write(f'    {type(e)} {str(e)}\n')
            else:
                raise e
    else:
        try:
            add_songs_lite(db,data,date)
        except Exception as e:
            if HANDLE_EXCEPTIONS:
                sys.stderr.write(f'    Failed parsing as song list lite\n')
                sys.stderr.write(f'    {type(e)} {str(e)}\n')
            else:
                raise e

if __name__ == '__main__':

    # Get files and dirs with normed paths
    arg_norm  : List[str] = list(map(os.path.normpath, sys.argv[1:]))
    arg_files : Iterator[str] = filter(os.path.isfile, arg_norm)
    arg_dirs  : Iterator[str] = filter(os.path.isdir , arg_norm)

    # Chain given files with all files in each given directory
    inputs : Iterator[str] = chain(arg_files,
        chain.from_iterable(walk_files(dir) for dir in arg_dirs))

    database : Dict[str,Any] = dict()

    # Collect data from each file
    for file in inputs:
        add_from_file(database,file)
        
    # Write output
    sys.stdout.write(json.dumps(database,separators=(',',':')))

