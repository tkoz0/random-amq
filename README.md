# random-amq
a place for me to mess around with amq stuff (animemusicquiz.com)

this file needs to be updated at some point but laziness...

## ranked data

Spreadsheet with the ranked data JSON files:
https://docs.google.com/spreadsheets/d/1g0jW7k-GJiHueQ0ZVYe4WilupnUkBYLVlbB9GEdqQ98/

The `ranked_data_zip` directory contains monthly/seasonally zip files with all
the JSON files for that month/season.

The 2 scripts are meant to download all the ranked data listed in the
spreadsheet and conveniently load it for analysis/usage. The scraping part is
mostly handled well, but data cleaning/reformatting is still work in progress.

To download the JSON files, go on the google sheet and use File -> Download ->
CSV. Then use the saved CSV files in the `amq_scraper.py` script to get the JSON
files. The usage is: `amq_scraper.py <sheet csv> <output dir>`

Some older files may contain JSON errors that have to be corrected manually.
However, if you download the JSON files from this repo rather than scraping them
again, I should have those issues taken care of. Another issue is that some
links to older JSON files are now dead, but you can still get them here.

The `amq_loader.py` script has 2 functions: 1 for loading all ranked files from
a directory and 1 for reformatting the data to make it consistent. Documentation
for these is in `amq_loader.py`. The `clean_ranked_data` function will work the
way I intended only if you follow the details below about which files I decided
to exclude. As of now, I cannot be 100% sure the data is completely ready.

### data to use

Upon further inspection, I decided to drop some of the early data that is
missing total player count. The percent of players guessing correctly is
important to analysis so correct player count does not mean a lot without also
having the total number of players. Also, many of these older files are missing
video links and only provide 1 anime name (appears to be English). These were
probably collected with older versions of the userscripts.

The list of files I am dropping for ease of analysis are:
- everything in `amq_2019s03` (2019 season 3)
- everything in `amq_2020s01` (2020 season 1)
- the following in `amq_2020s02` (2020 season 2)
  - `amq_2020s02_01_2020-01-27_central.json`
  - `amq_2020s02_01_2020-01-27_west.json`
  - `amq_2020s02_02_2020-01-28_west.json`
  - `amq_2020s02_03_2020-01-29_west.json`
  - `amq_2020s02_04_2020-01-30_west.json`

What remains should be consistent enough for the desirable percent correct
analysis I am planning on. The only issue I see remaining is some of the files
not having all 75 songs (not surprising because AMQ is often unreliable and you
may get disconnected even with a good internet connection). Most of the time
only a few are missing so it should not be a big problem for analysis. The
bigger issue is several ranked matches missing in older seasons which I cannot
do anything about.
