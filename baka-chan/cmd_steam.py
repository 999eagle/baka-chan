import asyncio

import globals
from command import Command
from util import *
from errors import *

@Command('steam', help = 'Displays some information about a Steam user.', usage = ('info','<steamid:str>'))
async def cmd_steam(message, steamid):
	try:
		info = globals.api_steam.get_user_info(steamid)
	except SteamDataException as e:
		await send_message(message.channel, e.text)
		return

	personastates=('Offline','Online','Busy','Away','Snooze','Looking to trade','Looking to play')

	text = ''
	text += '**Profile Name:** {0}\n'.format(info['personaname'])
	text += '**Steam ID:** {0}\n'.format(info['steamid'])
	text += '**URL:** {0}\n'.format(info['profileurl'])
	text += '\n'
	text += '**Status:** {0}\n'.format(personastates[info['personastate']])
	text += '**Calculator:** http://steamdb.info/calculator/{0}/\n'.format(info['steamid'])

	await send_message(message.channel, text)

@Command('csgo', help = 'Displays a summary of the CS:GO stats of a player or a random single stat about that player.', usage = ('stats','<steamid:str>',('optional','r')))
async def cmd_csgo(message, steamid, r):
	try:
		stats = globals.api_steam.get_user_stats_730(steamid)
	except SteamDataException as e:
		await send_message(message.channel, e.text)
		return

	if r == True:
		# display a random stat
		randstat = None
		max = len(stats) - 1
		while randstat == None:
			randstat = stats[random.randint(0, max)]
			if not randstat['name'] in csgo_randomstattexts:
				randstat = None
		value = randstat['value']
		if randstat['name'] == 'total_time_played':
			sec = value % 60
			value = (value - sec) / 60
			min = value % 60
			value = (value - min) / 60
			hour = value % 24
			days = (value - hour) / 24
			value = '{0}d {1}h {2}min'.format(int(days), int(hour), int(min))
		await send_message(message.channel, steamid + ' ' + csgo_randomstattexts[randstat['name']].format(value))
	else:
		# display a summary
		stats = cmd_csgo_usefulstats(stats)
		text = '**Total stats**\nKills: {0}, Deaths: {1}, K/D: {2:.2f}, Headshots: {3}, Accuracy: {4:.2f}%, MVPs: {5}, Bombs defused: {6}, Bombs planted: {7}\n\n**Last match**\nKills: {8}, Deaths: {9}, K/D: {10:.2f}, MVPs: {11}, Favourite weapon: {12}'
		text = text.format(stats['tkill'], stats['tdeath'], stats['tkd'], stats['theadshot'], stats['taccuracy'] * 100, stats['tmvp'], stats['tbombd'], stats['tbombp'], stats['lmkill'], stats['lmdeath'], stats['lmkd'], stats['lmmvp'], stats['lmfavweapon'])
		await send_message(message.channel, text)

# source: https://tf2b.com/itemlist.php?gid=730
csgo_weapons = ('','Desert Eagle','Dual Berettas','Five-SeveN','Glock-18','','','AK-47','AUG','AWP',
                'FAMAS','G3SG1','','Galil AR','M249','','M4A1','MAC10','','P90',
                '','','','','UMP-45','XM1014','PP-Bizon','MAG-7','Negev','Sawed-Off',
                'Tec-9','Zeus x27','P2000','MP7','MP9','Nova','P250','','SCAR-20','SG 553',
                'SSG 08','','Knife','Flashbang','HE Grenade','Smoke Grenade','Molotov','Decoy Grenade','Incendiary Grenade','C4 Explosive')
csgo_randomstattexts = {'total_time_played':'played {0}!',
                        'total_matches_won':'won {0} matches!',
                        'total_damage_done':'dealt {0} damage in total!',
                        'total_money_earned':'earned ${0}!',
                        'total_kills_knife':'killed {0} enemies with the Knife!',
                        'total_kills_hegrenade':'killed {0} enemies with the HE-Grenade!',
                        'total_kills_glock':'killed {0} enemies with the Glock-18!',
                        'total_kills_deagle':'killed {0} enemies with the Deagle!',
                        'total_kills_elite':'killed {0} enemies with the Dualies!',
                        'total_kills_fiveseven':'killed {0} enemies with the 5-7!',
                        'total_kills_xm1014':'killed {0} enemies with the XM1014!',
                        'total_kills_mac10':'killed {0} enemies with the MAC10!',
                        'total_kills_ump45':'killed {0} enemies with the UMP-45!',
                        'total_kills_p90':'killed {0} enemies with the P90!',
                        'total_kills_awp':'killed {0} enemies with the AWP!',
                        'total_kills_ak47':'killed {0} enemies with the AK-47!',
                        'total_kills_aug':'killed {0} enemies with the AUG!',
                        'total_kills_famas':'killed {0} enemies with the FAMAS!',
                        'total_kills_g3sg1':'killed {0} enemies with the G3SG1!',
                        'total_kills_m249':'killed {0} enemies with the M249!',
                        'total_kills_hkp2000':'killed {0} enemies with the P2000!',
                        'total_kills_p250':'killed {0} enemies with the P250!',
                        'total_kills_sg556':'killed {0} enemies with the SG-556!',
                        'total_kills_scar20':'killed {0} enemies with the SCAR-20!',
                        'total_kills_ssg08':'killed {0} enemies with the Scout!',
                        'total_kills_mp7':'killed {0} enemies with the MP7!',
                        'total_kills_mp9':'killed {0} enemies with the MP9!',
                        'total_kills_nova':'killed {0} enemies with the Nova!',
                        'total_kills_negev':'killed {0} enemies with the NEGEV!',
                        'total_kills_sawedoff':'killed {0} enemies with the Sawed-Off!',
                        'total_kills_bizon':'killed {0} enemies with the PP-Bizon!',
                        'total_kills_tec9':'killed {0} enemies with the Tec-9!',
                        'total_kills_mag7':'killed {0} enemies with the MAG-7!',
                        'total_kills_m4a1':'killed {0} enemies with the M4A1-S!',
                        'total_kills_galilar':'killed {0} enemies with the Galil AR!',
                        'total_kills_molotov':'killed {0} enemies with the Molotov!',
                        'total_kills_taser':'killed {0} enemies with the Zeus!',
                        'total_kills_headshot':'killed {0} enemies with headshots!',
                        'total_kills_enemy_weapon':'killed {0} enemies with their own weapons!',
                        'total_wins_pistolround':'won {0} Pistolrounds!',
                        'total_wins_map_de_aztec':'won {0} matches on Aztec!',
                        'total_wins_map_de_cbble':'won {0} matches on Cobble!',
                        'total_wins_map_de_dust2':'won {0} matches on Dust2!',
                        'total_wins_map_de_dust':'won {0} matches on Dust!',
                        'total_wins_map_de_inferno':'won {0} matches on Inferno!',
                        'total_wins_map_de_nuke':'won {0} matches on Nuke!',
                        'total_wins_map_de_train':'won {0} matches on Train!',
                        'total_weapons_donated':'donated {0} weapons to teammates!',
                        'total_broken_windows':'broke {0} windows!',
                        'total_kills_knife_fight':'won {0} knife fights!',
                        'total_kills_against_zoomed_sniper':'killed {0} aiming enemy snipers!',
                        'total_shots_fired':'fired {0} shots in total!',
                        'total_rounds_played':'played {0} rounds!'
                        }

def cmd_csgo_usefulstats(stats):
	out_stats = {}
	for stat in stats:
		if stat['name'] == 'total_kills':
			out_stats.setdefault('tkill', stat['value'])
		elif stat['name'] == 'total_deaths':
			out_stats.setdefault('tdeath', stat['value'])
		elif stat['name'] == 'total_shots_fired':
			out_stats.setdefault('tshot', stat['value'])
		elif stat['name'] == 'total_shots_hit':
			out_stats.setdefault('thit', stat['value'])
		elif stat['name'] == 'total_kills_headshot':
			out_stats.setdefault('theadshot', stat['value'])
		elif stat['name'] == 'total_planted_bombs':
			out_stats.setdefault('tbombp', stat['value'])
		elif stat['name'] == 'total_defused_bombs':
			out_stats.setdefault('tbombd', stat['value'])
		elif stat['name'] == 'total_mvps':
			out_stats.setdefault('tmvp', stat['value'])
		elif stat['name'] == 'last_match_kills':
			out_stats.setdefault('lmkill', stat['value'])
		elif stat['name'] == 'last_match_deaths':
			out_stats.setdefault('lmdeath', stat['value'])
		elif stat['name'] == 'last_match_mvps':
			out_stats.setdefault('lmmvp', stat['value'])
		elif stat['name'] == 'last_match_favweapon_id':
			out_stats.setdefault('lmfavweapon', csgo_weapons[stat['value']])
	out_stats.setdefault('taccuracy', out_stats['thit'] / out_stats['tshot'])
	out_stats.setdefault('tkd', out_stats['tkill'] / out_stats['tdeath'])
	out_stats.setdefault('lmkd', out_stats['lmkill'] / out_stats['lmdeath'])
	return out_stats
