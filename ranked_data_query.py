'''
Requires the ranked_data.pickle.bz2 file to be created by running amq_loader.py.
Specify query as a list of arguments to search the parameters available. Only
one condition may be specified for each parameter, using the last one if it
occurs multiple times.

String parameters:
animeeng=<keywords>
animeromaji=<keywords>
songname=<keywords>
artist=<keywords>
type=<op|ed|in>[##]
dateold=YYYY-MM-DD
datenew=YYYY-MM-DD

(keywords is a whitespace separated list of words the parameter must contain)
(type is optionally followed by a number, which is ignored for insert songs)
(keywords are case insensitive)

Number parameters:
correct<##
correct>##
players<##
players>##
ratio<#.#
ratio>#.#

(ratio is calculated as correct/players)
Both the < and > options can be specified to create a range
The < and > symbols have to be quoted in bash

Examples:

1. Find all Love Live songs by Aqours
ranked_data_query.py animeeng="love live sunshine" artist=aqours
2. Find Dragon Ball Z OPs before March 2020
ranked_data_query.py animeeng="dragon ball z" type=op datenew=2020-02-29
3. Find all occurrences of Angel Beats ED3
ranked_data_query.py animeeng="angel beats" type=ed3
4. Find the hardest Idolm@ster songs
ranked_data_query.py animeromaji=idolm@ster ratio"<0.05"
5. Find muscle songs in games with over 300 players in 2021
ranked_data_query.py players">300" correct"<2" correct">0" dateold=2021-01-01

The results are written to stdout as a JSON list of objects:
{
    "date": string,
    "region": string,
    "song": object with satisfying parameters
}
'''

import amq_loader
import json
import re
import sys

def queryRankedData(data,parameters,debug=False):
    
    # parameter conditions
    animeeng = []
    animeromaji = []
    songname = []
    artist = []
    typeRegex = re.compile(r'.*')
    correctLo = -1
    correctHi = 2**31 # essentially infinity
    playersLo = -1
    playersHi = 2**31
    ratioLo = -0.1
    ratioHi = 1.1
    dateold = '2000-01-01'
    datenew = '2099-12-31'
    
    for arg in sys.argv:
        arg = arg.lower()
        if arg.startswith('animeeng='): animeeng = arg[9:].split()
        if arg.startswith('animeromaji='): animeromaji = arg[12:].split()
        if arg.startswith('songname='): songname = arg[9:].split()
        if arg.startswith('artist='): artist = arg[7:].split()
        if arg.startswith('type='):
            type_ = arg[5:].lower()
            assert re.compile(r'op\d*|ed\d*|in\d*').match(type_)
            number = type_[2:]
            wordmap = {'op':'Opening','ed':'Ending','in':'Insert'}
            if number and type_[:2] != 'in':
                typeRegex = re.compile(wordmap[type_[:2]]+' '+number)
            else:
                typeRegex = re.compile(wordmap[type_[:2]]+'.*')
        if arg.startswith('correct<'): correctHi = int(arg[8:])
        if arg.startswith('correct>'): correctLo = int(arg[8:])
        if arg.startswith('players<'): playersHi = int(arg[8:])
        if arg.startswith('players>'): playersLo = int(arg[8:])
        if arg.startswith('ratio<'): ratioHi = float(arg[6:])
        if arg.startswith('ratio>'): ratioLo = float(arg[6:])
        if arg.startswith('dateold='): dateold = arg[8:]
        if arg.startswith('datenew='): datenew = arg[8:]
    
    assert re.compile(r'\d{4}-\d\d-\d\d').match(dateold)
    assert re.compile(r'\d{4}-\d\d-\d\d').match(datenew)
    
    animeeng = [word.lower() for word in animeeng]
    animeromaji = [word.lower() for word in animeromaji]
    songname = [word.lower() for word in songname]
    artist = [word.lower() for word in artist]
    
    if debug:
        print('animeeng =',animeeng)
        print('animeromaji =',animeromaji)
        print('songname =',songname)
        print('artist =',artist)
    
    results = []
    
    for match in data:
        if match['date'] <= dateold or match['date'] >= datenew:
            continue
        for song in match['data']:
            if any(word not in song['animeEng'].lower()
                    for word in animeeng):
                continue
            if any(word not in song['animeRomaji'].lower()
                    for word in animeromaji):
                continue
            if any(word not in song['songName'].lower()
                    for word in songname):
                continue
            if any(word not in song['artist'].lower()
                    for word in artist):
                continue
            if not typeRegex.match(song['type']):
                continue
            if song['correct'] <= correctLo:
                continue
            if song['correct'] >= correctHi:
                continue
            if song['players'] <= playersLo:
                continue
            if song['players'] >= playersHi:
                continue
            if song['correct']/song['players'] <= ratioLo:
                continue
            if song['correct']/song['players'] >= ratioHi:
                continue
            results.append({'date':match['date'],
                            'region':match['region'],
                            'song':song})
    return results

if __name__ == '__main__':
    sys.stderr.write('loading data...\n')
    data = amq_loader.read_ranked_data(None,True)
    #amq_loader.clean_ranked_data(data)
    sys.stderr.write('done loading\n')
    sys.stderr.write('running query...\n')
    query = queryRankedData(data,sys.argv[1:])
    sys.stderr.write('done querying\n')
    print(json.dumps(query,indent=4))

