### Constants

DIR_UP = 1 
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4
DIR_NOWHERE = -1

### Cell Type - describes the appearance and behavior of a MadCell object

##Not implemented (yet, anyway)
# CELL_TYPE_PUP_UNKNOWN = 7 # an unopened powerup!
# CELL_TYPE_PUP_FOG_OF_WAR_LIFTED = 8 # briefly lift fog of war (seed will determine duration - with a chance of it lasting all game)
# CELL_TYPE_PUP_FAR_SIGHT = 9 # increases the distance the player can see (duration via seed)
# CELL_TYPE_PUP_GROWTH_MULTIPLIER = 10 # increases or decreases the player's spawn rates across all cell types! duration and multiplier via seed.. perhaps allow multipliers between 0 and 1 to reduce generation.. and even negative to cause troops to shrink! 
# CELL_TYPE_PUP_POISON = 11 # if ALL player cells lose, eg. 1 troop per 2 turns for 25 turns, it makes sense to use the 'shore up' functionality to reduce number of cells temporarily


TERRAIN_TYPE_WATER = 101
TERRAIN_TYPE_LAND = 102 # TODO
TERRAIN_TYPE_BEACH = 103 # TODO
TERRAIN_TYPE_SWAMP = 104 
TERRAIN_TYPE_MOUNTAIN = 105
TERRAIN_TYPE_MOUNTAIN_CRACKED = 106
TERRAIN_TYPE_MOUNTAIN_BROKEN = 107

ENTITY_TYPE_ADMIRAL = 200
ENTITY_TYPE_SHIP = 201
ENTITY_TYPE_SHIP_2 = 202 # combine 2 ships to make this. Increased growth rate
ENTITY_TYPE_SHIP_3 = 203 # combine 1 ship_2 with a ship to make this. Increased growth rate
ENTITY_TYPE_SHIP_4 = 204 # combine 2 ship_2s or 1 ship_3 and 1 ship to make this. Increased growth rate
ENTITY_TYPE_INFANTRY = 205


GAME_STATUS_INIT = 0 # loading
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


BOT_PERSONALITY_PETRI = 101 # all petri all the time
BOT_PERSONALITY_TRACKER = 102 # always on the hunt
BOT_PERSONALITY_GROW_ONLY = 103 # james and the giant reach
BOT_PERSONALITY_AMBUSH_ONLY = 104 # crouching bot, hidden bot
BOT_PERSONALITY_PETRI_AND_GATHER = 105 # like herding cats
BOT_PERSONALITY_GROW_PETRI_AND_GATHER = 106
BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK = 107
BOT_PERSONALITY_GROW_GATHER_SAIL_COMBINE = 108
BOT_PERSONALITY_GROW_GATHER_SAIL_ATTACK = 109
BOT_PERSONALITY_MIX_IT_UP = 110
BOT_SMARTY_PANTS = 111

# Currently the bot's entire personality, but different behavior checks for the same bot should be built later on
BOT_BEHAVIOR_PETRI = 1 # Analyzes current board state and comes up with a weighted list of suggested moves; a weighted sort picks one. Chaotic and shortsighted, but not totally stupid.
BOT_BEHAVIOR_TRACKER = 2 # Picks a ship or admiral on the board and queues up an A*-generated list of move towards the target. Initial version may also default to petri-ing
BOT_BEHAVIOR_GROW = 14 # Programmed to grow into empty spaces when possible, resorting to combat and other operations when needed. Waits if it can't find a valid move
BOT_BEHAVIOR_AMBUSH = 15 # Waits until it is touched by an enemy.. as soon as one of its entities has enough troops to overwhelm the troops along the A* to the nearest touching entity, queue it up to move like the tracker
BOT_BEHAVIOR_GATHER = 16 # pick an owned, non-entity cell with more than one cell (maybe weighted towards the one with the most troops?) and set in an ACTION_MOVE_NORMAL A* course to the nearest admiral
BOT_BEHAVIOR_COMBINE_SHIPS = 17 # Attempt to combine two friendly ships. If no friendly ships exist, see if there are any neutral ships nearby w/ enough 
BOT_BEHAVIOR_ATTACK_SHIP = 18 # If a friendly ship has a distance-weighted troop advantage over an enemy ship or admiral, sail towards it
BOT_BEHAVIOR_SAIL_AROUND = 19 # Prioritize expanding via ship. If no ships are available, try to capture one



# TODO rename these to be more logically consistent - eg BOT_BEHAVIOR_MOVE_HALF_THEN_NORMAL is a set of actions to perform while acting out a different 'behavior'
BOT_BEHAVIOR_MOVE_HALF_THEN_NORMAL = 11 # Currently used by the tracker behavior to queue up different actions in one go
BOT_BEHAVIOR_MOVE_HALF_THEN_ALL = 12 # Currently used by the tracker behavior to queue up different actions in one go
BOT_BEHAVIOR_MOVE_ALL = 13 # Currently used by the tracker behavior to queue up the same action each time, used alongside the "move half then ..." actions


### GUI
MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 32
DEFAULT_FONT_SIZE = 10

MIN_LABEL_SIZE = 25
MAX_LABEL_SIZE = 250
DEFAULT_LABEL_SIZE = 55

MAGIC_NUM_TO_FIX_CELL_SIZE = 0 # tk.Button seems to add 5 px to the height and width 

NUM_DEFAULT_COLORS = 8 # how many bot colors are listed as preferred

ROW_FRAME_WIN_CONDS = 2 #????

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
COLOR_TIDE_LOW = '#1A57C4' # old:'#3171e3'
COLOR_TIDE_RISING_2 ='#1a59c9'
COLOR_TIDE_RISING_3 = '#1850B4' # old: '#15469e'
COLOR_TIDE_RISING_4 ='#0f3373'
COLOR_TIDE_HIGH = '#0E306C' # old: '#092048'

COLOR_SWAMP = '#0E735A' # old: '#29e29f'
COLOR_SWAMP_MID_TIDE = '#105F72' # old: '#29d3e3'

COLOR_HIDDEN_BG = '#222222'
COLOR_HIDDEN_TEXT = '#FFFFFF'
COLOR_HIDDEN_ICON ='#BBBBBB'

COLOR_MOUNTAINS = '#BBBBBB'


# position based on the query that populated self.replay_data
REPLAY_DATA_COL_TURN = 0 
REPLAY_DATA_COL_ROW = 1
REPLAY_DATA_COL_COL = 2
REPLAY_DATA_COL_CELLTYPE = 3
REPLAY_DATA_COL_TERRAIN_TYPE = 4
REPLAY_DATA_COL_ENTITY_TYPE = 5
REPLAY_DATA_COL_UID = 6
REPLAY_DATA_COL_TROOPS = 7


# Describes how many often to increment the troops in a cell. eg rate=2 will grow every other turn
ADMIRAL_GROW_RATE = 2
SHIP_GROW_RATE = 6
BLANK_GROW_RATE = 25
SWAMP_DRAIN_RATE = 1
BROKEN_MTN_GROW_RATE = 50


def get_personality_name(num):
    if num == BOT_PERSONALITY_PETRI: return 'Petri Dish'
    elif num == BOT_PERSONALITY_TRACKER: return 'Tracker'
    elif num == BOT_PERSONALITY_GROW_ONLY: return 'Gardener'
    elif num == BOT_PERSONALITY_AMBUSH_ONLY: return 'Ambush Pred'
    elif num == BOT_PERSONALITY_PETRI_AND_GATHER: return 'Petri Gatherer'
    elif num == BOT_PERSONALITY_GROW_PETRI_AND_GATHER: return 'Petri Gardener'
    elif num == BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK: return 'Petri Tracker'
    elif num == BOT_PERSONALITY_GROW_GATHER_SAIL_COMBINE: return 'Sailor'
    elif num == BOT_PERSONALITY_GROW_GATHER_SAIL_ATTACK: return 'Seaman'
    elif num == BOT_PERSONALITY_MIX_IT_UP: return 'Sir Mix Up'
    elif num == BOT_SMARTY_PANTS: return 'Smarty Pants'

    else: raise ValueError('Invalid personality matrix detected')

def get_behavior_name(num):
    if num == BOT_BEHAVIOR_PETRI: return 'Petri'
    elif num == BOT_BEHAVIOR_TRACKER: return 'Tracking'
    elif num == BOT_BEHAVIOR_GROW: return 'Growing'
    elif num == BOT_BEHAVIOR_AMBUSH: return 'Ambush'
    elif num == BOT_BEHAVIOR_GATHER: return 'Gathering'
    elif num == BOT_BEHAVIOR_COMBINE_SHIPS: return 'Combining'
    elif num == BOT_BEHAVIOR_ATTACK_SHIP: return 'Attack ship'
    elif num == BOT_BEHAVIOR_SAIL_AROUND: return 'Sailing'
    elif num is None: return 'None'
    
    else: raise ValueError('Invalid behavior pattern detected')