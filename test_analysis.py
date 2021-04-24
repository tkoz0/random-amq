import amq_loader

data = amq_loader.read_ranked_data('ranked_data',True,False)
amq_loader.clean_ranked_data(data)

animes = dict()
songs = dict()

for match in data:
    for song in match['data']:
        if song['animeRomaji'] in animes:
            animes[song['animeRomaji']] += 1
        else:
            animes[song['animeRomaji']] = 1
        if (songtuple := (song['songName'],song['artist'])) in songs:
            songs[songtuple] += 1
        else:
            songs[songtuple] = 1

animes_top = sorted(((a,animes[a]) for a in animes),key=lambda x:-x[1])
songs_top = sorted(((s,songs[s]) for s in songs),key=lambda x:-x[1])

print('animes')
for a in animes_top[:20]:
    print('%03d'%a[1],a[0])

print()
print()

print('songs')
for s in songs_top[:50]:
    print('%03d'%s[1],s[0][0],'by',s[0][1])
