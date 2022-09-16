import json
import lzma
import sys
sys.stderr.write('reading database...\n')
db = json.loads(lzma.open('db.json.xz','rt').read())
sys.stderr.write(f'done reading ({len(db)} links)\n')
link_readers = [
    lambda x : x,
    lambda x : f'https://files.catbox.moe/{x}.webm',
    lambda x : f'https://files.catbox.moe/{x}.mp3'
]
while True:
    try:
        link = input()
    except:
        break
    any_worked = False
    for lr in link_readers:
        link2 = lr(link)
        try:
            data = db[link2]
            print(f'LINK = {repr(link2)}')
            print(json.dumps(data,indent=4))
            any_worked = True
            break
        except:
            pass
    if not any_worked:
        sys.stderr.write(f'could not understand link: {link}\n')
