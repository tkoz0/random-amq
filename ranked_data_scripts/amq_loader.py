'''
Reads all the files from:
<dir>/amq_<year>s<season>_<day>_<date>_<region>_.json

Specify <dir> as single command line argument.

Produces an object containing all the ranked AMQ data stored.
'''

import bz2 # significantly better than gzip but not very slow
import json
import os
import pickle
import re
import sys

re_fname = re.compile(r'amq_(\d{4})s(\d\d)_(ch|\d\d)_(\d{4})-(\d\d)-(\d\d)_'
                       '(east|central|west)\.json')

# recursively build a list of every file in the input dir
def all_files(file):
    if os.path.isfile(file):
        return [file]
    elif os.path.isdir(file):
        files = sorted(os.listdir(file))
        filelists = [all_files(file+'/'+f) for f in files]
        return sum(filelists,[])
    else: return []

# map attributes in reformatted to those in original data
# different scrypt versions may name them differently
attr_mapping = \
{
    'animeEng': ['animeEng','animeEnglish'],
    'animeRomaji': ['animeRomaji'],
    'songName': ['songName'],
    'artist': ['artist'],
    'type': ['type'],
    'linkWebm': ['LinkVideo','linkWebm'],
    'linkMp3': ['LinkMp3'], # may not be present
    'start': ['startTime','startSample'], # may not be present
    'length': ['songDuration','videoLength'], # may be null
    'correct': ['correctCount'],
    'players': ['activePlayers','activePlayerCount','totalPlayers']
}

# attributes allowing null value for when it is not found
# all other missing attributes will cause an error
attr_nulls = \
{
    'linkMp3', # video could be uploaded but mp3 not created yet
    'start'
}

def clean_ranked_data(data):
    '''
    Changes the song format to use these attributes:
    
    animeEng, animeRomaji, songName, artist, type, correct, link
    
    correct = (correct guesses) / (total players)
    link = video link (webm)
    others are the same as in the given data
    
    The given argument is modified in place
    '''
    for match in data:
        for i,song in enumerate(match['data']):
            cleaned = dict()
            missing = []
            for attr in attr_mapping:
                for attr_old in attr_mapping[attr]:
                    if attr_old in song:
                        cleaned[attr] = song[attr_old]
                        break
                if attr not in cleaned: # cannot find
                    if attr in attr_nulls:
                        cleaned[attr] = None
                    else:
                        missing.append(attr)
            if len(missing) > 0:
                print('cannot convert %ds%02d %s %s'
                    %(match['year'],match['season'],
                    'ch' if match['number'] == -1 else '%02d'%match['number'],
                    match['region']))
                print('    cannot get:',missing)
            else:
                match['data'][i] = cleaned

def read_ranked_data(dir,use_cached_obj=False,store_cached_obj=True):
    '''
    Returns a list containing ranked objects (type dict) that look like:
    {
        "region": "western"
        "year": 2020
        "season": 11
        "number": 20 # -1 for championship to keep the type consistent
        "date": "2020-11-21"
        "data": [object read from the JSON file on disk]
    }
    May store/read the data from "ranked_data.pickle" to speed things up
    depending on the options provided
    '''
    if use_cached_obj and os.path.isfile('ranked_data.pickle.bz2'):
        data = pickle.load(bz2.BZ2File('ranked_data.pickle.bz2','rb'))
        return data
    
    filelist = all_files(dir)
    data = []
    
    # process files in the directory
    for file in filelist:
        i = len(file)-1
        while i >= 0 and file[i] != '/': i -= 1 # find last /
        year,season,num,y,m,d,region = re_fname.fullmatch(file[i+1:]).groups()
        obj = dict()
        obj['region'] = region
        obj['year'] = int(year)
        obj['season'] = int(season)
        obj['number'] = -1 if num == 'ch' else int(num)
        obj['date'] = '%s-%s-%s'%(y,m,d)
        obj['data'] = json.loads(open(file,'r').read())
        data.append(obj)
    
    # clean data as well to finish processing
    clean_ranked_data(data)

    if store_cached_obj:
        pickle.dump(data,bz2.BZ2File('ranked_data.pickle.bz2','wb'))
    
    return data

if __name__ == '__main__':
    print('reading ranked data')
    data = read_ranked_data(sys.argv[1])
    print('done reading')
    print(len(data),'ranked files loaded')
    print(sum(len(match['data']) for match in data),'songs loaded')

