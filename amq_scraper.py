'''
Scraper to download the JSON files containing AMQ ranked match data. Parses from
.csv files in the "sheets" subdirectory of the working directory. This is
compatible with the .csv files from download as .csv on google sheets.

Assertion is used, expecting things to be formatted consistently. These are to
try to prevent the scraper from doing something wrong if there is an issue.

Sometimes the downloaded JSON files have issues (out of your control) and need
to be fixed. This may need to be done manually because code cannot accommodate
all possible issues that may show up.

Structure/format of the resulting output:
<output dir>/amq_<year>s<season>_<day>_<date>_<region>_.json

Spreadsheet link:
https://docs.google.com/spreadsheets/d/1g0jW7k-GJiHueQ0ZVYe4WilupnUkBYLVlbB9GEdqQ98/
'''

if __name__ != '__main__': quit() # only run scraper as main

import bs4
import csv
import json
import os
import re
import requests
import sys

if len(sys.argv) != 3:
    print('usage: amq_scraper.py <sheet csv> <output dir>')
    quit()

# sheet data to process
sheet = sys.argv[1]

# dir to store output in
outdir = os.path.normpath(sys.argv[2])

if not os.path.isdir(outdir):
    os.mkdir(outdir)

# \d{4} is 4 digit year, \d\d? is 1 or 2 digit season number
re_sheet_name = re.compile(r'Ranked AMQ Data Links - (\d{4}) S(\d\d?).csv')

# mm/dd/yyyy date format
re_date_mmddyyyy = re.compile(r'(\d\d?)/(\d\d?)/(\d{4})')

# pastebin url with the paste ID at the end
# replace last / with /raw/ to get the url for download
re_url_pastebin = re.compile(r'https?://(www\.)?pastebin.com/\w+')

# github gist url with the ID at the end
# getting the raw url requires finding it in the html
re_url_gistgithub = re.compile(r'https?://gist.github.com/\w+')

def get_year_and_season(sheet):
    ''' returns tuple of 2 integers '''
    return (int(sheet[24:28]),int(sheet[30:sheet.find('.')]))

# if more sites are needed in the future, might be good to design this to try
# several scrapers, each with a url regex and a scraper function
def download_url(link):
    ''' returns (success_bool, result_str)
    if successful, result_str is json data, otherwise it is error message '''
    link = link.strip()
    
    # pastebin.com
    if re_url_pastebin.fullmatch(link):
        # get index of last / in the url
        i = len(link)-1
        while link[i] != '/': i -= 1
        # construct link to raw pastebin data
        link_raw = link[:i] + '/raw' + link[i:]
        
    # gist.github.com
    elif re_url_gistgithub.fullmatch(link):
        # first get the page that is linked
        request = requests.get(link)
        if not request.ok:
            return (False,'error extracting link to raw from url: "%s"'%link)
        page = bs4.BeautifulSoup(request.text,'html.parser')
        # find the buttons that link to the raws
        raws = [a for a in page.find_all('a')
                if a.text.lower().strip() == 'raw']
        if len(raws) == 0:
            return (False,'did not find a raw link on url: "%s"'%link)
        # assume desired json is the first raw link
#        if len(raws) != 1 or (not raws[0].has_attr('href')):
#            return (False,'did not find exactly 1 raw link on url: "%s"'%link)
        # get the href attribute that links to the raw json
        link_raw = raws[0]['href']
        # these href may be absolute on the server (starting with /)
        if link_raw.startswith('/'):
            link_raw = 'https://gist.github.com' + link_raw
    
    # unsupported
    else:
        return (False, 'unsupported url: "%s"'%link)
        
    # use link_raw to get the json data
    request = requests.get(link_raw)
    if request.ok:
        return (True,request.text)
    else:
        return (False,'error fetching raw url: "%s"'%link_raw)

def json_valid(data):
    try:
        data = json.loads(data)
        return True
    except:
        return False

def json_fixer(data):
    ''' handle some basic/common issues that occur in the data
    if the input is invalid json then it may return a different output
    output may not be valid json because not all issues can be fixed by code
    return (success,data)'''
    if json_valid(data):
        return (True,data)
    # TODO implement
    return (False,data)

REGIONS = ['east','central','west']

def process_sheet(sheet):
    ''' goes through the links in the sheet to collect the ranked data
    if the file does not exist, it tries to download it
    the validity of the json output is checked afterward'''
    print('='*40)
    print('===','processing file:',sheet)
    # extract sheet name
    i = len(sheet)-1
    while i >= 0 and sheet[i] != '/': i -= 1
    sheet_file_name = sheet[i+1:]
    # check sheet name
    sheet_match = re_sheet_name.fullmatch(sheet_file_name)
    if not sheet_match:
        print('===','ERROR file name does not match regex')
        return
    year,season = sheet_match.groups()
    year,season = int(year),int(season)
    print('===','year:',year)
    print('===','season:',season)
    
    print('parsing csv...')
    
    # read csv file and extract information
    rows = list(csv.reader(open(sheet,'r')))
    assert len(rows) >= 2, 'no header rows'
    if len(rows) not in [29,36]:
        print('===','WARNING number of rows may be incorrect for season')
    assert rows[1][0].strip().lower() == 'day', 'header row day/date expected'
    assert rows[1][1].strip().lower() == 'date', 'header row day/date expected'
    
    # for each region find leftmost column with its data
    region_col = dict() # map region -> leftmost column
    for i,cell in enumerate(rows[0]):
        cell = cell.strip().lower()
        if cell == '': continue
        assert cell in REGIONS, 'invalid region: %s'%cell
        assert cell not in region_col, 'duplicate region: %s'%cell
        assert i >= 2, 'region %s is in first 2 columns'%cell
        region_col[cell] = i
    
    # find the songlist column for each region
    songlist_col = dict() # map region -> column with its song list
    for region in region_col:
        col = region_col[region]
        other_region_cols = set(region_col.values())
        other_region_cols.remove(col)
        # search cols for this region, end once reaching another region
        while col < len(rows[1]) and (col not in other_region_cols):
            if rows[1][col].strip().lower() == 'songlist':
                assert region not in songlist_col, \
                        'ambiguous songlist col for region %s'%region
                songlist_col[region] = col
            col += 1
    
    print('processing files...')
    
    # starting on row 2: expect day,date, then extract url with songlist_col
    for i in range(2,len(rows)):
        day,date = rows[i][:2]
        if day.strip().lower() == 'championship':
            day = 0
        else:
            day = int(day)
            assert day+1 == i, 'ranked day numbers in incorrect order'
        m,d,y = re_date_mmddyyyy.fullmatch(date.strip()).groups()
        m,d,y = int(m),int(d),int(y)
        assert 1<=m<=12 and 1<=d<=31, 'invalid date: '+date.strip()
        
        # process each region for this date
        for region in songlist_col:
            filename = 'amq_%ds%02d_%s_%d-%02d-%02d_%s.json' \
                        %(year,season,'ch' if day == 0 else '%02d'%day,
                            y,m,d,region)
            
            # if file is downloaded, check json
            if os.path.exists(outdir+'/'+filename):
                data = open(outdir+'/'+filename,'r').read()
                if json_valid(data):
                    redump = json.dumps(json.loads(data),indent=4)
                    if redump != data: # rewrite file with json reformatted
                        file = open(outdir+'/'+filename,'w')
                        file.write(redump)
                        file.close()
                        print('exists,reformatted:',filename)
                    else:
                        print('exists,done:',filename)
                else:
                    success,data = json_fixer(data)
                    if success:
                        print('exists,done:',filename)
                    else:
                        print('JSON ERROR:',filename)
                continue
            
            # download nonexisting file if available
            url = rows[i][songlist_col[region]].strip()
            if url == '':
                print('not available:',filename)
                continue
            success,result = download_url(url)
            if not success:
                print('FAILED DOWNLOAD:',filename,'MESSAGE:',result)
            else:
                success,result = json_fixer(result)
                file = open(outdir+'/'+filename,'w')
                if success:
                    file.write(json.dumps(json.loads(result),indent=4))
                    print('success:',filename)
                else:
                    file.write(result)
                    print('JSON ERROR:',filename)
                file.close()

try:
    process_sheet(sheet)
    print('===','DONE')
except Exception as e:
    print('===','ERROR parsing file "%s"'%sheet)
    print('===',type(e).__name__+':',str(e))

