
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
from db import MadDBConnection
from seedy import Seedling # 


class MadmiralsGameInstance:
    
    def __init__(self, parent, seed=None, num_rows=None, num_cols=None, game_mode=None, num_players=None, game_id=None, player_color=None, player_name=None):
        self.parent = parent
        
        self.seed = seed # the world seed used for generating the level
        if self.seed is None:
            self.seed = random.randint(0, 10**10)
        
        #self.seedling = Seedling(self.seed) # eventually 
        self.game_id = game_id # the id of the game in table game_logs
        self.game_mode = game_mode
        self.game_status = GAME_STATUS_INIT
        self.turn = 0

        self.tide = self.Tide(self)

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
        
        self.generate_game_world(starting_admiral_troops=100)

        if self.game_mode == GAME_MODE_REPLAY:
            sql = f'SELECT turn_num, row, col, terrain_type, entity_type, player_id, troops FROM log_game_moves WHERE game_id={self.game_id} ORDER BY turn_num, row, col'
            
            self.replay_data = self.parent.db.run_sql_select(sql)


        else:
            self.add_game_to_log()
            self.record_starting_conditions()
    
    def closest_instance_of_entity(self, entity_type, starting_cell):
        MAX_SEARCH_DEPTH = 3  # temp, should line up w/ user input

        class SearchQueue:
            def __init__(self):
                self.queue = [] # an ordered list of SearchQueueItem cells to check, facilitating a breadth first approach to checking
                self.addresses_already_searched = []
                self.addresses_pending_search = []

            def pop_next_search_item(self):
                if len(self.queue) > 0:
                    return self.queue.pop(0)
                else:
                    return None
                
            class SearchQueueItem:
                def __init__(self, target_cell, distance, continue_left=True, continue_up=True, continue_down=True, continue_right=True):
                    self.target_cell = target_cell
                    self.distance = distance
                    self.continue_left = continue_left
                    self.continue_up = continue_up
                    self.continue_down = continue_down
                    self.continue_right = continue_right

        
        search_queue = SearchQueue()
        search_queue.queue.append(search_queue.SearchQueueItem(starting_cell, distance=0))
        #print(search_queue.queue[0].target_cell)

        entity_found = False
        distance = 0

        print(f'Starting... first cell is ({search_queue.queue[0].target_cell.row}, {search_queue.queue[0].target_cell.col})')
        
        while(len(search_queue.addresses_already_searched) < self.num_rows*self.num_cols and not entity_found and distance <= MAX_SEARCH_DEPTH):
            s_item = search_queue.pop_next_search_item()
            
            if s_item is not None:
                # print(f''target cell{s_item.target_cell}')
                row = s_item.target_cell.row
                col = s_item.target_cell.col
                
                if (row, col) not in search_queue.addresses_already_searched:
                    search_queue.addresses_already_searched.append((row, col))
                    print(f'Checking \t{(row, col)}\t attempt {len(search_queue.addresses_already_searched)}\tDistance {s_item.distance}')    
                    
                    if s_item.target_cell.entity_type == entity_type:
                        entity_found = True
                        distance = s_item.distance
                    
                    else:
                        if s_item.continue_left: # if this check looks left
                            if col > 0: # if left is in bounds
                                new_address = (row, col-1)
                                if new_address not in search_queue.addresses_already_searched and new_address not in search_queue.addresses_pending_search:
                                    search_queue.addresses_pending_search.append(new_address)
                                    new_cell = self.game_board[new_address]
                                    search_queue.queue.append(search_queue.SearchQueueItem(new_cell, s_item.distance + 1))
                        
                        if s_item.continue_up: # if this check looks up
                            if row > 0:  # if move is in bounds
                                new_address = (row-1, col)
                                if new_address not in search_queue.addresses_already_searched and new_address not in search_queue.addresses_pending_search:
                                    search_queue.addresses_pending_search.append(new_address)
                                    new_cell = self.game_board[new_address]
                                    search_queue.queue.append(search_queue.SearchQueueItem(new_cell, s_item.distance + 1))
                            
                        
                        if s_item.continue_right: 
                            if col < (self.num_cols-1): # if move is in bounds
                                new_address = (row, col+1)
                                if new_address not in search_queue.addresses_already_searched and new_address not in search_queue.addresses_pending_search:
                                    search_queue.addresses_pending_search.append(new_address)
                                    new_cell = self.game_board[new_address]
                                    search_queue.queue.append(search_queue.SearchQueueItem(new_cell, s_item.distance + 1))
                        
                        if s_item.continue_down: 
                            if row < (self.num_rows-1): # if move is in bounds
                                new_address = (row+1, col)
                                if new_address not in search_queue.addresses_already_searched and new_address not in search_queue.addresses_pending_search:
                                    search_queue.addresses_pending_search.append(new_address)
                                    new_cell = self.game_board[new_address]
                                    search_queue.queue.append(search_queue.SearchQueueItem(new_cell, s_item.distance + 1))
                        
                        
                    # if x: entity_found = True
                    # else: add queue items to valid targets in valid continue_ directions
                    # TODO here almost on the verge of greatness, or at least adequacy..
                
                else:
                    print(f'Already checked ({s_item.target_cell.row}, {s_item.target_cell.col})')

            else:
                print('I think reaching this means at least one cell is blocked by eg mountains')
                distance = -1

        print(f'Escaped with a result of {distance}\t{s_item.target_cell.row}, {s_item.target_cell.col}')
        return distance
    
    def generate_game_world(self, starting_admiral_troops):
        print(f'Generating world with seed {self.seed}')
        if self.num_players is None:
            #self.num_players = self.seedling.get_num_players()
            self.num_players = Seedling.get_num_players(self.seed)

            print(f'Num players: {self.num_players}')

        sql_names = 'SELECT bot_name FROM bot_names ORDER BY bot_name'
        sql_colors = 'SELECT hex FROM colors ORDER BY hex'
        list_avail_names = self.parent.db.run_sql_select(sql_names, num_vals_selected=1)
        list_avail_colors = self.parent.db.run_sql_select(sql_colors, num_vals_selected=1)

        for i in range(self.num_players):
            player_id = i
            
            user_desc = list_avail_names.pop(self.seed*123 % len(list_avail_names))
            user_colors = list_avail_colors.pop(self.seed*33 % len(list_avail_colors))
            
            bg = user_colors
            # print(bg)
            fg = '#FFFFFF' if self.parent.gui.is_color_dark(bg) else '#000000'

            if player_id == 0: # ie the player
                if self.player_color is not None:
                    bg = self.player_color[0]
                    fg = self.player_color[1]

                if self.player_name is not None:
                    user_desc = self.player_name
                  
            bot_behavior = None
            if i > 0:    
                if i % 4 == 0:
                    bot_behavior = BOT_BEHAVIOR_PETRI #TODO TEMP
                else:
                    bot_behavior = BOT_BEHAVIOR_PETRI

            self.players[i] = self.GamePlayer(self, player_id, user_desc, bg, fg, bot_behavior)
            
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
            
            target_cell.owner = self.players[p].user_id
            target_cell.entity_type = ENTITY_TYPE_ADMIRAL
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
        print('get_admiral_count')
        count = 0

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                if (self.game_board[(i, j)].owner == uid) and (self.game_board[(i, j)].entity_type== ENTITY_TYPE_ADMIRAL):
                    count += 1

        return count

    def move_active_cell(self, new_address=None, dir=None):
    # Requires either a direction to move or a new_address to move to
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
                    self.game_status == GAME_STATUS_GAME_OVER_LOSE
                    break

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
                    if source_cell.entity_type in (ENTITY_TYPE_ADMIRAL, ENTITY_TYPE_SHIP_4):
                        troops_to_move = starting_troops - 1
                    elif source_cell.entity_type in(ENTITY_TYPE_SHIP, ENTITY_TYPE_SHIP_2, ENTITY_TYPE_SHIP_3, ENTITY_TYPE_SHIP_4) and target_cell.terrain_type != TERRAIN_TYPE_WATER: # never abandon a ship
                        troops_to_move = starting_troops - 1
                    else:
                        troops_to_move = starting_troops
                        if troops_to_move == 0: # this may no longer be useful/possible - check troops == 0 retains ownership
                            troops_to_move += 1

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
                            if target_cell.entity_type is None and target_cell.terrain_type == TERRAIN_TYPE_WATER:
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
            
        output_type = ENTITY_TYPE_SHIP

        if invading_ship_count > 4:
            print('do not combine ships!')
        if invading_ship_count == 2:
            output_type = ENTITY_TYPE_SHIP_2
            # print('ship 2 created!')
        elif invading_ship_count == 3:
            output_type = ENTITY_TYPE_SHIP_3
            # print('ship 3 created!')
        elif invading_ship_count == 4:
            output_type = ENTITY_TYPE_SHIP_4
            # print('ship 4 created!')
        elif invading_ship_count > 4:
            output_type = ENTITY_TYPE_SHIP_4

            # print(f'Source {source_cell.entity_type}\tTarget {target_cell.entity_type} \t{invading_ship_count}')
            # print('NEW ADMIRAL created!')
            print('ITS THAT DANG BUG AGAIN')

        source_cell.entity_type = None
        target_cell.entity_type = output_type

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

    def bot_turn(self, bot_num):
        behavior = self.players[bot_num].bot_behavior
        if behavior == BOT_BEHAVIOR_AMBUSH_PREDATOR:
            self.players[bot_num].run_ambush_behavior_check() 
        
        if behavior == BOT_BEHAVIOR_PETRI:
            self.players[bot_num].run_petri_growth_check() 


    def tick(self): # move / attack / takeover 
    # Advance the game by one turn
    # If the current "game" is a replay, process the turn in advance_replay()
    # Otherwise, 
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
                            (entity_type == ENTITY_TYPE_INFANTRY and self.tide.get_tide_info()[0] == TIDE_LOW and self.turn % BLANK_GROW_RATE == 0) or
                            (terrain_type == TERRAIN_TYPE_MOUNTAIN_BROKEN and self.turn % BROKEN_MTN_GROW_RATE == 0)):                   
                                troops_to_add = 1

                                if entity_type == ENTITY_TYPE_SHIP_2: troops_to_add = 2
                                if entity_type == ENTITY_TYPE_SHIP_3: troops_to_add = 3
                                if entity_type == ENTITY_TYPE_SHIP_4: troops_to_add = 4                                

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


            if self.game_status == GAME_STATUS_GAME_OVER_WIN:
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
        def __init__(self, parent):
            self.parent = parent

            self.high_tide_duration = 890
            self.retreating_tide_duration = 10
            self.low_tide_duration = 90
            self.incoming_duration = 10

#         tide code
# tide string
# bool tide just changed
# tide color bg
# tide color fg


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

            elif tide == TIDE_GOING_OUT:
                next_tide = 'Low'
                next_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration)
                later_tide = 'Coming In'
                later_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)

            elif tide == TIDE_LOW:
                next_tide = 'Coming In'
                next_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)
                later_tide = 'High'
                later_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration - self.incoming_duration)

            elif tide == TIDE_COMING_IN:
                next_tide = 'High'
                next_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)
                later_tide = 'Going Out'
                later_tide_time = abs(tide_no - self.high_tide_duration - self.retreating_tide_duration - self.low_tide_duration)
            
            else:
                raise ValueError('Invalid tide')
            
            return desc, next_tide, next_tide_time, later_tide, later_tide_time, color
           
        

    class GamePlayer:
        def __init__(self, parent, user_id, user_desc, color_bg, color_fg, bot_behavior=None):
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

            self.bot_behavior = bot_behavior # what role(s) should this entity perform? None if regular player -- could do this as a dict of one or more behaviors!

            self.right_click_pending_address = None # if the player right clicked on a cell, be ready to move half of troops instead of all
            self.commando_mode = False # if true, attempt to move ALL troops instead of all but one
        
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
            



        # def update_land_count(self):
        #     num_land = 0
        #     for i in range(self.parent.num_rows):
        #         for j in range(self.parent.num_cols):
        #             if self.parent.game_board[(i,j)].owner == self.user_id:
        #                 num_land += 1
            
        #     self.land = num_land
            
        # def update_troop_count(self):
        #     num_troops = 0
        #     for i in range(self.parent.num_rows):
        #         for j in range(self.parent.num_cols):
        #             if self.parent.game_board[(i,j)].owner == self.user_id:
        #                 num_troops += self.parent.game_board[(i,j)].troops
            
        #     self.troops = num_troops


        class ActionQueue:
            
            def __init__(self, parent):
                self.parent = parent
                self.queue = []
                
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
            
        def run_ambush_behavior_check(self):
            pass 
            # print(f'run_ambush_behavior_check for: {self.user_desc}')
        
        class PotentialMove:
            def __init__(self, source_cell, target_cell, action, weight, dir):
                self.source_cell = source_cell
                self.target_cell = target_cell
                self.action = action
                self.weight = weight
                self.dir = dir
                
        def run_petri_growth_check(self):
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
                            
                                                            
            #print(f'len potential_moves is {len(potential_moves)}')
            if len(potential_moves) > 0:
                list_weights = []

                for i in range(len(potential_moves)):
                    list_weights.append(potential_moves[i].weight)

                num_moves_to_queue = 1
                list_decided_move_or_moves = random.choices(potential_moves, weights=list_weights, k=num_moves_to_queue) # k indicates how many choices to return.. may be worth increasing above 1 to queue up multiple actions
                first_moves_first = list_decided_move_or_moves[0]

                #print((this_one.source_cell.row, this_one.source_cell.col), action=this_one.action, direction=this_one.dir)
                self.player_queue.add_action_to_queue((first_moves_first.source_cell.row, first_moves_first.source_cell.col), action=first_moves_first.action, direction=first_moves_first.dir)

                #self.queue.append(self.PendingAction(self.parent.user_id, source_address, action, direction))



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
                text = ''
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
                # relief = tk.GROOVE


            return text, bg, fg, self.image