### Constants

DIR_UP = 1 
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4
DIR_NOWHERE = -1

### Cell Type - describes the appearance and behavior of a MadCell object
CELL_TYPE_BLANK = 0
CELL_TYPE_ADMIRAL = 1 # fastest growth rate, regardless of tide. One is by default assigned to each entity, and can also be created by combining 5 ships into 1
CELL_TYPE_MOUNTAIN = 2
CELL_TYPE_SHIP = 3
CELL_TYPE_SHIP_2 = 32 # combine 2 ships to make this. Increased growth rate
CELL_TYPE_SHIP_3 = 33 # combine 1 ship_2 with a ship to make this. Increased growth rate
CELL_TYPE_SHIP_4 = 34 # combine 2 ship_2s or 1 ship_3 and 1 ship to make this. Increased growth rate
CELL_TYPE_SWAMP = 4
CELL_TYPE_MOUNTAIN_CRACKED = 5
CELL_TYPE_MOUNTAIN_BROKEN = 6
##Not implemented (yet, anyway)
# CELL_TYPE_PUP_UNKNOWN = 7 # an unopened powerup!
# CELL_TYPE_PUP_FOG_OF_WAR_LIFTED = 8 # briefly lift fog of war (seed will determine duration - with a chance of it lasting all game)
# CELL_TYPE_PUP_FAR_SIGHT = 9 # increases the distance the player can see (duration via seed)
# CELL_TYPE_PUP_GROWTH_MULTIPLIER = 10 # increases or decreases the player's spawn rates across all cell types! duration and multiplier via seed.. perhaps allow multipliers between 0 and 1 to reduce generation.. and even negative to cause troops to shrink! 
# CELL_TYPE_PUP_POISON = 11 # if ALL player cells lose, eg. 1 troop per 2 turns for 25 turns, it makes sense to use the 'shore up' functionality to reduce number of cells temporarily

GAME_STATUS_INIT = -1 # loading
GAME_STATUS_READY = 1 # able to start
GAME_STATUS_IN_PROGRESS = 2 #
GAME_STATUS_PAUSE = 3 #
GAME_STATUS_GAME_OVER_WIN = 4 # game instance is complete and can no longer be played
GAME_STATUS_GAME_OVER_LOSE = 5 # game instance is complete and can no longer be played

GAME_MODE_FFA = 1
GAME_MODE_FFA_CUST = 2
GAME_MODE_REPLAY = 3

ACTION_MOVE_NORMAL = 1
ACTION_MOVE_HALF = 2
ACTION_MOVE_ALL = 3
ACTION_MOVE_CITY = 4
ACTION_MOVE_NONE = 5
ACTION_CHARGE = 777 # idea: start a chain of move_normals that extends to the edge of the board (or until it hits a barrier)
    
ACTION_QUEUE_MAX_SIZE = 100 # do not accept new queued moves if the player has this many pending

### GUI
MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 32
DEFAULT_FONT_SIZE = 10

MIN_LABEL_SIZE = 25
MAX_LABEL_SIZE = 250
DEFAULT_LABEL_SIZE = 60

ROW_FRAME_WIN_CONDS = 2

### Game Settings window / Seedy
MIN_BOTS = 1
MAX_BOTS = 15
MIN_ROW_OR_COL = 5
MAX_ROW_OR_COL = 30

USE_DEFAULT = 0 # for radio buttons (use seed default or use a custom override)
USE_CUST = 1

PLAYER_ID = 0 # how is this being done so far?

### Scoreboard widgets
SCORE_BOARD_WIDTH_NAME_MIN = 15
SCORE_BOARD_WIDTH_NAME_MAX = 35
SCORE_BOARD_WIDTH_LAND = 4
SCORE_BOARD_WIDTH_ADMIRALS = 6
SCORE_BOARD_WIDTH_SHIPS = 6
SCORE_BOARD_WIDTH_TROOPS = 6

TIDE_HIGH = 1
TIDE_LOW = 2
TIDE_COMING_IN = 3
TIDE_GOING_OUT = 4

# COLOR_TIDE_LOW = '#5c8fe9'
# COLOR_TIDE_RISING_1 ='#3171e3'
COLOR_TIDE_LOW = '#3171e3'
COLOR_TIDE_RISING_2 ='#1a59c9'
COLOR_TIDE_RISING_3 ='#15469e'
COLOR_TIDE_RISING_4 ='#0f3373'
COLOR_TIDE_HIGH = '#092048'

COLOR_SWAMP = '#29e29f'
COLOR_SWAMP_MID_TIDE = '#29d3e3'

# position based on the query that populated self.replay_data
REPLAY_DATA_COL_TURN = 0 
REPLAY_DATA_COL_ROW = 1
REPLAY_DATA_COL_COL = 2
REPLAY_DATA_COL_TYPE = 3
REPLAY_DATA_COL_UID = 4
REPLAY_DATA_COL_TROOPS = 5 


BOT_BEHAVIOR_PETRI = 1
BOT_BEHAVIOR_AMBUSH_PREDATOR = 2