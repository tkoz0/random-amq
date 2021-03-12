'''
Reads all the files from:
ranked_data/amq_<year>s<season>_<day>_<date>_<region>_.json

Produces an object containing all the ranked AMQ data stored.
'''

import bz2 # significantly better than gzip but not very slow
import json
import os
import pickle
import re

re_fname = re.compile(r'amq_(\d{4})s(\d\d)_(ch|\d\d)_(\d{4})-(\d\d)-(\d\d)_'
                       '(east|central|west)\.json')

def read_ranked_data(use_cached_obj=False,store_cached_obj=True):
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
    
    filelist = os.listdir('ranked_data')
    data = []
    
    # process files in the directory
    for file in filelist:
        year,season,number,y,m,d,region = re_fname.fullmatch(file).groups()
        obj = dict()
        obj['region'] = region
        obj['year'] = int(year)
        obj['season'] = int(season)
        obj['number'] = -1 if number == 'ch' else int(number)
        obj['date'] = '%s-%s-%s'%(y,m,d)
        obj['data'] = json.loads(open('ranked_data/'+file,'r').read())
        data.append(obj)
    
    if store_cached_obj:
        pickle.dump(data,bz2.BZ2File('ranked_data.pickle.bz2','wb'))
    
    return data

def clean_ranked_data():
    '''
    Not implemented yet. Intention is to format the object returned from
    read_ranked_data() consistently since the scraped JSON files might come from
    different (versions of a) userscript(s) and structure their data a bit
    differently. This might be challenging to get right and it might not be
    feasible to handle every case of inconsistency.
    '''

if __name__ == '__main__':
    print('testing')
    data = read_ranked_data(True)
    print(len(data),'ranked files loaded')
    print(data[0])
    print('done')

