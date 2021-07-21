'''
Python program to read all the JSON files and identify missing information.

The important song information might be identified by different (but similar)
keys. See the if statements in the check_file function for details.

After removing the files listed in README.md (the old ones with missing stuff)
this program should show no issues for most and fewer than 75 songs for some.
'''

import json
import os
import sys

in_dir = os.path.normpath(sys.argv[1])

# recursively build a list of every file in the input dir
def all_files(file):
    if os.path.isfile(file):
        return [file]
    elif os.path.isdir(file):
        files = sorted(os.listdir(file))
        filelists = [all_files(file+'/'+f) for f in files]
        return sum(filelists,[])
    else: return []

ranked_files = all_files(in_dir)
print('input:',len(ranked_files),'files')

# ignore these, they were used for testing something dumb
song_keys = set(['animeEng','animeRomaji','songName','artist','type','correctCount','startTime','songDuration','songNumber','activePlayerCount','LinkVideo','LinkMp3'])
req_keys = set(['animeEng','animeRomaji','songName','artist','type','correctCount','activePlayers','LinkVideo','LinkMp3'])

# searches for issues and returns list of strings describing them
def check_file(file):
    issues = []
    data = json.loads(open(file,'r').read())
    if len(data) != 75:
        issues.append('%d != 75 songs'%len(data))
    attr_missing = dict() # map attr missing to song index
    # go backwards so earliest occurrence overwrites in attr_missing dictionary
    for i,song in ((j,data[j]) for j in range(len(data)-1,-1,-1)):
        if ('animeEng' not in song) and ('animeEnglish' not in song):
            #issues.append('(index %d) no animeEng or animeEnglish'%i)
            attr_missing['animeEng/animeEnglish'] = i
        if 'animeRomaji' not in song:
            #issues.append('(index %d) no animeRomaji'%i)
            attr_missing['animeRomaji'] = i
        if 'songName' not in song:
            #issues.append('(index %d) no songName'%i)
            attr_missing['songName'] = i
        if 'artist' not in song:
            #issues.append('(index %d) no artist'%i)
            attr_missing['artist'] = i
        if 'type' not in song:
            #issues.append('(index %d) no type'%i)
            attr_missing['type'] = i
        if 'correctCount' not in song:
            #issues.append('(index %d) no correctCount'%i)
            attr_missing['correctCount'] = i
        if ('activePlayers' not in song) and ('activePlayerCount' not in song) and ('totalPlayers' not in song):
            #issues.append('(index %d) no activePlayers or activePlayerCount or totalPlayers'%i)
            attr_missing['activePlayers/activePlayerCount/totalPlayers'] = i
        if ('LinkVideo' not in song) and ('linkWebm' not in song):
            #issues.append('(index %d) no LinkVideo or linkWebm'%i)
            attr_missing['LinkVideo/linkWebm'] = i
        # should always have video/webm link which is more important than mp3
        #if 'LinkMp3' not in song:
        #    return '(index %d) no LinkMp3'%i
    # add issue for each one
    for attr in attr_missing:
        issues.append('(index %d) no %s'%(attr_missing[attr],attr))
    return issues

# show issues in each file, === just makes it easier to find where lines start
for file in ranked_files:
    issues = check_file(file)
    if len(issues) > 0:
        print('===',file,issues)
