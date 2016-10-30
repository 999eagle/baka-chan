import globals

import cmd_general
import cmd_bc_games
import cmd_rps
if globals.config.has_steam_api_key:
	import cmd_steam
import cmd_admin
