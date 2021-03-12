# random-amq
a place for me to mess around with amq stuff (animemusicquiz.com)

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

The `amq_loader.py` script still work in progress, but the intention is to load
and clean the data. Some of these JSON files, especially older ones, are
formatted a bit differently and have difficulties that may have to be worked
with. For example, some older ones have English/Romaji name but not both.
Additionally, AMQ may have changed the names of some entries in their database
since these files were created.
