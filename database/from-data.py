'''
This is not done and I am not sure it will be finished. I realized that the
problem this is trying to solve is very annoying to solve and that it would be
easier to do things a different way. The intention was to build a local database
of catbox links organized by anime/song.
'''

import json
import os
import re
import sys

output = sys.argv[1] # file for json output

inputs = sys.argv[2:] # files/dirs with song list exports / expand library dumps

while True: # BFS collect all files
    dirs = [f for f in inputs if os.path.isdir(f)]
    files = [f for f in inputs if os.path.isfile(f)]
    if len(dirs) == 0: break
    files += sum([[d+'/'+f for f in os.listdir(d)] for d in dirs],[])
    inputs = files

# map: anime annId ->
# {
#   "names": string list (unique only)
#   "songs": list of songs
#   [
#     {
#       "name": string list
#       "artist": string list
#       "type": string like "ed1", "op2", "in0" (inserts are numbered 0?)
#       "links":
#       {
#         "720": map url -> most recent date found (8 digit string)
#         "480": ...
#         "mp3": ...
#       }
#     }
#   ]
#   
# }
# for now: song is uniquely identified by name,artist,type
database = dict()
datematch1 = re.compile('(\d{4})-(\d\d)-(\d\d)')

for f in inputs:
    i = len(f)-1
    while i > 0 and f[i] != '/': i -= 1 # find filename
    if f[i] == '/': i += 1
    match = datematch1.search(f[i:])
    if match:
        date = ''.join(match.groups())
        if int(date[:4]) not in range(2017,2030):
            print('date',date,'failed sanity check in:',f)
            continue
    else:
        # try last 8 digits before extension
        j = len(f)-1
        while j > 0 and f[j] != '.': j -= 1
        if f[j] == '.' and j-8 >= 0:
            date = f[j-8:j]
            if not date.isdigit() or int(date[:4]) not in range(2017,2030):
                print('date',date,'failed sanity check in:',f)
                continue
        else:
            print('cannot parse date from filename:',f)
            continue
    object = json.loads(open(f,'r').read())
    assert type(object) == list
    if len(object) == 0: continue
    if object[0] == 'command': # expand library dump
        animes = object[1]['data']['questions']
        for anime in animes:
            annId = anime['annId']
            name = anime['name']
            songs = anime['songs']
            if annId not in database:
                database[annId] = dict()
                database[addId]['names'] = []
                database[annId]['songs'] = []
            if name not in database[annId]['names']:
                database[annId]['names'].append(name)
            for song0 in songs:
                name = song0['name']
                artist = song0['artist']
                type = ['op','ed','in'][song0['type']] + str(song0['number'])
                # find song if it exist already
                index = -1
                for i,song in enumerate(database[annId]):
                    if (song['name'],song['artist'],song['type']) \
                        == (name,artist,type):
                        index = i
                        break
                if index == -1: # create new entry
                    index = len(database[annId])
                    database[annId].append(dict())
                    database[annId][index]['name'] = name
                    database[annId][index]['artist'] = artist
                    database[annId][index]['type'] = type
                    database[annId][index]['links'] = dict()
                for res in song0['examples']:
                    if res not in database[annId][index]['links']:
                        database[annId][index]['links'][res] = \
                            [[song0['examples'][res],date]]
                    else:
                        # find the link if it already exists
                        index2 = -1
                        for i,item in enumerate(database[annId][index]['links']):
                            if item[0] == song0['examples'][res]:
                                index2 = i
                                break
                        if index2 == -1:
                            index2 = len(database[annId][index]['links'])
                            database[annId][index]['links'].append([song0['examples'][res],date])
                        else:
                            database[annId][index]['links'][index2] = \
                                [song0['examples'][res],max(database[annId][index]['links'][index2][1],date)]
    else: # song list export (either type)
        pass




# map attributes in reformatted to those in original data
attr_mapping = \
{
    'animeEng': ['animeEng','animeEnglish'],
    'animeRomaji': ['animeRomaji'],
    'songName': ['songName'],
    'artist': ['artist'],
    'type': ['type'],
    'link': ['LinkVideo','linkWebm']
}

