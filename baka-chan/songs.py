# -*- coding: utf-8 -*-
import asyncio

from util import *

_songs = (
	('What is love?', 'Baby don\'t hurt me', 'Don\'t hurt me', 'No more'),
	('Never gonna give you up', 'Never gonna let you down', 'Never gonna run around and desert you', 'Never gonna make you cry', 'Never gonna say goodbye', 'Never gonna tell a lie and hurt you'),
	('I\'m blue', 'Da ba dee da ba daa'),
	('And I know why', 'Coz I got high'),
	('I wanna be the very best', 'Like no one ever was', 'To catch them is my real test', 'To train the is my cause',
	 'I will travel across the land', 'Searching far and wide', 'Each Pokémon to understand', 'The power that\'s inside',
	 'Pokémon, gotta catch \'em all!',
	 'It\'s you and me', 'I know it\'s my destiny', 'Pokémon, oh, you\'re my best friend', 'In a world we must defend', 'Pokémon, gotta catch \'em all', 'A heart so true', 'Our courage will pull us through',
	 'You teach me and I\'ll teach you', 'Pokémon, gotta catch \'em all', 'Gotta catch \'em all', 'Yeah'),
	('Po-a-mon', '(Tötet sie alle!)'),
	('It\'s beginning to look a lot like murder', 'Everywhere you go!','Senpai\'s bothersome childhood friend','Is flirting with him again','She wants him, but I\'ll never let him go!','It\'s beginning to look a lot like murder','Lots of blood and gore!','But the prettiest sight to see is Senpai beneath a tree','The boy I adore!',
	 'A rusty pipe made of lead and a blow to the head','Will take care of Kokona-chan!','A shiny sharp axe and one glorious whack','To eliminate Osana-chan!','Oh, golly, I can hardly wait for school to start again!',
	 'It\'s beginning to look a lot like murder','Everywhere you go!','Well I could send her straight to hell','Or just get her expelled','Stab her quick or gut her nice and slow!','It\'s beginning to look a lot like murder','Killing is an art!','Won\'t you please stop your struggling','You know I just want one thing','To carve out your heart!'),
)

# save for each channel how far the channel is into a song to allow multiple lines to be the same
_song_states = {}

def normalize_lyrics(s):
	return s.lower().rstrip(' !.?').replace(',', '').replace('\'', '').replace('é', 'e')

async def song_timeout(channel_id, song_idx, line_idx):
	await asyncio.sleep(120)
	if _song_states[channel_id][song_idx] == line_idx:
		del _song_states[channel_id][song_idx]

async def try_sing(message):
	channel_state = _song_states.get(message.channel.id, {})
	for song_idx in range(len(_songs)):
		song = _songs[song_idx]
		line_idx = channel_state.get(song_idx, 0)
		# at least two lines must still be in the song to be useful, if there aren't just check the next song
		if line_idx >= len(song) - 1:
			continue
		line = song[line_idx]
		if normalize_lyrics(message.content).endswith(normalize_lyrics(line)):
			await send_message(message.channel, song[line_idx + 1] + ' :notes:')
			if message.channel.id not in _song_states:
				_song_states[message.channel.id] = {song_idx: line_idx + 2}
			else:
				_song_states[message.channel.id][song_idx] = line_idx + 2
			asyncio.ensure_future(song_timeout(message.channel.id, song_idx, line_idx + 2))
			break
