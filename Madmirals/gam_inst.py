
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
    
    def __init__(self, parent, seed=None, num_rows=None, num_cols=None, game_mode=None, num_players=None, game_id=None):
        self.parent = parent
        
        self.seed = seed # the world seed used for generating the level
        if self.seed is None:
            self.seed = random.randint(0, 10**10)
        
        self.seedling = Seedling(self.seed) # eventually 
        self.game_id = game_id # the id of the game in table game_logs
        self.game_mode = game_mode
        self.game_status = GAME_STATUS_INIT
        self.turn = 0

        self.num_rows = num_rows # either a predefined integer value (preferably higher than 5) or None. 
        self.num_cols = num_cols #      If it's None, a pseudo-random value will be assigned in 
        self.num_players = num_players

        self.active_cell = None # cell address 

        self.players = {} # contains the player objects w/ numeric id
        self.turn_order = [] # the initial order of turns.. can be eg shuffled between turns, or assign priority keys and flip flop between whether or high or low has priority
        
        self.game_board = {} # dictionary where keys are a tuple of (row, col) and the value is a MadCell instance

        self.replay_data = None # IFF game_mode = replay, store the game's record of changes in this object.. TODO refactor replays into a different class
        self.replay_pos = 0 # IFF game_mode = replay, use this row to iterate through records
        
        self.generate_game_world()

        if self.game_mode == GAME_MODE_REPLAY:
            
            sql = f'SELECT turn_num, row, col, cell_type, player_id, troops FROM log_game_moves WHERE game_id={self.game_id} ORDER BY turn_num, row, col'
            
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
                    
                    if s_item.target_cell.cell_type == entity_type:
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
    
    def generate_game_world(self):
        print(f'Generating world with seed {self.seed}')
        if self.num_players is None:
            self.num_players = self.seedling.get_num_players()

            print(f'Num players: {self.num_players}')

        sql_names = 'SELECT bot_name FROM bot_names ORDER BY bot_name'
        sql_colors = 'SELECT bg_color, fg_color FROM entity_colors ORDER BY bg_color, fg_color'
        list_avail_names = self.parent.db.run_sql_select(sql_names, num_vals_selected=1)
        list_avail_colors = self.parent.db.run_sql_select(sql_colors, num_vals_selected=2)

        for i in range(self.num_players):
            user_desc = list_avail_names.pop(self.seed*123 % len(list_avail_names))
            user_colors = list_avail_colors.pop(self.seed*33 % len(list_avail_colors))
            
            bg = user_colors[0]
            fg = user_colors[1]

            player_id = i

            bot_behavior = None
            if i > 0:    
                if i % 4 == 0:
                    #bot_behavior = self.GameEntity.BEHAVIOR_AMBUSH_PREDATOR
                    bot_behavior = self.GameEntity.BEHAVIOR_PETRI #TODO TEMP
                else:
                    bot_behavior = self.GameEntity.BEHAVIOR_PETRI

            self.players[i] = self.GameEntity(self, player_id, user_desc, bg, fg, bot_behavior)
            self.turn_order.append(player_id)

        if self.num_rows is None: self.num_rows = self.seedling.get_num_rows()
        if self.num_cols is None: self.num_cols = self.seedling.get_num_cols()
            
        print(f'Rows: {self.num_rows}\tCols: {self.num_cols}\tPlayers{self.num_players}\tSeed{self.seed}')
        
        num_params = 2 # item id; include item or not; how many of item (eg starting 'troops' on idle cities and strength of mtns)
        result = self.seedling.get_3d_noise_result(self.num_rows, self.num_cols, num_params)
        
        for i in range(self.num_rows):
            for j in range(self.num_cols):
                self.game_board[(i, j)] = self.MadCell(self, i, j)

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                target_cell = self.game_board[(i, j)]
                target_cell.item_id = result[i][j][0]
                target_cell.item_amt = result[i][j][1]

                if target_cell.item_id < -.4: #-.25:
                    target_cell.cell_type = CELL_TYPE_MOUNTAIN
                    target_cell.troops = 25 + int(abs(target_cell.item_amt)*50)
                    
                elif target_cell.item_id < -.3: # -.15:
                    target_cell.cell_type = CELL_TYPE_SHIP
                    target_cell.troops = 35 + int(abs(target_cell.item_amt)*25)

                elif target_cell.item_id < -.2:
                    target_cell.cell_type = CELL_TYPE_SWAMP
        
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
            target_cell.cell_type = CELL_TYPE_ADMIRAL
            target_cell.troops = 10 # consider playing w/ starting troops
            
            # dev bonus
            if p == 0: 
                #target_cell.troops = 255 #500
                self.players[p].user_desc = 'Zeke'

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
                list_changes.append((self.game_id, self.turn, i, j, cell.cell_type, cell.owner, cell.troops))
        
        sql = 'INSERT INTO log_game_moves (game_id, turn_num, row, col, cell_type, player_id, troops) VALUES(?,?,?,?,?,?,?)'
        self.parent.db.run_sql(sql, list_changes, execute_many=True)
    
    def get_admiral_count(self, uid):
        print('get_admiral_count')
        count = 0

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                if (self.game_board[(i, j)].owner == uid) and (self.game_board[(i, j)].cell_type== CELL_TYPE_ADMIRAL):
                    count += 1

        return count

    def move_active_cell(self, dir): 
        if self.active_cell:
            row = self.active_cell[0]
            col = self.active_cell[1]

            if dir == DIR_UP and row > 0: row -= 1
            if dir == DIR_DOWN and row < (self.num_rows-1): row += 1
            if dir == DIR_LEFT and col > 0: col -= 1
            if dir == DIR_RIGHT and col < (self.num_cols-1): col += 1

            if self.game_board[(row, col)].hidden:
                self.active_cell = (row, col)
            else:
                # check if we can stop the active cell from moving
                if self.game_board[(row, col)].cell_type not in [CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED]:
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
        
    class GameEntity:
        BEHAVIOR_PETRI = 1
        BEHAVIOR_AMBUSH_PREDATOR = 2
        # etc
           
        
        def __init__(self, parent, user_id, user_desc, color_bg, color_fg, bot_behavior=None):
            self.parent = parent
            self.user_id = user_id
            self.user_desc = user_desc
            self.color_bg = color_bg
            self.color_fg = color_fg
            self.active = True # set to False upon defeat
            #self.is_a_player = False # does this entity belong to the player? if so player will be defeated when all such entities are deactivated
            
            self.troops = -1 # call update_troop_count() to update -- WARNING may be buggy if you're not careful
            self.land = -1 # gets updated when update_land_count() is called -- WARNING may be buggy if you're not careful
            
            self.player_queue = self.ActionQueue(self)

            self.bot_behavior = bot_behavior # what role(s) should this entity perform? None if regular player -- could do this as a dict of one or more behaviors!

            self.right_click_pending_address = None # if the player right clicked on a cell, be ready to move half of troops instead of all
            self.commando_mode = False # if true, attempt to move ALL troops instead of all but one

        def update_land_count(self):
            num_land = 0
            for i in range(self.parent.num_rows):
                for j in range(self.parent.num_cols):
                    if self.parent.game_board[(i,j)].owner == self.user_id:
                        num_land += 1
            
            self.land = num_land
            
        def update_troop_count(self):
            num_troops = 0
            for i in range(self.parent.num_rows):
                for j in range(self.parent.num_cols):
                    if self.parent.game_board[(i,j)].owner == self.user_id:
                        num_troops += self.parent.game_board[(i,j)].troops
            
            self.troops = num_troops


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
                            if s_cell.cell_type == CELL_TYPE_ADMIRAL:                            
                                if s_cell.troops > 4:

                                    if t_cell.cell_type in (CELL_TYPE_BLANK, CELL_TYPE_SHIP, CELL_TYPE_SHIP_2, CELL_TYPE_SHIP_3, CELL_TYPE_SHIP_4, CELL_TYPE_MOUNTAIN_BROKEN):
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*2, dir=neighbor[1]))
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops*2, dir=neighbor[1]))
                                    elif t_cell.cell_type == CELL_TYPE_SWAMP:
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*.75, dir=neighbor[1]))
                                    elif t_cell.cell_type in (CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED):
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops*.5, dir=neighbor[1]))
                                    
                                    
                            elif s_cell.cell_type == CELL_TYPE_BLANK:    
                                if s_cell.troops > 1:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=s_cell.troops*2, dir=neighbor[1]))
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_HALF, weight=s_cell.troops, dir=neighbor[1]))
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=s_cell.troops, dir=neighbor[1]))
                                    
                            elif s_cell.cell_type in (CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED, CELL_TYPE_MOUNTAIN_BROKEN):                            
                                pass
                            elif s_cell.cell_type in (CELL_TYPE_SHIP, CELL_TYPE_SHIP_2, CELL_TYPE_SHIP_3, CELL_TYPE_SHIP_4):                            
                                potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NONE, weight=s_cell.troops*2, dir=DIR_NOWHERE))

                            elif s_cell.cell_type == CELL_TYPE_SWAMP:            
                                if s_cell.troops > 1: # leave small troops to die
                                    if t_cell.cell_type == CELL_TYPE_BLANK:
                                        potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=75, dir=neighbor[1]))
                                
                                
                            # Check for adjacent bait
                            if t_cell.cell_type == CELL_TYPE_ADMIRAL:   
                                if t_cell.owner is not None and t_cell.owner != s_cell.owner and t_cell.troops < s_cell.troops: # always capture an admiral to the best of your ability, esp. if it's owned by someone else
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=100, dir=neighbor[1]))
                                elif t_cell.owner != s_cell.owner and t_cell.troops < s_cell.troops:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_ALL, weight=80, dir=neighbor[1]))
                                else:
                                    potential_moves.append(self.PotentialMove(s_cell, t_cell, action=ACTION_MOVE_NORMAL, weight=10, dir=neighbor[1]))
                                                                    
                            elif t_cell.cell_type == CELL_TYPE_BLANK:                            
                                pass
                                
                            elif t_cell.cell_type in (CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED, CELL_TYPE_MOUNTAIN_BROKEN):                            
                                pass
                            elif t_cell.cell_type in (CELL_TYPE_SHIP, CELL_TYPE_SHIP_2, CELL_TYPE_SHIP_3, CELL_TYPE_SHIP_4):                            
                                pass
                            elif t_cell.cell_type == CELL_TYPE_SWAMP:                            
                                # if cell.troops > 2: # leave small troops to die
                                #     if n is not None:
                                pass
                                                            
            #print(f'len potential_moves is {len(potential_moves)}')
            if len(potential_moves) > 0:
                list_weights = []

                for i in range(len(potential_moves)):
                    list_weights.append(potential_moves[i].weight)

                list_decided_move_or_moves = random.choices(potential_moves, weights=list_weights, k=1) # k indicates how many choices to return.. may be worth increasing above 1 to queue up multiple actions
                first_moves_first = list_decided_move_or_moves[0]

                #print((this_one.source_cell.row, this_one.source_cell.col), action=this_one.action, direction=this_one.dir)
                self.player_queue.add_action_to_queue((first_moves_first.source_cell.row, first_moves_first.source_cell.col), action=first_moves_first.action, direction=first_moves_first.dir)

                #self.queue.append(self.PendingAction(self.parent.user_id, source_address, action, direction))

            
            # FLAIL_THRESHOLD = 3 
            # if len(potential_moves) and len(self.player_queue.queue) <= FLAIL_THRESHOLD:
            #     r1 = random.random() # whether to act
            #     r2 = random.choice([ACTION_MOVE_NORMAL, ACTION_MOVE_HALF, ACTION_MOVE_ALL]) # which action to attempt
            #     r3 = random.choice([DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT])
                
            #     if r1 > .25: # try adding something
            #     #if r1 > .75: # try adding something
            #         #print(f'attempt grow in dir {r3}')
            #         self.player_queue.add_action_to_queue((i,j), action=r2, direction=r3)
                    
            #         if r2 < .1: # 
            #             act = 

                        # if cell.cell_type == CELL_TYPE_SWAMP and cell.troops >2:
                        #     # try to get out of there!
                        #         # weight preferred target cell. High to low:
                        #             # target cell type == admiral and owner != user_id and target troops < source_troops
                        #             # target cell type == admiral and owner != user_id
                        #             # target cell type == admiral and owner == user_id
                        #             # target cell type == city and "enemy troops" < troops (so yes if neutral or owned)
                        #             # target cell type == blank and "enemy troops" < troops (so yes if neutral or owned)
                        #             # target cell type == blank and "enemy troops" > troops (pushing against them)
                        #             # target cell type == city and "enemy troops" > troops (pushing against them)
                        #             # target cell type == mtn and "enemy troops" < troops
                        #             # target cell type == swamp
                                    
                                    
                        #             # n

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
        
        elif pending_action.action == ACTION_MOVE_CITY:
            if (
                start_cell.cell_type in [CELL_TYPE_SHIP, CELL_TYPE_SHIP_2, CELL_TYPE_SHIP_3, CELL_TYPE_SHIP_4] and
                target_cell.cell_type in [CELL_TYPE_BLANK, CELL_TYPE_SHIP, CELL_TYPE_SHIP_2, CELL_TYPE_SHIP_3, CELL_TYPE_SHIP_4]
            ):  
                print('move city!')
                #TODO move this logic elswhere and make it work if player active celled past here quickly
                #TODO 1 day later.. yeah refactor this because it's getting fixed anyway.. gonna let break for now
                self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), ACTION_MOVE_NONE, DIR_NOWHERE)
                self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), ACTION_MOVE_NONE, DIR_NOWHERE)
                self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), ACTION_MOVE_NONE, DIR_NOWHERE)
                self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), ACTION_MOVE_NONE, DIR_NOWHERE)
                return True
            else:
                return False 
            
        elif pending_action.action==ACTION_MOVE_ALL: # move all cells, leaving only 1 cell in admiral cells
            return start_cell.owner == pending_action.user_id
        
        elif pending_action.action in [ACTION_MOVE_NORMAL, ACTION_MOVE_HALF]:
            if start_cell.owner == pending_action.user_id:
                return target_cell.cell_type not in (CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED)
        else:
            raise ValueError('Unexpected action detected')
        
        
        if start_cell.owner == pending_action.user_id and (pending_action.action==ACTION_MOVE_ALL or target_cell.cell_type not in (CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED)):
            return True
        else:
            return False
            
        # pending_action.action 
        # pending_action.direction
        #print(f'Action pending: {next_action.source_address} \t{next_action.action} \t{next_action.direction}')

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
        next_action = self.players[uid].player_queue.pop_queued_action()
        if next_action:
            if self.action_is_valid(next_action):
                source_cell = self.game_board[next_action.source_address]
                target_cell = self.game_board[next_action.target_address]

                starting_troops = source_cell.troops
                if next_action.action == ACTION_MOVE_NORMAL:
                    troops_to_move = starting_troops - 1
                
                elif next_action.action == ACTION_MOVE_HALF:
                    troops_to_move = math.trunc(starting_troops/2) # round down w/ truncate to make sure we never move our last troop

                elif next_action.action == ACTION_MOVE_CITY:
                    troops_to_move = starting_troops
                                            
                elif next_action.action == ACTION_MOVE_ALL:
                    # print(f'cell type {source_cell.cell_type} / in ({CELL_TYPE_ADMIRAL} {CELL_TYPE_SHIP}) ')
                    if source_cell.cell_type in (CELL_TYPE_ADMIRAL, ): #, CELL_TYPE_SHIP):
                        troops_to_move = starting_troops - 1
                    else:
                        troops_to_move = starting_troops
                        if troops_to_move == 0:
                            # print('renounce land (+1 troops bonus)')
                            troops_to_move += 1

                elif next_action.action == ACTION_MOVE_NONE:
                    troops_to_move = 0

                else:
                    raise ValueError('Unexpected action encountered')


                source_cell.troops -= troops_to_move
                source_cell.changed_this_turn = True

                if source_cell.troops <= 0:
                    source_cell.owner = None
                    
                    if next_action.action == ACTION_MOVE_CITY:
                        invading_ship_count = 0
                        
                        if source_cell.cell_type == CELL_TYPE_SHIP: invading_ship_count = 1
                        elif source_cell.cell_type == CELL_TYPE_SHIP_2: invading_ship_count = 2
                        elif source_cell.cell_type == CELL_TYPE_SHIP_3: invading_ship_count = 3
                        elif source_cell.cell_type == CELL_TYPE_SHIP_4: invading_ship_count = 4
                        else: invading_ship_count = 0

                        if target_cell.cell_type == CELL_TYPE_SHIP: invading_ship_count += 1
                        elif target_cell.cell_type == CELL_TYPE_SHIP_2: invading_ship_count += 2
                        elif target_cell.cell_type == CELL_TYPE_SHIP_3: invading_ship_count += 3
                        elif target_cell.cell_type == CELL_TYPE_SHIP_4: invading_ship_count += 4
                            
                        output_type = CELL_TYPE_SHIP

                        if invading_ship_count == 2:
                            output_type = CELL_TYPE_SHIP_2
                        elif invading_ship_count == 3:
                            output_type = CELL_TYPE_SHIP_3
                        elif invading_ship_count == 4:
                            output_type = CELL_TYPE_SHIP_4
                        elif invading_ship_count > 4:
                            output_type = CELL_TYPE_ADMIRAL

                        source_cell.cell_type = CELL_TYPE_BLANK
                        target_cell.cell_type = output_type
                        #print(f'output cell type: {target_cell.cell_type}')


                if target_cell.owner == next_action.user_id: # combine forces
                    target_cell.troops += troops_to_move
                    target_cell.changed_this_turn = True
                
                else: # combat
                    target_cell.troops -= troops_to_move
                    if target_cell.troops < 0:
                        old_owner = target_cell.owner
                        target_cell.troops *= -1
                        target_cell.owner = next_action.user_id
                        target_cell.changed_this_turn = True

                        # Mountain breaking check
                        if target_cell.cell_type in [CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED]:
                            target_cell.cell_type = CELL_TYPE_MOUNTAIN_BROKEN
                            target_cell.changed_this_turn = True

                        # check if player captured target's last admiral - if so you inherit their kingdom
                        if old_owner is not None and target_cell.cell_type == CELL_TYPE_ADMIRAL:
                            if self.get_admiral_count(old_owner) <= 0:
                                print(f'Player {old_owner} defeated')
                                self.hostile_takeover_of_player(victim=old_owner, victor=uid)
                    
                    # Mountain cracking check
                    elif target_cell.cell_type == CELL_TYPE_MOUNTAIN:
                        target_cell.cell_type = CELL_TYPE_MOUNTAIN_CRACKED
                        target_cell.changed_this_turn = True

            else:
                self.pop_until_valid_or_empty(uid)
                
    def advance_game_turn(self): # move / attack / takeover 
        self.turn += 1

        if self.game_mode == GAME_MODE_REPLAY:
            #print(f'Replaying turn {self.turn}')

            RE_COL_TURN = 0 # in the query that populated self.replay_data
            RE_COL_ROW = 1
            RE_COL_COL = 2
            RE_COL_TYPE = 3
            RE_COL_UID = 4
            RE_COL_TROOPS = 5 
            
            if self.replay_data is not None:
                #print('replay data')
                caught_up_yet = False
                while not caught_up_yet:
                    if self.replay_pos < len(self.replay_data):
                        move = self.replay_data[self.replay_pos]
                        # print(f'{self.replay_pos}{move}')
                        if move[RE_COL_TURN] <= self.turn:
                            self.game_board[(move[RE_COL_ROW], move[RE_COL_COL])].cell_type = move[RE_COL_TYPE]
                            self.game_board[(move[RE_COL_ROW], move[RE_COL_COL])].owner = move[RE_COL_UID]
                            self.game_board[(move[RE_COL_ROW], move[RE_COL_COL])].troops = move[RE_COL_TROOPS]
                            
                            self.replay_pos += 1
                        else:
                            caught_up_yet = True

                    else:
                        caught_up_yet = True
                        self.game_status == GAME_STATUS_GAME_OVER_WIN
                        
            else:
                self.game_status == GAME_STATUS_GAME_OVER_WIN



        elif self.game_mode in [GAME_MODE_FFA, GAME_MODE_FFA_CUST]: 
            
            #list_changes_this_turn = []
            # Reset change checker, so that we can look for new changes this turn
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    self.game_board[(i,j)].changed_this_turn = False
        
            ### Cycle through the players in turn_order[]. If the player's queue is not empty, pop the first element and attempt to perform it
            # Invalid moves: 
            #   - player attempts to move out of bounds or into a mountain (except when Move All-ing into a mtn), 
            #   - attempts to move from a cell they don't currently own 
            #   - player has fewer than 2 troops in cell
            # advance to the next move in stack if invalid


            ### Bot behavior phase
            for i in range(len(self.turn_order)):
                behavior = self.players[self.turn_order[i]].bot_behavior
                if behavior == self.GameEntity.BEHAVIOR_AMBUSH_PREDATOR:
                    self.players[self.turn_order[i]].run_ambush_behavior_check() 
                
                if behavior == self.GameEntity.BEHAVIOR_PETRI:
                    self.players[self.turn_order[i]].run_petri_growth_check() 
                    
            ### Action phase
            for i in range(len(self.turn_order)):
                #print(f'Player order: {i}\tid: {self.turn_order[i]}\tName: {self.players[self.turn_order[i]].user_desc}')         
                self.pop_until_valid_or_empty(self.turn_order[i])

            ### growth phase
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    cell_type = self.game_board[(i,j)].cell_type
                    owner = self.game_board[(i,j)].owner
                    
                    ADMIRAL_GROW_RATE = 2
                    CITY_GROW_RATE = 4
                    BLANK_GROW_RATE = 25
                    SWAMP_DRAIN_RATE = 1
                    BROKEN_MTN_GROW_RATE = 50

                    if owner is not None:

                        if ((cell_type == CELL_TYPE_ADMIRAL and self.turn % ADMIRAL_GROW_RATE == 0) or
                            (cell_type == CELL_TYPE_SHIP and self.turn % CITY_GROW_RATE == 0) or
                            (cell_type == CELL_TYPE_BLANK and self.turn % BLANK_GROW_RATE == 0) or
                            (cell_type == CELL_TYPE_MOUNTAIN_BROKEN and self.turn % BROKEN_MTN_GROW_RATE == 0)):                   
                                self.game_board[(i,j)].troops += 1
                                self.game_board[(i,j)].changed_this_turn = True
                        
                        elif cell_type == CELL_TYPE_SWAMP and self.turn % SWAMP_DRAIN_RATE == 0:
                            self.game_board[(i,j)].troops -= 1
                            self.game_board[(i,j)].changed_this_turn = True                            

                        # check for loss of property (eg to swampland)
                        if self.game_board[(i,j)].troops < 0:
                            self.game_board[(i,j)].owner = None
                            self.game_board[(i,j)].troops = 0
                            self.game_board[(i,j)].changed_this_turn = True                            
                                
            
        # refresh the text values of each cell
        for i in range(self.num_rows):
            for j in range(self.num_cols):
                cell = self.game_board[(i,j)]
                cell.update_visibility_status(player_id=0)
                cell.update_display_text()

        # Update land and troop counts for each player
        for i in range(self.num_players):
            self.parent.game.players[i].update_land_count()
            self.parent.game.players[i].update_troop_count()


        if self.game_mode in [GAME_MODE_FFA, GAME_MODE_FFA_CUST]: 
            # Reverse the turn order - this was every other turn, a given player has priority over any other particular player
            self.turn_order.reverse()

            # Update the db w/ any changes this round
            list_changes = []
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    cell = self.game_board[(i,j)]
                    if cell.changed_this_turn:
                        # print(f'Turn {self.turn}\tChange detected in cell {i}x{j}\t{cell.owner}\t{cell.troops}\t{cell.cell_type}')
                        list_changes.append((self.game_id, self.turn, i, j, cell.cell_type, cell.owner, cell.troops))
            
            sql = 'INSERT INTO log_game_moves (game_id, turn_num, row, col, cell_type, player_id, troops) VALUES(?,?,?,?,?,?,?)'
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

    class MadCell:
        
        # ooh what about introducing tides!!! every 100 turns or so the tide goes in and out.. 'blank' cells get washed away during high tide (so growth rate is negative), ships aka cities don't produce troops during low tide (growth rate is 0), broken mtn growth rate affected by tides too (produce 0 at high tide, low at low tide?)
        # color would be light blue at low tide and darker blue at high tide
        # low chance of a storm coming by and wrecking random cells 

        def __init__(self, parent, row, col):
            self.parent = parent
            self.row = row
            self.col = col
            self.cell_type = CELL_TYPE_BLANK
            self.owner = None # user_id of controlling entity, if any
            self.troops = 0 # the strength of this block (defense) and potential offensive strength, depending on cell type and owner
            self.hidden = True # when true, the player character should not be able to see display text or custom formatting of this cell
            self.display_text = tk.StringVar() # what information should the human player be able to glean about this cell?
            self.changed_this_turn = False # any changes to ownership, troop number, or cell type happen this turn?
            self.cell_type_last_seen_by_player = None # once the fog of war has been lifted, the player knows what type of cell is here.. or at least was here
            
            self.item_id = None # one of the opensimplex.noise3array values for this cell - used to determine to spawn here - may also be used to determine admiral spawn locations
            self.item_amt = None # another noise3array value - used to determine how much of an item should be here

        def update_visibility_status(self, player_id):
            if not self.parent.parent.fog_of_war:
                self.hidden = False
                # self.cell_type_last_seen_by_player = self.cell_type # on second thought let's not
            
            elif self.owner == player_id:
                self.hidden = False
                self.cell_type_last_seen_by_player = self.cell_type
            
            elif (
                (self.row>0 and self.parent.game_board[(self.row-1, self.col)].owner == player_id) or  # top
                (self.row>0 and self.col>0 and self.parent.game_board[(self.row-1, self.col-1)].owner == player_id) or # top left
                (self.row>0 and self.col<(self.parent.num_cols-1) and self.parent.game_board[(self.row-1, self.col+1)].owner == player_id) or # top right
                (self.col>0 and self.parent.game_board[(self.row, self.col-1)].owner == player_id) or # left
                (self.col<(self.parent.num_cols-1) and self.parent.game_board[(self.row, self.col+1)].owner == player_id) or # right
                (self.row<(self.parent.num_rows-1) and self.col>0 and self.parent.game_board[(self.row+1, self.col-1)].owner == player_id) or # bot left
                (self.row<(self.parent.num_rows-1) and self.parent.game_board[(self.row+1, self.col)].owner == player_id) or # bot
                (self.row<(self.parent.num_rows-1) and self.col<(self.parent.num_cols-1) and self.parent.game_board[(self.row+1, self.col+1)].owner == player_id)# bot right
                ):
                    # print(f'{(row, col)} {player_id}')
                    self.hidden = False
                    self.cell_type_last_seen_by_player = self.cell_type
                
            else:
                self.hidden = True             
        
        def update_display_text(self):
            str_troops = self.troops if self.troops > 0 else ''
            
            if self.hidden:
                if self.cell_type_last_seen_by_player is not None: #oops i think this is logically buggy TODO make this report the last cell type seen, not just the current cell type masked if it has been seen before
                    if self.cell_type == CELL_TYPE_SHIP:
                        self.display_text.set('C')  
                    elif self.cell_type == CELL_TYPE_ADMIRAL:                        
                            self.display_text.set('A')  
                    elif self.cell_type in [CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED]:
                        self.display_text.set('M')
                    elif self.cell_type == CELL_TYPE_SWAMP:
                        self.display_text.set('S')
                    else:
                        self.display_text.set('')

                elif self.cell_type in [CELL_TYPE_SHIP, CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED, CELL_TYPE_MOUNTAIN_BROKEN]:
                    self.display_text.set('M?')
                else:
                    self.display_text.set('')

            else:
                if self.cell_type == CELL_TYPE_SHIP:
                    self.display_text.set(f'C{str_troops}')  
                elif self.cell_type == CELL_TYPE_ADMIRAL:                        
                        self.display_text.set(f'A{str_troops}')  
                elif self.cell_type == CELL_TYPE_MOUNTAIN:
                    self.display_text.set('M')
                elif self.cell_type == CELL_TYPE_MOUNTAIN_CRACKED:
                    self.display_text.set(f'm{str_troops}')
                elif self.cell_type == CELL_TYPE_MOUNTAIN_BROKEN:
                    self.display_text.set(f'~{str_troops}')
                elif self.cell_type == CELL_TYPE_SWAMP:
                    self.display_text.set(f'S{str_troops}')

                else:
                    self.display_text.set(f'{str_troops}')  
