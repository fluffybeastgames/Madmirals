
# game of life as opponent entity(ies) - can adjust win/lose conditions around ability to influence the preexisting algo
# spinoff idea: petri wars: spend points to decide numner of starting cells and their respective locations and traits.. then it plays out like conway's game of lie, except maybe w/ ability to place powerups to influence gameplay!
import time
import math
import random
import opensimplex
import numpy as np
import tkinter as tk  # TODO is that one remaining Stringvar() necessary?

### Project modules
from constants import *
# from db import MadDBConnection
from seedy import Seedling # 
from path_finder import *

class MadmiralsGameInstance:
    def __init__(self, parent, seed=None, num_rows=None, num_cols=None, game_mode=None, num_players=None, game_id=None, player_color=None, player_name=None, starting_troops=100, fog=True):
        self.parent = parent
        
        self.seed = seed # the world seed used for generating the level
        if self.seed is None:
            self.seed = random.randint(0, 10**10)
        
        #self.seedling = Seedling(self.seed) # eventually 
        self.game_id = game_id # the id of the game in table game_logs
        self.game_mode = game_mode
        self.game_status = GAME_STATUS_INIT
        self.turn = 0
        self.frames_rendered = 0
        self.game_creation_time = time.time()

        self.tide = self.Tide(self)

        self.parent.fog_of_war = fog

        self.player_color = player_color # if not none, override the default seed's color for the player TODO implement downstream from here
        self.player_name = player_name if player_name else 'SLAYER 1'
        
        self.num_rows = num_rows # either a predefined integer value (preferably higher than 5) or None. 
        self.num_cols = num_cols #      If it's None, a pseudo-random value will be assigned in 
        self.num_players = num_players
        
        self.active_cell = None # current address of the grid location currently selected, corresponding to which cell will be moved
        self.active_cell_prev = None # cell address of the active cell before it was in this location, used to update crosshair animation
        

        self.players = {} # contains the player objects w/ numeric id
        self.turn_order = [] # the initial order of turns.. can be eg shuffled between turns, or assign priority keys and flip flop between whether or high or low has priority
        
        self.game_board = {} # dictionary where keys are a tuple of (row, col) and the value is a MadCell instance

        self.replay_data = None # IFF game_mode = replay, store the game's record of changes in this object.. TODO refactor replays into a different class
        self.replay_pos = 0 # IFF game_mode = replay, use this row to iterate through records
        
        self.generate_game_world(starting_admiral_troops=starting_troops)
        ####self.generate_game_world_test(starting_admiral_troops=starting_troops) #TODO
        

        if self.game_mode == GAME_MODE_REPLAY:
            sql = f'SELECT turn_num, row, col, terrain_type, entity_type, player_id, troops FROM log_game_moves WHERE game_id={self.game_id} ORDER BY turn_num, row, col'
            
            self.replay_data = self.parent.db.run_sql_select(sql)


        else:
            self.add_game_to_log()
            self.record_starting_conditions()


    def get_game_status_text(self):
        if self.game_status == GAME_STATUS_INIT: return 'Init' # loading
        elif self.game_status == GAME_STATUS_READY: return 'Ready' # able to start
        elif self.game_status == GAME_STATUS_IN_PROGRESS: return 'In Progress' #
        elif self.game_status == GAME_STATUS_PAUSE: return 'Paused' #
        elif self.game_status == GAME_STATUS_GAME_OVER_WIN: return 'Won' # game instance is complete and can no longer be played
        elif self.game_status == GAME_STATUS_GAME_OVER_LOSE: return 'Lost' # game instance is complete and can no longer be played
            
    def closest_instance_of_entity(self, entity_type, ref_address, entity_owner='n\a'):
        closest_entity_address = None
        closest_entity_distance = 999

        for r in range(self.num_rows):
            for c in range(self.num_cols):
                if (r, c) != ref_address and self.game_board[(r, c)].entity_type == entity_type:
                    if entity_owner == 'n\a' or self.game_board[(r, c)].owner == entity_owner: 
                        distance = abs(ref_address[0] - r) + abs(ref_address[1] - c)
                        if distance < closest_entity_distance:
                            closest_entity_distance = distance
                            closest_entity_address = (r, c)

        return closest_entity_address, closest_entity_distance # will return None if no entities found on map

    def generate_game_world_test(self, starting_admiral_troops):
        print(f'Generating test world with seed {self.seed}')
        self.num_players = 2
        



    def generate_game_world(self, starting_admiral_troops):
        print(f'Generating world with seed {self.seed}')
        if self.num_players is None:
            #self.num_players = self.seedling.get_num_players()
            self.num_players = Seedling.get_num_players(self.seed)

            print(f'Num players: {self.num_players}')

        list_bot_names  = Seedling.get_bot_names(self, self.seed, self.num_players)
        list_player_colors = Seedling.get_player_colors(self, self.seed, self.num_players)
        
        bot_personalities = [
            BOT_PERSONALITY_MIX_IT_UP,
            BOT_PERSONALITY_GROW_GATHER_SAIL_COMBINE,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK,
            BOT_PERSONALITY_GROW_GATHER_SAIL_ATTACK,
            BOT_PERSONALITY_PETRI,
            BOT_PERSONALITY_TRACKER,
            BOT_PERSONALITY_GROW_ONLY,
            BOT_PERSONALITY_AMBUSH_ONLY,
            BOT_PERSONALITY_PETRI_AND_GATHER,
            BOT_PERSONALITY_GROW_PETRI_AND_GATHER,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK,
            BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK
        ] 

        for i in range(self.num_players):
            player_id = i
            
            # user_desc = list_avail_names.pop(self.seed*123 % len(list_avail_names))
            user_desc = list_bot_names[i]

            print(f'num players {self.num_players} player_id {i} len list_colors {len(list_player_colors)}')
            bg = list_player_colors[i]
            fg = '#FFFFFF' if self.parent.gui.is_color_dark(bg) else '#000000'

            if player_id == PLAYER_ID:
                if self.player_color is not None:
                    bg = self.player_color[0]
                    fg = self.player_color[1]

                if self.player_name is not None:
                    user_desc = self.player_name
                
                bot_personality = None
            else:
                bot_personality = bot_personalities.pop(0)
                  
            # bot_personality = None
            # if i > 0:   
            #     if i == 2:
            #         bot_personality = BOT_PERSONALITY_TRACKER
            #     elif i == 3:
            #         bot_personality = BOT_PERSONALITY_AMBUSH_ONLY
            #     elif i == 4:
            #         bot_personality = BOT_PERSONALITY_GROW_ONLY
            #     elif i == 5:
            #         bot_personality = BOT_PERSONALITY_PETRI_AND_GATHER
            #     elif i == 6:
            #         bot_personality = BOT_PERSONALITY_GROW_PETRI_AND_GATHER
            #     elif i == 1:
            #         bot_personality = BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK                                        
            #     else:
            #         bot_personality = BOT_PERSONALITY_PETRI

            self.players[i] = self.GamePlayer(self, player_id, user_desc, bg, fg, bot_personality)
            
            # every player moves at the same time, but turn order determines the order of operations.
            # This would be quite unfair if this were a multiplayer game. Instead, it would give player 0 (aka user) an advantage
            # Currently we're reversing the list after each turn, but maybe it would be best to give player the advantage
            # ..otherwise best approach could be popping first player id at end of turn and reappending it turn_order!
            self.turn_order.append(player_id) 
            

        # if self.num_rows is None: self.num_rows = self.seedling.get_num_rows()
        # if self.num_cols is None: self.num_cols = self.seedling.get_num_cols()
        if self.num_rows is None: self.num_rows = Seedling.get_num_rows(self.seed)
        if self.num_cols is None: self.num_cols = Seedling.get_num_cols(self.seed)
            
        print(f'Rows: {self.num_rows}\tCols: {self.num_cols}\tPlayers{self.num_players}\tSeed{self.seed}')
        
        num_params = 2 # item id; include item or not; how many of item (eg starting 'troops' on idle cities and strength of mtns)
        #result = self.seedling.get_3d_noise_result(self.num_rows, self.num_cols, num_params)
        result = Seedling.get_3d_noise_result(self.seed, self.num_rows, self.num_cols, num_params)
        
        for i in range(self.num_rows):
            for j in range(self.num_cols):
                self.game_board[(i, j)] = self.MadCell(self, i, j)

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                target_cell = self.game_board[(i, j)]
                target_cell.item_id = result[i][j][0]
                target_cell.item_amt = result[i][j][1]

                if target_cell.item_id < -.4: #-.25:
                    target_cell.terrain_type = TERRAIN_TYPE_MOUNTAIN
                    target_cell.troops = 25 + int(abs(target_cell.item_amt)*50)
                    
                elif target_cell.item_id < -.3: # -.15:
                    target_cell.entity_type = ENTITY_TYPE_SHIP
                    target_cell.troops = 35 + int(abs(target_cell.item_amt)*25)

                elif target_cell.item_id < -.2:
                    target_cell.terrain_type = TERRAIN_TYPE_SWAMP
        
        list_spawn_regions = [] # Each player will be placed in a separate sector of the map. Thus we must have at least as many spawn regions available as players

        num_regions = -1
        if self.num_players <= 4:
            num_regions = 4
        elif self.num_players <= 9: 
            num_regions = 9
        elif self.num_players <= 16:
            num_regions = 16
        else:
            raise ValueError('Too many players!')
        
        list_spawn_regions = list(range(num_regions))
        region_height = self.num_rows/math.sqrt(len(list_spawn_regions))
        region_width = self.num_cols/math.sqrt(len(list_spawn_regions))

        print(f'Cells per region: ({region_width}x{region_height})')
    
        for p in range(self.num_players):
            # spawn_region determines which quadrant/9th/16th of the board each player spawns in
            # Pick a spawn sector and then assign a spawn cell within that region
            spawn_region = list_spawn_regions.pop(self.seed*321 % len(list_spawn_regions))

            region_map_row = int(spawn_region / math.sqrt(num_regions)) # integer division
            region_map_col = int(spawn_region % math.sqrt(num_regions))

            top_left_row = int(region_map_row * region_height)
            top_left_col = int(region_map_col * region_width)
            max_item_amt = -999
            max_item_cell = None

            least_item_amt = 999
            least_item_cell = None

            for check_r in range(top_left_row, top_left_row+int(region_height)):
                for check_c in range(top_left_col, top_left_col+int(region_width)):
                    #print(f'checking {check_r}x{check_c} - item_id {self.game_board[(check_r,check_c)].item_amt}')

                    if self.game_board[(check_r,check_c)].item_amt > max_item_amt:
                        max_item_amt = self.game_board[(check_r,check_c)].item_amt
                        max_item_cell = self.game_board[(check_r,check_c)]
                    
                    if self.game_board[(check_r,check_c)].item_amt < least_item_amt:
                        least_item_amt = self.game_board[(check_r,check_c)].item_amt
                        least_item_cell = self.game_board[(check_r,check_c)]
                    

            # I'm hoping this check will reduce the likelihood that players spawn near each other on the boundaries of their region
            if (region_map_row % 2 == 0 and region_map_col % 2 == 0) or (region_map_row % 2 == 1 and region_map_col % 2 == 1):
                target_cell = max_item_cell
            else:
                target_cell = least_item_cell
            
            print(f'Nearest admiral, distance: {self.closest_instance_of_entity(ENTITY_TYPE_ADMIRAL, (target_cell.row, target_cell.col))}\tTODO do not allow admirals to spawn close together')
            target_cell.owner = self.players[p].user_id
            target_cell.entity_type = ENTITY_TYPE_ADMIRAL
            target_cell.terrain_type = TERRAIN_TYPE_WATER
            
            target_cell.troops = starting_admiral_troops 

    def add_game_to_log(self):
        # Add an entry to the database for this game
        values = (self.seed, self.num_rows, self.num_cols, self.num_players) # list of tuples
        sql = 'INSERT INTO log_games (seed, num_rows, num_cols, num_players) VALUES(?,?,?,?)'
        self.game_id = self.parent.db.run_sql(sql, values)
        
    def record_starting_conditions(self):
        # Mark the starting layout as 'moves' on turn 0            
        
        list_entities = []
        for i in range(self.num_players):
            list_entities.append((self.game_id, self.players[i].user_id, self.players[i].user_desc, self.players[i].color_bg, self.players[i].color_fg ))
        sql = 'INSERT INTO log_game_entities (game_id, player_id, player_name, bg, fg) VALUES (?,?,?,?,?)'
        
        # print('list enttities')
        # print(list_entities)
        self.parent.db.run_sql(sql, list_entities, execute_many=True)
        
        list_changes = []
        for i in range(self.num_rows):
            for j in range(self.num_cols):
                cell = self.game_board[(i,j)]
                list_changes.append((self.game_id, self.turn, i, j, cell.terrain_type, cell.entity_type, cell.owner, cell.troops))
        
        sql = 'INSERT INTO log_game_moves (game_id, turn_num, row, col, terrain_type, entity_type, player_id, troops) VALUES(?,?,?,?,?,?,?,?)'
        self.parent.db.run_sql(sql, list_changes, execute_many=True)
    
    def get_admiral_count(self, uid):
        count = 0

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                if (self.game_board[(i, j)].owner == uid) and (self.game_board[(i, j)].entity_type== ENTITY_TYPE_ADMIRAL):
                    count += 1

        return count

    def move_active_cell(self, new_address=None, dir=None):
    # Requires either a direction to move (relative to current active cell) or a new_address (via clicking) to activate
    # Only player-owned pieces can be clicked on, but dir can extend beyond (until it hits a mountain)

        if new_address is not None:
            if self.game_board[new_address].owner == PLAYER_ID: # only allow clicking on player's pieces
                self.active_cell_prev = self.active_cell
                self.active_cell = new_address
            else: # otherwise, treat it as an intentional deselection
                self.active_cell_prev = self.active_cell
                self.active_cell = None

                
        elif self.active_cell: # if nothing is already selected, active can can't be moved
            row = self.active_cell[0]
            col = self.active_cell[1]

            if dir == DIR_UP and row > 0: row -= 1
            if dir == DIR_DOWN and row < (self.num_rows-1): row += 1
            if dir == DIR_LEFT and col > 0: col -= 1
            if dir == DIR_RIGHT and col < (self.num_cols-1): col += 1

            if self.game_board[(row, col)].is_hidden():
                self.active_cell_prev = self.active_cell
                self.active_cell = (row, col)
                
            else:
                # check if we can stop the active cell from moving
                if self.game_board[(row, col)].terrain_type not in [TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED]:
                    self.active_cell_prev = self.active_cell
                    self.active_cell = (row, col)
        
        # Make sure we render current and prev active cells and cells surrounding them
        if self.active_cell is not None:
            act_row = self.active_cell[0]
            act_col = self.active_cell[1]
            self.game_board[(act_row, act_col)].changed_this_turn = True
            if act_row < self.num_rows - 1: self.game_board[(act_row+1, act_col)].changed_this_turn = True
            if act_row > 0: self.game_board[(act_row-1, act_col)].changed_this_turn = True
            if act_col < self.num_cols - 1: self.game_board[(act_row, act_col+1)].changed_this_turn = True
            if act_col > 0: self.game_board[(act_row, act_col-1)].changed_this_turn = True

        if self.active_cell_prev is not None:
            act_row = self.active_cell_prev[0]
            act_col = self.active_cell_prev[1]
            self.game_board[(act_row, act_col)].changed_this_turn = True
            if act_row < self.num_rows - 1: self.game_board[(act_row+1, act_col)].changed_this_turn = True
            if act_row > 0: self.game_board[(act_row-1, act_col)].changed_this_turn = True
            if act_col < self.num_cols - 1: self.game_board[(act_row, act_col+1)].changed_this_turn = True
            if act_col > 0: self.game_board[(act_row, act_col-1)].changed_this_turn = True


    def hostile_takeover_of_player(self, victim, victor):
        TAKEOVER_KEEP_RATE = .5

        self.players[victim].active = False
        
        for i in range(self.num_rows):
            for j in range(self.num_cols):
                if self.game_board[(i,j)].owner == victim:
                    self.game_board[(i,j)].owner = victor
                    self.game_board[(i,j)].troops = math.ceil(self.game_board[(i,j)].troops * TAKEOVER_KEEP_RATE)
                    self.game_board[(i,j)].changed_this_turn = True
        
    def action_is_valid(self, pending_action):
        #is the action allowable at this moment

        # is it in bounds?
        if (pending_action.target_address[0] < 0 or 
            pending_action.target_address[1] < 0 or 
            pending_action.target_address[0] >= self.num_rows or 
            pending_action.target_address[1] >= self.num_cols):
                return False

        start_cell = self.game_board[pending_action.source_address]
        target_cell = self.game_board[pending_action.target_address]

        if pending_action.action == ACTION_MOVE_NONE: # rest move, valid if player still occupying cell
            return start_cell.owner == pending_action.user_id
                    
        elif pending_action.action==ACTION_MOVE_ALL: # move all cells, leaving only 1 cell in admiral cells
            return start_cell.owner == pending_action.user_id
        
        elif pending_action.action in [ACTION_MOVE_NORMAL, ACTION_MOVE_HALF]:
            if start_cell.owner == pending_action.user_id:
                return target_cell.terrain_type not in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED)
        else:
            raise ValueError('Unexpected action detected')
    
        if start_cell.owner == pending_action.user_id and (pending_action.action==ACTION_MOVE_ALL or target_cell.terrain_type not in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED)):
            return True
        else:
            return False
            
    def update_game_status(self):
        num_active = 0
        for i in range(self.num_players):
            if not self.players[i].active:
                if self.players[i].user_id == 0: # TODO player's user id
                    self.game_status = GAME_STATUS_GAME_OVER_LOSE
                    return

            else:
                num_active += 1 
        
        if num_active <= 1: # if you lost but everyone else also lost, then you win.. using FTL: Faster Than Light logic
            self.game_status = GAME_STATUS_GAME_OVER_WIN

        else:
            self.game_status = GAME_STATUS_IN_PROGRESS
            
    def pop_until_valid_or_empty(self, uid):  
        # If the player's queue is not empty, pop the first element and attempt to perform it
        # Invalid moves: 
        #   - player attempts to move out of bounds or into a mountain (except when Move All-ing into a mtn), 
        #   - attempts to move from a cell they don't currently own 
        #   - player has fewer than 2 troops in cell
        # Continue cycling through the queue until a valid move is found or the queue is empty
                                 
        next_action = self.players[uid].player_queue.pop_queued_action()
        if next_action:
            if self.action_is_valid(next_action):
                source_cell = self.game_board[next_action.source_address]
                target_cell = self.game_board[next_action.target_address]
                source_cell.changed_this_turn = True
                target_cell.changed_this_turn = True

                starting_troops = source_cell.troops
                if next_action.action == ACTION_MOVE_NORMAL:
                    troops_to_move = starting_troops - 1
                
                elif next_action.action == ACTION_MOVE_HALF:
                    troops_to_move = math.trunc(starting_troops/2) # round down w/ truncate to make sure we never move our last troop

                                            
                elif next_action.action == ACTION_MOVE_ALL:
                    # print(f'cell type {source_cell.entity_type} / in ({ENTITY_TYPE_ADMIRAL} {ENTITY_TYPE_SHIP}) ')
                    if source_cell.entity_type in (ENTITY_TYPE_ADMIRAL, ):
                        troops_to_move = starting_troops - 1
                    elif source_cell.entity_type in(ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4) and not (target_cell.terrain_type in (TERRAIN_TYPE_WATER, TERRAIN_TYPE_SWAMP) and target_cell.entity_type is None): # never abandon a ship
                        troops_to_move = starting_troops - 1
                    else:
                        troops_to_move = starting_troops
                        # if troops_to_move == 0: # this may no longer be useful/possible - check troops == 0 retains ownership
                        #     troops_to_move += 1

                elif next_action.action == ACTION_MOVE_NONE:
                    troops_to_move = 0

                else:
                    raise ValueError('Unexpected action encountered')

                source_cell.troops -= troops_to_move
                
                if source_cell.troops <= 0:
                    source_cell.owner = None
                    
                if target_cell.owner == next_action.user_id: # combine forces of already owned troops
                    target_cell.troops += troops_to_move
                    
                    # If we're moving a ship, check to see if we're going to combine them into a single ship
                    if source_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4): 
                        if target_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4, None) and target_cell.terrain_type in (TERRAIN_TYPE_WATER, TERRAIN_TYPE_SWAMP):
                            if next_action.action not in(ACTION_MOVE_HALF, ACTION_MOVE_NONE): # use move half to unload troops, and move none means don't move
                                self.move_or_combine_ships(source_cell, target_cell)
                        
                else: # combat
                    target_cell.troops -= troops_to_move
                    if target_cell.troops < 0:
                        old_owner = target_cell.owner
                        target_cell.troops *= -1
                        target_cell.owner = next_action.user_id
                    
                        # Mountain breaking check
                        if target_cell.terrain_type in [TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED]:
                            target_cell.terrain_type = TERRAIN_TYPE_MOUNTAIN_BROKEN
                            
                        # check if player captured target's last admiral - if so you inherit their kingdom
                        if old_owner is not None and target_cell.entity_type == ENTITY_TYPE_ADMIRAL:
                            if self.get_admiral_count(old_owner) <= 0:
                                print(f'Player {old_owner} defeated')
                                self.hostile_takeover_of_player(victim=old_owner, victor=uid)

                        if source_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4): 
                            if target_cell.entity_type in (None, ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4) and target_cell.terrain_type in (TERRAIN_TYPE_WATER, TERRAIN_TYPE_SWAMP):
                                if next_action.action not in(ACTION_MOVE_HALF, ACTION_MOVE_NONE): # use move half to unload troops, and move none means don't move
                                    self.move_or_combine_ships(source_cell, target_cell)
                                                                            
                    # Mountain cracking check
                    elif target_cell.terrain_type == TERRAIN_TYPE_MOUNTAIN:
                        target_cell.terrain_type = TERRAIN_TYPE_MOUNTAIN_CRACKED

            else:
                self.pop_until_valid_or_empty(uid)
                
    def move_or_combine_ships(self, source_cell, target_cell):
        invading_ship_count = 0
        
        if source_cell.entity_type == ENTITY_TYPE_SHIP: invading_ship_count = 1
        elif source_cell.entity_type == ENTITY_TYPE_SHIP_2: invading_ship_count = 2
        elif source_cell.entity_type == ENTITY_TYPE_SHIP_3: invading_ship_count = 3
        elif source_cell.entity_type == ENTITY_TYPE_SHIP_4: invading_ship_count = 4

        if target_cell.entity_type == ENTITY_TYPE_SHIP: invading_ship_count += 1
        elif target_cell.entity_type == ENTITY_TYPE_SHIP_2: invading_ship_count += 2
        elif target_cell.entity_type == ENTITY_TYPE_SHIP_3: invading_ship_count += 3
        elif target_cell.entity_type == ENTITY_TYPE_SHIP_4: invading_ship_count += 4

        output_source = None    
        output_target = ENTITY_TYPE_SHIP
        
        if invading_ship_count == 2:
            output_target = ENTITY_TYPE_SHIP_2
        elif invading_ship_count == 3:
            output_target = ENTITY_TYPE_SHIP_3
        elif invading_ship_count == 4:
            output_target = ENTITY_TYPE_SHIP_4
        elif invading_ship_count > 4: # Swap the boats if you cross a smaller one. 
            output_target = ENTITY_TYPE_SHIP_4
            if invading_ship_count - 4 == 1: output_source = ENTITY_TYPE_SHIP
            elif invading_ship_count - 4 == 2: output_source = ENTITY_TYPE_SHIP_2
            elif invading_ship_count - 4 == 3: output_source = ENTITY_TYPE_SHIP_3
            elif invading_ship_count - 4 == 4: output_source = ENTITY_TYPE_SHIP_4 # Idea - If you encounter another 4 Star Ship, turn into an admiral? big plus (extra spawn point) and big downside (smaller troop production, immobile)   


        source_cell.entity_type = output_source
        target_cell.entity_type = output_target

    def advance_replay_to_turn(self):
    # In replay mode, each tick/turn the screen is updated to update any and all cells that were changed up until that turn
    # If we want to implement a FF option, then we can either increase the tick speed or increase the turn+=1 incrementer. This function will work well
    # Similarly, a 'jump to turn number x' functionality would work IFF the turn number >= the already rendered cells
    # NOTE Rewinding would require resetting the replay position to the earlier number, clearing the board, then run this function
    
        if self.replay_data is not None:
            #print('replay data')
            caught_up_yet = False
            while not caught_up_yet:
                if self.replay_pos < len(self.replay_data):
                    move = self.replay_data[self.replay_pos]
                    if move[REPLAY_DATA_COL_TURN] <= self.turn:
                        self.game_board[(move[REPLAY_DATA_COL_ROW], move[REPLAY_DATA_COL_COL])].entity_type = move[REPLAY_DATA_COL_ENTITY_TYPE]
                        self.game_board[(move[REPLAY_DATA_COL_ROW], move[REPLAY_DATA_COL_COL])].terrain_type = move[REPLAY_DATA_COL_TERRAIN_TYPE]
                        self.game_board[(move[REPLAY_DATA_COL_ROW], move[REPLAY_DATA_COL_COL])].owner = move[REPLAY_DATA_COL_UID]
                        self.game_board[(move[REPLAY_DATA_COL_ROW], move[REPLAY_DATA_COL_COL])].troops = move[REPLAY_DATA_COL_TROOPS]
                        
                        self.replay_pos += 1
                    else:
                        caught_up_yet = True
                else:
                    caught_up_yet = True
                    self.game_status == GAME_STATUS_GAME_OVER_WIN                        
        else:
            self.game_status == GAME_STATUS_GAME_OVER_LOSE


    def get_bot_behavior(self, bot_num):
        pers = self.players[bot_num].bot_personality  

        if pers == BOT_PERSONALITY_AMBUSH_ONLY: return BOT_BEHAVIOR_AMBUSH
        elif pers == BOT_PERSONALITY_GROW_ONLY: return BOT_BEHAVIOR_GROW
        elif pers == BOT_PERSONALITY_PETRI: return BOT_BEHAVIOR_PETRI
        elif pers == BOT_PERSONALITY_TRACKER: return BOT_BEHAVIOR_TRACKER
        elif pers == BOT_PERSONALITY_PETRI_AND_GATHER: 
            if self.turn % 100 <50:
            # if self.turn % 30 <15:
                return BOT_BEHAVIOR_PETRI
            else:
                return BOT_BEHAVIOR_GATHER
            
        elif pers == BOT_PERSONALITY_GROW_PETRI_AND_GATHER: 
            if self.turn % 75 < 25:
                return BOT_BEHAVIOR_GROW
            elif self.turn % 75 < 50:
                return BOT_BEHAVIOR_PETRI            
            else:
                return BOT_BEHAVIOR_GATHER            
            
        elif pers == BOT_PERSONALITY_GROW_PETRI_GATHER_TRACK:
            if self.turn % 100 < 25:
                return BOT_BEHAVIOR_GROW
            elif self.turn % 100 < 50:
                return BOT_BEHAVIOR_PETRI      
            elif self.turn % 100 < 75:      
                return BOT_BEHAVIOR_GATHER  
            else:
                return BOT_BEHAVIOR_TRACKER
        
        elif pers == BOT_PERSONALITY_GROW_GATHER_SAIL_COMBINE:
            if self.turn % 75 < 25:
                return BOT_BEHAVIOR_GROW    
            elif self.turn % 75 < 35:      
                return BOT_BEHAVIOR_GATHER 
            elif self.turn % 75 < 75:     
                return BOT_BEHAVIOR_SAIL_AROUND 
            else:
                return BOT_BEHAVIOR_COMBINE_SHIPS
            
            # if self.turn % 125 < 50:
            #     return BOT_BEHAVIOR_GROW    
            # elif self.turn % 125 < 75:      
            #     return BOT_BEHAVIOR_GATHER 
            # elif self.turn % 125 < 100:     
            #     return BOT_BEHAVIOR_SAIL_AROUND 
            # else:
            #     return BOT_BEHAVIOR_COMBINE_SHIPS

        elif pers == BOT_PERSONALITY_GROW_GATHER_SAIL_ATTACK:
            if self.turn % 125 < 50:
                return BOT_BEHAVIOR_GROW    
            elif self.turn % 125 < 75:      
                return BOT_BEHAVIOR_GATHER 
            elif self.turn % 125 < 100:     
                return BOT_BEHAVIOR_SAIL_AROUND 
            else:
                return BOT_BEHAVIOR_ATTACK_SHIP
            
        elif pers == BOT_PERSONALITY_MIX_IT_UP:
            if self.turn % 15 == 1:
                return random.choice((BOT_BEHAVIOR_PETRI, BOT_BEHAVIOR_TRACKER, BOT_BEHAVIOR_GROW, BOT_BEHAVIOR_GATHER, BOT_BEHAVIOR_COMBINE_SHIPS, BOT_BEHAVIOR_SAIL_AROUND))
            else: 
                return self.players[bot_num].bot_last_behavior 
            # return random.choice((BOT_BEHAVIOR_PETRI, BOT_BEHAVIOR_TRACKER, BOT_BEHAVIOR_GROW, BOT_BEHAVIOR_GATHER, BOT_BEHAVIOR_COMBINE_SHIPS, BOT_BEHAVIOR_SAIL_AROUND))

        elif pers == BOT_SMARTY_PANTS:
            print('so smart I do nothing')

    def bot_turn(self, bot_num):
        behavior =  self.get_bot_behavior(bot_num)
        if behavior == BOT_BEHAVIOR_PETRI:
            self.players[bot_num].run_petri_growth_check() 

        elif behavior == BOT_BEHAVIOR_TRACKER:
            self.players[bot_num].run_tracker_behavior_check() 
        
        elif behavior == BOT_BEHAVIOR_GROW:
            self.players[bot_num].run_grower_growth_check() 

        elif behavior == BOT_BEHAVIOR_AMBUSH:
            self.players[bot_num].run_ambush_check() 
        
        elif behavior == BOT_BEHAVIOR_GATHER:
            self.players[bot_num].gather_troops() 

        elif behavior == BOT_BEHAVIOR_SAIL_AROUND:
            self.players[bot_num].sail_around() 

        elif behavior == BOT_BEHAVIOR_COMBINE_SHIPS:
            self.players[bot_num].combine_ships() 

        elif behavior == BOT_BEHAVIOR_ATTACK_SHIP:
            self.players[bot_num].attack_ship() 

        

    def tick(self): # move / attack / takeover 
    # Advance the game by one turn
    # If the current "game" is a replay, process the turn in advance_replay()
    # Otherwise, each game turn encompasses 5 distinct phases:
    #   -0. the .changed_this_turn flag is reset for each cell. This flag empowers us to do a sparse rendering when the frame updates at the end of the tick
    #   -1. Each bot player queues 0, 1, or several moves, depending on their personality seting, current behavior mode, and game state
    #   -2. Each player executes the next valid move in their stack, if any, discarding currently invalid moves as it goes
    #   -3. The underlying simulation updates by 1 tick - cells grow or shrink if certain conditions are encountered 
    #       (eg admirals grow every 2nd tick, while ship growth is less frequent and depends on number of masts/ship type)
    #   -4. Cleanup and exit condition check - the scoreboard is updated, move are logged to the database, and check if the game ended on this turn

        self.turn += 1

        if self.game_mode == GAME_MODE_REPLAY:
            self.advance_replay()
            #print(f'Replaying turn {self.turn}')

        elif self.game_mode in [GAME_MODE_FFA, GAME_MODE_FFA_CUST]: 
            
            # Reset change checker, so that we can look for new changes this turn
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    self.game_board[(i,j)].changed_this_turn = False
        
            ### Bot behavior phase - have them all evaluate the current board and add 0 or more moves to their respective queues
            for i in range(len(self.turn_order)):
                self.bot_turn(self.turn_order[i])
                
                             
            ### Action phase - Cycle through the players in turn_order[], and attempt to play an item from their move queues
            for i in range(len(self.turn_order)):
                #print(f'Player order: {i}\tid: {self.turn_order[i]}\tName: {self.players[self.turn_order[i]].user_desc}')         
                self.pop_until_valid_or_empty(self.turn_order[i])

            ### growth phase
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    terrain_type = self.game_board[(i,j)].terrain_type
                    entity_type = self.game_board[(i,j)].entity_type
                    
                    owner = self.game_board[(i,j)].owner
                
                    if owner is not None:

                        if ((entity_type == ENTITY_TYPE_ADMIRAL and self.turn % ADMIRAL_GROW_RATE == 0) or
                            (entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4) and self.turn % SHIP_GROW_RATE == 0) or
                            (entity_type in (ENTITY_TYPE_INFANTRY, None) and self.tide.get_tide_info()[0] == TIDE_LOW and self.turn % BLANK_GROW_RATE == 0) or
                            (terrain_type == TERRAIN_TYPE_MOUNTAIN_BROKEN and self.turn % BROKEN_MTN_GROW_RATE == 0)):                   
                                troops_to_add = 1

                                if entity_type == ENTITY_TYPE_SHIP_2: troops_to_add = 2
                                if entity_type == ENTITY_TYPE_SHIP_3: troops_to_add = 4 # bonus troops
                                if entity_type == ENTITY_TYPE_SHIP_4: troops_to_add = 6 # bonus troops                                

                                self.game_board[(i,j)].troops += troops_to_add
                                
                                self.game_board[(i,j)].changed_this_turn = True
                        
                        elif terrain_type == TERRAIN_TYPE_SWAMP and self.tide.get_tide_info()[0] == TIDE_LOW and self.turn % SWAMP_DRAIN_RATE == 0:
                            self.game_board[(i,j)].troops -= 1
                            self.game_board[(i,j)].changed_this_turn = True                            

                        # check for loss of property (eg to swampland)
                        if self.game_board[(i,j)].troops < 0:
                            self.game_board[(i,j)].owner = None
                            self.game_board[(i,j)].troops = 0
                            self.game_board[(i,j)].changed_this_turn = True  


            ### Powerup check                          
            if self.turn % 50 == 0: # add pups
                num_pups_added = 0
                num_pups_to_add = 3
                
                random.seed(self.seed + self.turn) # makes the entire function pseudorandom - give the same board state and turn number, this will produce the same pups/amounts in the same cells
                row_order = list(range(self.num_rows))
                col_order = list(range(self.num_cols))
                random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
                random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves
                
                for i in row_order:
                    for j in col_order:
                        if num_pups_added < num_pups_to_add:
                            if self.game_board[(i,j)].troops == 0: 
                                self.game_board[(i,j)].troops = random.randrange(-25, -5)
                                num_pups_added += 1

            elif self.turn % 25 == 0: # remove pups
                for i in range(self.num_rows):
                    for j in range(self.num_cols):
                        if self.game_board[(i,j)].troops < 0: self.game_board[(i,j)].troops = 0 # for now, only pup is enticements onto empty land
                        # terrain_type = self.game_board[(i,j)].terrain_type
                        # entity_type = self.game_board[(i,j)].entity_type                                
            
        # # refresh which cells should be viewable to the user # TODO make an array of these values, one for each player, that way AI has some limitations re trying to walk thru mtns
        # for i in range(self.num_rows):
        #     for j in range(self.num_cols):
        #         cell = self.game_board[(i,j)]
        #         cell.update_visibility_status(player_id=0)
                

        # Update land and troop counts for each player
        for i in range(self.num_players):
            self.parent.game.players[i].update_player_stats()

        if self.game_mode in [GAME_MODE_FFA, GAME_MODE_FFA_CUST]: 
            # # Reverse the turn order - this was every other turn, a given player has priority over any other particular player
            # self.turn_order.reverse()
            

            # Update the db w/ any changes this round
            list_changes = []
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    cell = self.game_board[(i,j)]
                    if cell.changed_this_turn:
                        list_changes.append((self.game_id, self.turn, i, j, cell.terrain_type, cell.entity_type, cell.owner, cell.troops))
            
            sql = 'INSERT INTO log_game_moves (game_id, turn_num, row, col, terrain_type, entity_type, player_id, troops) VALUES(?,?,?,?,?,?,?,?)'
            self.parent.db.run_sql(sql, list_changes, execute_many=True)

            self.update_game_status()


            if self.game_status == GAME_STATUS_GAME_OVER_WIN: # TODO where is the game over lost check!?
                #tk.messagebox.askokcancel(title='GG', message='gg')
                self.fog_of_war = False
                
                # Determine winner
                active_id = None
                num_active = 0
                for i in range(self.num_players):
                    if self.players[i].active:
                        num_active += 1 
                        active_id = self.players[i].user_id

                sql = f'UPDATE log_games SET game_status={GAME_STATUS_GAME_OVER_WIN}, winner={active_id} WHERE game_id={self.game_id}'

                self.parent.db.run_sql(sql)


    class Tide:
    # The tides for a given game instance. The user can update the length of them in the settings window (TODO)
    # get_tide_info() returns pertinent information about the current tide
    # get_tide_frame_info() is used by the gui to grab additional tide info for the Tide Chart frame
        
        def __init__(self, parent, high_tide_duraton=90, low_tide_duration=90):
            self.parent = parent

            self.high_tide_duration = high_tide_duraton
            self.retreating_tide_duration = 10
            self.low_tide_duration = low_tide_duration
            self.incoming_duration = 10
        
        def get_tide_color(self, tide_val):
            if tide_val == TIDE_HIGH: return COLOR_TIDE_HIGH
            elif tide_val == TIDE_LOW: return COLOR_TIDE_LOW
            elif tide_val in (TIDE_COMING_IN, TIDE_GOING_OUT): return COLOR_TIDE_RISING_3
            else:
                raise ValueError('Invalid tide passed to get_tide_color()')
            
        def get_tide_info(self, turn=None):
            if turn is None: turn = self.parent.turn

            full_tide_cycle_length = self.high_tide_duration + self.retreating_tide_duration + self.low_tide_duration + self.incoming_duration
            tide_no = self.parent.turn % full_tide_cycle_length

            if tide_no < self.high_tide_duration:
                tide = TIDE_HIGH
                desc = 'High'
                tide_color = COLOR_TIDE_HIGH
                swamp_color = COLOR_TIDE_HIGH
                tide_change = True if tide_no == 0 else False

            elif  tide_no < self.high_tide_duration + self.retreating_tide_duration:
                tide = TIDE_GOING_OUT
                desc = 'Going Out'
                tide_color = COLOR_TIDE_RISING_3   
                swamp_color = COLOR_SWAMP_MID_TIDE
                tide_change = True if tide_no == self.high_tide_duration else False              
            
            elif  tide_no < self.high_tide_duration + self.retreating_tide_duration + self.low_tide_duration:
                tide = TIDE_LOW
                desc = 'Low'
                tide_color = COLOR_TIDE_LOW     
                swamp_color = COLOR_SWAMP
                tide_change = True if tide_no == self.high_tide_duration + self.retreating_tide_duration else False              
            
            elif  tide_no < self.high_tide_duration + self.retreating_tide_duration + self.low_tide_duration + self.incoming_duration:
                tide = TIDE_COMING_IN
                desc = 'Coming In'
                tide_color = COLOR_TIDE_RISING_3
                swamp_color = COLOR_SWAMP_MID_TIDE
                tide_change = True if tide_no == self.high_tide_duration + self.retreating_tide_duration + self.low_tide_duration else False                   
            else:
                raise ValueError('I do not think this is going to trigger')

            return tide, desc, tide_color, swamp_color, tide_change
        

        def get_tide_frame_info(self):
        # The tide chart below the scoreboard is updated every frame and update_tide_chart calls this function to collect the values it needs to display
            full_tide_cycle_length = self.high_tide_duration + self.retreating_tide_duration + self.low_tide_duration + self.incoming_duration
            tide_no = self.parent.turn % full_tide_cycle_length

            tide, desc, color, swamp_color, tide_change = self.get_tide_info(self.parent.turn)
            # next_tide = 'tbd2'
            # next_tide_time = '2222'
            # later_tide = 'tbd3'
            # later_tide_time = '333'

            if tide == TIDE_HIGH:
                next_tide = 'Going out'
                next_tide_time = abs(tide_no - self.high_tide_duration)
                later_tide = 'Low'
                later_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration)
                next_tide_color = self.get_tide_color(TIDE_GOING_OUT)
                later_tide_color = self.get_tide_color(TIDE_LOW)
                
            elif tide == TIDE_GOING_OUT:
                next_tide = 'Low'
                next_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration)
                later_tide = 'Coming In'
                later_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)
                next_tide_color = self.get_tide_color(TIDE_LOW)
                later_tide_color = self.get_tide_color(TIDE_COMING_IN)
                
            elif tide == TIDE_LOW:
                next_tide = 'Coming In'
                next_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)
                later_tide = 'High'
                later_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration - self.incoming_duration)
                next_tide_color = self.get_tide_color(TIDE_COMING_IN)
                later_tide_color = self.get_tide_color(TIDE_HIGH)
                
            elif tide == TIDE_COMING_IN:
                next_tide = 'High'
                next_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)
                later_tide = 'Going Out'
                later_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)
                next_tide_color = self.get_tide_color(TIDE_HIGH)
                later_tide_color = self.get_tide_color(TIDE_GOING_OUT)
                            
            else:
                raise ValueError('Invalid tide')
            
            return desc, next_tide, next_tide_time, later_tide, later_tide_time, color, next_tide_color, later_tide_color
           
    class GamePlayer:
        def __init__(self, parent, user_id, user_desc, color_bg, color_fg, bot_personality=None):
            self.parent = parent
            self.user_id = user_id
            self.user_desc = user_desc
            self.color_bg = color_bg
            self.color_fg = color_fg
            self.active = True # set to False upon defeat
            #self.is_a_player = False # does this entity belong to the player? if so player will be defeated when all such entities are deactivated
            
            # Update with update_player_game_stats() -- WARNING may be buggy if you're not careful
            self.troops = -1
            self.land = -1
            self.admirals = -1
            self.ships = -1 

            self.player_queue = self.ActionQueue(self)

            self.bot_personality = bot_personality # what role(s) should this entity perform? None if regular player -- could do this as a dict of one or more behaviors!
            self.bot_last_behavior = None # most recent behavior the bot has performed 

            self.right_click_pending_address = None # if the player right clicked on a cell, be ready to move half of troops instead of all
            self.move_all_mode = False # if true, attempt to move ALL troops instead of all but one
        
        def update_player_stats(self):
            num_land = 0
            num_admirals = 0
            num_ships = 0
            num_troops = 0
            
            for i in range(self.parent.num_rows):
                for j in range(self.parent.num_cols):
                    if self.parent.game_board[(i,j)].owner == self.user_id:
                        num_land += 1
                        
                        if self.parent.game_board[(i,j)].entity_type == ENTITY_TYPE_ADMIRAL:
                            num_admirals += 1

                        if self.parent.game_board[(i,j)].entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4):
                            num_ships += 1
            
                        num_troops += self.parent.game_board[(i,j)].troops

            self.land = num_land
            self.admirals = num_admirals
            self.ships = num_ships
            self.troops = num_troops
            
        class ActionQueue:
            def __init__(self, parent):
                self.parent = parent # a GamePlayer instance
                self.queue = [] # a list of queued actions; each turn, the first valid action will be performed
                
            class PendingAction:                    
                def __init__(self, uid, source_address, action, direction):
                    self.user_id = uid
                    self.source_address = source_address
                    self.target_address = (-1, -1) # we will assign based on direction - with no consideration of whether or not it would be a legal or valid move
                    self.action = action # ACTION_MOVE_NORMAL | ACTION_MOVE_HALF | ACTION_MOVE_ALL
                    self.direction = direction
        
                    if direction == DIR_DOWN:
                        self.target_address = (source_address[0]+1, source_address[1])
                    elif direction == DIR_UP:
                        self.target_address = (source_address[0]-1, source_address[1])
                    elif direction == DIR_LEFT:
                        self.target_address = (source_address[0], source_address[1]-1)
                    elif direction == DIR_RIGHT:
                        self.target_address = (source_address[0], source_address[1]+1)
                    elif direction == DIR_NOWHERE:
                        self.target_address = (source_address[0], source_address[1])
                    else:
                        raise ValueError('Invalid direction provided!')                            
            
            def add_action_to_queue(self, source_address, action, direction):
                self.queue.append(self.PendingAction(self.parent.user_id, source_address, action, direction))

            def print_queue(self):
                print(f'Action queue for entity {self.parent.user_desc}')
                for q in self.queue:
                    print(f'{q.source_address} \t{q.action} \t{q.direction}')

            def pop_queued_action(self, pos=0):
                if len(self.queue)>pos:
                    return self.queue.pop(pos)
                else:
                    return None
            

        def get_game_board_in_path_finder_speak(self, target_cell):
            # Reduce the board to an array of True/False, where False means there is an obstacle in the way
            board = AStar.Board(self.parent.num_rows, self.parent.num_cols)
            for r in range(self.parent.num_rows):
                for c in range(self.parent.num_cols):
                    cell = self.parent.game_board[(r, c)]
                    if cell.terrain_type in(TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED):
                        board.board[r][c].traversable = False
                    elif cell.owner != self.user_id and cell.entity_type in (ENTITY_TYPE_ADMIRAL, ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4):
                        board.board[r][c].traversable = False
            
            # Target must be traversable or it will never be found
            board.board[target_cell.row][target_cell.col].traversable = True
            
            #board.print_board()
            return board

        def cells_by_distance(self, ref_address):
        # Returns a list of all address tuples sorted by distance from the reference address, excluding the ref_address itself
            class MiniBoard:
                def __init__(self, num_rows, num_cols, ref_address): 
                    # self.mini_board = [[self.MiniCell((r, c), ref_address) for c in range(num_cols)] for r in range(num_rows)]
                    self.mb = []
                    for r in range(num_rows):
                        for c in range(num_cols):
                            self.mb.append(self.MiniCell((r, c), ref_address))
                    self.mb = sorted(self.mb, key=lambda x: x.distance)

                class MiniCell:
                    def __init__(self, address, ref_address):
                        self.address = address
                        self.distance = abs(ref_address[0]-address[0]) + abs(ref_address[1]-address[1]) # The Manhattan distance to reach this cell

                def get_addresses_by_distance(self):
                    out = []
                    for i in range(len(self.mb)): out.append(self.mb[i].address)
                    out.pop(0) # first cell will always be the reference point
                    return out

            return MiniBoard(self.parent.num_rows, self.parent.num_cols, ref_address).get_addresses_by_distance()


        def run_grower_growth_check(self):
            if not self.active: return

            self.bot_last_behavior = BOT_BEHAVIOR_GROW
            # Grow into any open squares available
            # Idea 1: If none available, attack empty ships. If none of those touching, then attack occupied blank cells, then attack adjacent admirals/ships. If none, attack mountains
            # Idea 2: If no open squares available, just wait. If not blocked in entirely, new troops will eventually spawn at the edges. But this will be pretty lame if bot only does this
            # Idea 3: behaviors need to be more modular - add a simple 'brain' to decide which behavior to try out. Then add personalities that prioritize different strats more often
            # Going to plan on going with 3 for now, so this function will start with just empty terrain filling - with or without enemies

            class PotentialGrowthMove:
                def __init__(self, source_cell, target_cell, dir, troop_diff, tide):
                    self.source_cell = source_cell
                    self.target_cell = target_cell
                    self.dir = dir
                    self.troop_diff = troop_diff

                    self.desirability = 0

                    if self.source_cell.terrain_type == TERRAIN_TYPE_SWAMP: # we don't love swamps
                        if tide in (TIDE_LOW, TIDE_GOING_OUT, TIDE_COMING_IN): # especially if they are actively or about to kill us
                            self.desirability += 10 # avoid swamps
                        elif self.target_cell.terrain_type != TERRAIN_TYPE_SWAMP: 
                            self.desirability += 5 # escape if we can

                    if self.target_cell.entity_type == ENTITY_TYPE_ADMIRAL: self.desirability += 5 # good to capture their admiral or reinforce our own
                    if self.target_cell.entity_type == None: self.desirability += 5 # empty cells should be our bread and butter
                    if self.target_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4, ENTITY_TYPE_INFANTRY): self.desirability += 1 # these are good to have, but not our primary focus
                    
                    if self.target_cell.terrain_type == TERRAIN_TYPE_WATER: self.desirability += 5 # fill the terrain
                    if self.target_cell.terrain_type in (TERRAIN_TYPE_SWAMP, TERRAIN_TYPE_MOUNTAIN_BROKEN): self.desirability += 1 # still a way to expand, but swamps are deadly at low tide and broken mountains limit troop growth
                    if self.target_cell.terrain_type in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED): self.desirability -= 20 # last resort
                    
                    if self.target_cell.owner == self.source_cell.owner: self.desirability -= 10 # prefer growing over retreading
                    if self.target_cell.owner != None: self.desirability -= 5 # prefer new territory over direct conflict
                    
                    # print(self.target_cell.row, self.target_cell.col, self.dir, self.troop_diff, self.desirability)
                    
            potential_moves = []
            
            # row_order = list(range(self.parent.num_rows))
            # col_order = list(range(self.parent.num_cols))
            # random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
            # random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves
            for i in range(self.parent.num_rows):                     
                for j in range(self.parent.num_cols):                
                    check_cell = self.parent.game_board[(i,j)]
                    neighbors = []
                    if check_cell.owner == self.user_id and check_cell.troops > 1:
                        if i > 0: neighbors.append([self.parent.game_board[(i-1,j)], DIR_UP]) # neighbor to the north
                        if j > 0: neighbors.append([self.parent.game_board[(i,j-1)], DIR_LEFT]) # neighbor to the west
                        if i < (self.parent.num_rows -1): neighbors.append([self.parent.game_board[(i+1,j)], DIR_DOWN]) # neighbor to the south
                        if j < (self.parent.num_cols -1): neighbors.append([self.parent.game_board[(i,j+1)], DIR_RIGHT]) # neighbor to the east
                      

                        for neighbor in neighbors:
                            t_cell = neighbor[0]
                            troop_diff = check_cell.troops - t_cell.troops
                            if t_cell.owner != self.user_id and troop_diff > 1 or t_cell.owner == self.user_id: # we'll need to leave 1 behind if attacking. move into own cells as a last resort
                                potential_moves.append(PotentialGrowthMove(check_cell, neighbor[0], neighbor[1], troop_diff, self.parent.tide.get_tide_info()[0]))

            random.shuffle(potential_moves) # as a tiebreaker
            potential_moves.sort(key=lambda x: (x.desirability, x.troop_diff), reverse=True)
            
            # print(potential_moves)
            if len(potential_moves) > 0:
                move = potential_moves[0]
                self.player_queue.add_action_to_queue((move.source_cell.row, move.source_cell.col), action=ACTION_MOVE_NORMAL, direction=move.dir)
            else:
                print('ran out of growth moves!')
        
        def run_ambush_check(self):
            if not self.active: return
            
            pass
            #print('todo run_ambush_check')


        def gather_troops(self):
        # pick an owned, non-entity cell with more than one cell (maybe weighted towards the one with the most troops?) and set in an ACTION_MOVE_NORMAL A* course to the nearest admiral
            if not self.active: return

            self.bot_last_behavior = BOT_BEHAVIOR_GATHER

            MOVE_THRESHOLD = 2
            if len(self.player_queue.queue) < 1:
                row_order = list(range(self.parent.num_rows))
                col_order = list(range(self.parent.num_cols))
                random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
                random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves
                
                s_cell = None  # s for source/start
                t_cell_address = None  # t for target

                for i in row_order:                     
                    for j in col_order:
                        if s_cell is None:
                            check_cell = self.parent.game_board[(i,j)]
                            if check_cell.owner == self.user_id and check_cell.troops >= MOVE_THRESHOLD and check_cell.entity_type == None:          
                                print(f'move this one: {i},{j}')    
                                # pick a destination
                                s_cell = check_cell
                                t_cell_address, t_cell_dist = self.parent.closest_instance_of_entity(ENTITY_TYPE_ADMIRAL, (i, j), entity_owner=self.user_id)     
                                print(t_cell_address)

                if t_cell_address is not None:
                    t_cell = self.parent.game_board[t_cell_address]
                    # now the hard part - linking up the A* algorithm to the game
                    board = self.get_game_board_in_path_finder_speak(t_cell)
                    # board.print_board()
                    a_star = AStar(board)
                    path = a_star.find_path((s_cell.row, s_cell.col), (t_cell.row, t_cell.col))
                    if path is None: 
                        print('NO PATH FOUND')
                        pass 
                        
                    else:
                        #print('PATH FOUND')
                        for i in range(len(path)-1):
                            if path[i+1][0] > path[i][0]:
                                dir = DIR_DOWN
                            elif path[i+1][0] < path[i][0]:
                                dir = DIR_UP
                            elif path[i+1][1] > path[i][1]:
                                dir = DIR_RIGHT
                            elif path[i+1][1] < path[i][1]:
                                dir = DIR_LEFT
                            else:
                                raise ValueError('Unexpected jump in found path')
                        
                            self.player_queue.add_action_to_queue(path[i], ACTION_MOVE_NORMAL, dir)


        def sail_around(self):
            if not self.active: return 
            print('sail_around')

            #First assess the board and see which boats are available to us
            list_owned_boats = []
            list_neutral_boats = []
            # list_hostile_boats = []
            # list_hostile_admirals = []
            
            row_order = list(range(self.parent.num_rows))
            col_order = list(range(self.parent.num_cols))
            random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
            random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves
            for i in row_order:                     
                for j in col_order:
                    check_cell = self.parent.game_board[(i,j)]
                    if check_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4):
                        if check_cell.owner == self.user_id: list_owned_boats.append(check_cell)
                        elif check_cell.owner is None: list_neutral_boats.append(check_cell)
                    #     else: list_hostile_boats.append(check_cell)
                    # elif check_cell.entity_type == ENTITY_TYPE_ADMIRAL and check_cell.owner != self.user_id:    
                    #     list_hostile_admirals.append(check_cell)
            
    
            list_owned_boats.sort(key=lambda x: x.troops, reverse=True) # sort by most troops, which we'll prioritize over other ships
            list_neutral_boats.sort(key=lambda x: x.troops, reverse=True) # sort by most troops, which we'll prioritize over other ships
            
            move_made_yet = False 
            def get_neighbors(s_cell): # inner function
                neighbors = [] 
                r = s_cell.row
                c = s_cell.col
                if r > 0: neighbors.append((self.parent.game_board[(r-1,c)], DIR_UP))
                if r < self.parent.num_rows - 1: neighbors.append((self.parent.game_board[(r+1,c)], DIR_DOWN))
                if c > 0 : neighbors.append((self.parent.game_board[(r,c-1)], DIR_LEFT))
                if c < self.parent.num_cols - 1: neighbors.append((self.parent.game_board[(r,c+1)], DIR_RIGHT))
                random.shuffle(neighbors) # randomize so we don't prioritize going one way or another
                    
                return neighbors

            # Check each owned boat to see it can expand into an empty tile
            for s_cell in list_owned_boats:
                if not move_made_yet:
                    for neighbor in get_neighbors(s_cell):
                        if not move_made_yet:
                            if neighbor[0].owner is None and neighbor[0].terrain_type == TERRAIN_TYPE_WATER and  neighbor[0].entity_type == None:
                                address = (s_cell.row, s_cell.col)
                                self.player_queue.add_action_to_queue(address, ACTION_MOVE_NORMAL, neighbor[1]) 
                                print(f'Adding to queue: {address} ACTION_MOVE_NORMAL {neighbor[1]}')
                                move_made_yet = True
            
            # If not, checked own boats for other valid moves
            if not move_made_yet:
                for s_cell in list_owned_boats:
                    if not move_made_yet:
                        for neighbor in get_neighbors(s_cell):
                            if not move_made_yet:
                                if (neighbor[0].terrain_type == TERRAIN_TYPE_WATER or 
                                    (neighbor[0].terrain_type == TERRAIN_TYPE_SWAMP and self.parent.tide.get_tide_info()[0] != TIDE_LOW) and
                                    neighbor[0].owner != self.user_id and neighbor[0].entity_type is None):
                                        self.player_queue.add_action_to_queue( (s_cell.row, s_cell.col), ACTION_MOVE_NORMAL, neighbor[1]) 
                                        move_made_yet = True    

            if not move_made_yet:
                for s_cell in list_owned_boats:
                    if not move_made_yet:                
                        # navigate to closest empty square
                        t_cell_address, t_cell_dist = self.parent.closest_instance_of_entity(None, (s_cell.row, s_cell.col), entity_owner=None)     
                        if t_cell_address is not None:
                            t_cell = self.parent.game_board[t_cell_address]
                            board = self.get_game_board_in_path_finder_speak(t_cell)
                            a_star = AStar(board)
                            path = a_star.find_path((s_cell.row, s_cell.col), (t_cell.row, t_cell.col))
                            if path is not None: 
                
                                #print('PATH FOUND')
                                for i in range(len(path)-1):
                                    if path[i+1][0] > path[i][0]:
                                        dir = DIR_DOWN
                                    elif path[i+1][0] < path[i][0]:
                                        dir = DIR_UP
                                    elif path[i+1][1] > path[i][1]:
                                        dir = DIR_RIGHT
                                    elif path[i+1][1] < path[i][1]:
                                        dir = DIR_LEFT
                                    else:
                                        raise ValueError('Unexpected jump in found path')
                                
                                    self.player_queue.add_action_to_queue(path[i], ACTION_MOVE_NORMAL, dir)
                                    move_made_yet = True



            if not move_made_yet:
                print('Could not find an empty spot to sail around. Going to revert to run_grower_growth_check')
                if len(list_neutral_boats) > 0:
                    print('Maybe try to capture a boat instead')
                
                self.run_grower_growth_check()
            # else: 
            #     print('Moved to ')


        def combine_ships(self):
            if not self.active: return 
            print('combine_ships - BOT_BEHAVIOR_COMBINE_SHIPS TODO')

            ##elif len(list_owned_boats) == 1  and len(list_neutral_boats) > 0:

        def attack_ship(self):
            if not self.active: return 
            print('attack_ship - BOT_BEHAVIOR_ATTACK_SHIP TODO')
                

        def run_tracker_behavior_check(self, intensity=3):
            if not self.active: return 
            
            ATTACK_THRESHOLD = 10
            if False and random.randint(1, intensity) == intensity: # adjust this range to adjust the frequency of defaulting to a petri check #TODO remove False or remove line
                    self.run_petri_growth_check() # this encourages more growth and less spreading itself thin
                
            elif len(self.player_queue.queue) < 1:
                self.bot_last_behavior = BOT_BEHAVIOR_TRACKER
                # pick an object and lunge for it
                # print('Trying to attack')
                row_order = list(range(self.parent.num_rows))
                col_order = list(range(self.parent.num_cols))
                random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
                random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves
                
                s_cell = None  # s for source/start
                t_cell = None  # t for target
                s_t_troop_diff = 0 
                behavior = None
                sorted_target_addresses = []

                for i in row_order:                     
                    for j in col_order:
                        if s_cell is None:
                            check_cell = self.parent.game_board[(i,j)]
                            if check_cell.owner == self.user_id and check_cell.troops >= ATTACK_THRESHOLD:        
                                s_cell = check_cell
                                sorted_target_addresses = self.cells_by_distance((i, j))
                    

                if s_cell is not None:
                    # pick a target and lay in a course
                    # print(f'Launching an attack from {s_cell.row}, {s_cell.col}')
                    # Pick a target
                    for i in sorted_target_addresses:                     
                        if t_cell is None:
                            check_cell = self.parent.game_board[i]
                            troop_diff = s_cell.troops - check_cell.troops
                            if check_cell.owner != self.user_id and check_cell.entity_type in (ENTITY_TYPE_ADMIRAL, ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4):
                                if random.randint(1, intensity) != 1: # go for the closest item more often the more intense the value
                                    t_cell = check_cell
                                    s_t_troop_diff = troop_diff
                                    
                                    if s_t_troop_diff > s_cell.troops: behavior = BOT_BEHAVIOR_MOVE_HALF_THEN_ALL
                                    elif s_t_troop_diff > 0: behavior = BOT_BEHAVIOR_MOVE_ALL
                                    elif abs(troop_diff) < s_cell.troops: behavior = BOT_BEHAVIOR_MOVE_HALF_THEN_NORMAL
                                    else:
                                        if random.randint(1, intensity) == intensity: behavior = BOT_BEHAVIOR_MOVE_HALF_THEN_NORMAL # maybe try anyway - without this it'll never attack turtles
                                    
                                    # print(f'found a target: {t_cell.row}, {t_cell.col}')


                    if behavior is not None:
                        # now the hard part - linking up the A* algorithm to the game
                        board = self.get_game_board_in_path_finder_speak(t_cell)
                        # board.print_board()
                        a_star = AStar(board)
                        path = a_star.find_path((s_cell.row, s_cell.col), (t_cell.row, t_cell.col))
                        if path is None: 
                            pass 
                            #print('NO PATH FOUND')
                        else:
                            #print('PATH FOUND')
                            for i in range(len(path)-1):
                                if path[i+1][0] > path[i][0]:
                                    dir = DIR_DOWN
                                elif path[i+1][0] < path[i][0]:
                                    dir = DIR_UP
                                elif path[i+1][1] > path[i][1]:
                                    dir = DIR_RIGHT
                                elif path[i+1][1] < path[i][1]:
                                    dir = DIR_LEFT
                                else:
                                    raise ValueError('Unexpected jump in found path')
                            
                                if i == 0 and behavior in (BOT_BEHAVIOR_MOVE_HALF_THEN_NORMAL, BOT_BEHAVIOR_MOVE_HALF_THEN_ALL):
                                    action = ACTION_MOVE_HALF
                                elif behavior in (BOT_BEHAVIOR_MOVE_ALL, BOT_BEHAVIOR_MOVE_HALF_THEN_ALL):
                                    action = ACTION_MOVE_ALL
                                else:
                                    action = ACTION_MOVE_NORMAL

                                self.player_queue.add_action_to_queue(path[i], action, dir)

                            # self.player_queue.add_action_to_queue((first_moves_first.source_cell.row, first_moves_first.source_cell.col), action=first_moves_first.action, direction=first_moves_first.dir)

            if len(self.player_queue.queue) < 1: # if it's still empty after trying to add a tracker move, then consider adding a petri check
                if random.randint(1, 3) == 3: # adjust this range to adjust the frequency of defaulting to a petri check
                    self.run_petri_growth_check()
                
            
        class PotentialMove:
            def __init__(self, source_cell, target_cell, action, weight, dir):
                self.source_cell = source_cell
                self.target_cell = target_cell
                self.action = action
                self.weight = weight
                self.dir = dir
                
        def run_petri_growth_check(self):
            if not self.active: return

            self.bot_last_behavior = BOT_BEHAVIOR_PETRI
            #print(f'run_petri_growth_check for: {self.user_desc}')
            # random.seed(11) # 0.5714025946899135
            row_order = list(range(self.parent.num_rows))
            col_order = list(range(self.parent.num_cols))
            random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
            random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves
            potential_moves = []

            for i in row_order: 
                for j in col_order:
                    s_cell = self.parent.game_board[(i,j)] # s for source
                    if len(self.player_queue.queue) <= ACTION_QUEUE_MAX_SIZE and s_cell.owner == self.user_id:
                        neighbors = []
                        if i > 0: neighbors.append([self.parent.game_board[(i-1,j)], DIR_UP]) # neighbor to the north
                        if j > 0: neighbors.append([self.parent.game_board[(i,j-1)], DIR_LEFT]) # neighbor to the west
                        if i < (self.parent.num_rows -1): neighbors.append([self.parent.game_board[(i+1,j)], DIR_DOWN]) # neighbor to the south
                        if j < (self.parent.num_cols -1): neighbors.append([self.parent.game_board[(i,j+1)], DIR_RIGHT]) # neighbor to the east
                        
                        for neighbor in neighbors:
                            t_cell = neighbor[0] # t for target
                            # print(f'neighbor is ({t_cell.row}, {t_cell.col}) - {t_cell.troops} troops')
                            
                            # Go through cell types of starting cell and consider valid options for getting around
                            if s_cell.entity_type == ENTITY_TYPE_ADMIRAL:                            
                                if s_cell.troops > 4:
                                    
                                    if (t_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4) 
                                        or t_cell.terrain_type in (TERRAIN_TYPE_WATER, TERRAIN_TYPE_MOUNTAIN_BROKEN)):
                                        
                                        if s_cell.troops > t_cell.troops:
                                            potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*5, dir=neighbor[1]))
                                            potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*10, dir=neighbor[1]))
                                        else:
                                            potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*2, dir=neighbor[1]))
                                            potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*2, dir=neighbor[1]))

                                    elif t_cell.terrain_type == TERRAIN_TYPE_SWAMP:
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*.5, dir=neighbor[1]))
                                    elif t_cell.terrain_type in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED):
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*.2, dir=neighbor[1]))
                                    
                            elif s_cell.terrain_type == TERRAIN_TYPE_WATER:    
                                if s_cell.troops > 1:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*2, dir=neighbor[1]))
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*.1, dir=neighbor[1]))
                                    #potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops, dir=neighbor[1]))
                                    
                            elif s_cell.terrain_type in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED, TERRAIN_TYPE_MOUNTAIN_BROKEN):                            
                                potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*2, dir=neighbor[1]))

                            elif s_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4):                            
                                potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*2, dir=DIR_NOWHERE))
                                potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*8, dir=neighbor[1]))

                            elif s_cell.terrain_type == TERRAIN_TYPE_SWAMP and self.parent.tide.get_tide_info()[0] in (TIDE_LOW, TIDE_GOING_OUT):            
                                if s_cell.troops > 1: # leave small troops to die
                                    if t_cell.terrain_type == TERRAIN_TYPE_WATER or t_cell.owner == s_cell.owner:
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*75, dir=neighbor[1]))
                                    elif t_cell.terrain_type in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED):
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*5, dir=neighbor[1]))
                                    elif t_cell.terrain_type in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED):
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*20, dir=neighbor[1]))
                                
                            # Check for adjacent bait
                            if t_cell.entity_type == ENTITY_TYPE_ADMIRAL:   
                                if t_cell.owner is not None and t_cell.owner != s_cell.owner and t_cell.troops < s_cell.troops: # always capture an admiral to the best of your ability, esp. if it's owned by someone else
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*100, dir=neighbor[1]))
                                elif t_cell.owner != s_cell.owner and t_cell.troops < s_cell.troops:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*25, dir=neighbor[1]))
                                else:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*3, dir=neighbor[1]))
                                                                    
                            elif t_cell.terrain_type == TERRAIN_TYPE_WATER:       
                                if t_cell.owner is None: # expand                     
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*10, dir=neighbor[1]))
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*1, dir=neighbor[1]))
                                elif t_cell.owner == s_cell.owner: # shuffle about
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*5, dir=neighbor[1]))
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*1, dir=neighbor[1]))
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*2, dir=neighbor[1]))
                                else: # attack
                                    if s_cell.troops > t_cell.troops:
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*50, dir=neighbor[1]))
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*5, dir=neighbor[1]))
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*25, dir=neighbor[1]))
                                    else:
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*10, dir=neighbor[1]))
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*5, dir=neighbor[1]))
    
                            elif t_cell.terrain_type in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED, TERRAIN_TYPE_MOUNTAIN_BROKEN):                            
                                potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*.05, dir=neighbor[1]))

                            elif t_cell.entity_type in (ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4):                            
                                if s_cell.troops > t_cell.troops:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*25, dir=neighbor[1]))
                                else:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*5, dir=neighbor[1]))

                            elif t_cell.terrain_type == TERRAIN_TYPE_SWAMP:                            
                                potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops, dir=neighbor[1]))
                                # if cell.troops > 2: # leave small troops to die
                                #     if n is not None:
                                pass
            
            # If we have at least one potential move identified, we now pick a move and queue it up.
            # The move is selected using a weighted random selectin, where heigh values of list_weights[] are more likely to be selected.
            #print(f'len potential_moves is {len(potential_moves)}')
            if len(potential_moves) > 0:
                list_weights = []

                for i in range(len(potential_moves)):
                    list_weights.append(potential_moves[i].weight)

                num_moves_to_queue = 1
                list_decided_move_or_moves = random.choices(potential_moves, weights=list_weights, k=num_moves_to_queue) # k indicates how many choices to return.. may be worth increasing above 1 to queue up multiple actions
                first_moves_first = list_decided_move_or_moves[0]

                self.player_queue.add_action_to_queue((first_moves_first.source_cell.row, first_moves_first.source_cell.col), action=first_moves_first.action, direction=first_moves_first.dir)

    class MadCell:
        def __init__(self, parent, row, col, terrain_type=TERRAIN_TYPE_WATER, entity_type=None, owner=None):
            self.parent = parent # a game instance
            self.row = row
            self.col = col
            
            self.terrain_type = terrain_type # water, land, beach, mountain
            self.entity_type = entity_type # admiral, ships, troops
            self.troops = 0 # the strength of this block (defense) and potential offensive strength, depending on cell type and owner
            
            self.image = None
            self.owner = owner
            # self.hidden = True # when true, the player character should not be able to see display text or custom formatting of this cell
            # self.cell_type_last_seen_by_player = None # once the fog of war has been lifted, the player knows what type of cell is here.. or at least was here
            
            self.item_id = None # one of the opensimplex.noise3array values for this cell - used to determine to spawn here - may also be used to determine admiral spawn locations
            self.item_amt = None # another noise3array value - used to determine how much of an item should be here
            
        def is_hidden(self):
            # returns true if the cell should be hidden
            if not self.parent.parent.fog_of_war: # If fog of war is off, then no cells are hidden
                return False
                
            elif self.owner == PLAYER_ID: # player can always see their own cells
                return False
            
            elif (
                (self.row>0 and self.parent.game_board[(self.row-1, self.col)].owner == PLAYER_ID) or  # top
                (self.row>0 and self.col>0 and self.parent.game_board[(self.row-1, self.col-1)].owner == PLAYER_ID) or # top left
                (self.row>0 and self.col<(self.parent.num_cols-1) and self.parent.game_board[(self.row-1, self.col+1)].owner == PLAYER_ID) or # top right
                (self.col>0 and self.parent.game_board[(self.row, self.col-1)].owner == PLAYER_ID) or # left
                (self.col<(self.parent.num_cols-1) and self.parent.game_board[(self.row, self.col+1)].owner == PLAYER_ID) or # right
                (self.row<(self.parent.num_rows-1) and self.col>0 and self.parent.game_board[(self.row+1, self.col-1)].owner == PLAYER_ID) or # bot left
                (self.row<(self.parent.num_rows-1) and self.parent.game_board[(self.row+1, self.col)].owner == PLAYER_ID) or # bot
                (self.row<(self.parent.num_rows-1) and self.col<(self.parent.num_cols-1) and self.parent.game_board[(self.row+1, self.col+1)].owner == PLAYER_ID)# bot right
                ):
                    return False
                    
            else:
                return True       

        def get_button_info(self): 
            
            if self.is_hidden():
                text = ' '
                bg = COLOR_HIDDEN_BG
                fg = COLOR_HIDDEN_TEXT
                icon_color = COLOR_HIDDEN_ICON
            else:
                tide, tide_desc, tide_color, swamp_color, tide_changed = self.parent.tide.get_tide_info(self.parent.turn)
                
                text = '' if self.troops == 0 else self.troops
            
                if self.terrain_type in (TERRAIN_TYPE_WATER, TERRAIN_TYPE_MOUNTAIN_BROKEN):
                    bg = tide_color
                elif self.terrain_type == TERRAIN_TYPE_SWAMP:
                    bg = swamp_color
                elif self.terrain_type in (TERRAIN_TYPE_MOUNTAIN, TERRAIN_TYPE_MOUNTAIN_CRACKED):
                    bg = tide_color #COLOR_MOUNTAINS
                else:
                    bg = 'red'
                    raise ValueError('Unexpected terrain type')
                    
                if self.owner is None:
                    icon_color = '#BBBBBB'
                    fg = '#FFFFFF'
                    
                else:
                    icon_color = self.parent.players[self.owner].color_bg
                    fg = self.parent.players[self.owner].color_fg 

            self.image = self.parent.parent.images.get_image_by_cell(self, icon_color)                 

            # Lighten the cell it's the active (currently selected) cell to bring attention to it
            # Also darken the cell if it's adjacent to the active cell
            if self.parent.active_cell == (self.row, self.col):
                bg = self.parent.parent.gui.adjust_color_brightness(bg, +50)     # maybe instead / in addition change tk.sunken to tk.groove
            elif self.parent.active_cell in [(self.row-1,self.col), (self.row+1,self.col), (self.row,self.col-1), (self.row,self.col+1)]:
                bg = self.parent.parent.gui.adjust_color_brightness(bg, -50)     # maybe instead / in addition change tk.sunken to tk.groove

            return text, bg, fg, self.image