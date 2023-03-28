# ### MADMIRALS!!!


# game of life as opponent entity(ies) - can adjust win/lose conditions around ability to influence the preexisting algo
# spinoff idea: petri wars: spend points to decide numner of starting cells and their respective locations and traits.. then it plays out like conway's game of lie, except maybe w/ ability to place powerups to influence gameplay!
import random
import tkinter as tk 
from tkinter import messagebox
import time
from functools import partial
import math
import json
import opensimplex
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

DIR_UP = 1 
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4

class MadmiralsGameManager:
    GAME_TURN_SPEED = .5 # in s
    CYCLE_SPEED = 100 # ms between checks of game loop
    DEFAULT_ROWS = 9
    DEFAULT_COLS = 16

    def __init__(self):
        num_players = 5

        self.gui = self.MadmiralsGUI(self)
        self.game = self.MadmiralsGameInstance(self, num_rows=self.DEFAULT_ROWS, num_cols=self.DEFAULT_COLS, game_mode='normal', num_players=num_players)
        
        self.gui.populate_cell_frame()
        self.gui.populate_scoreboard_frame()
        self.gui.populate_win_conditions_frame()
        
         
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop

        self.game.game_status = self.game.GAME_STATUS_IN_PROGRESS

        self.game_loop() # start the game cycle!

    def game_loop(self):
        # print('game loop')

        if self.game.game_status == self.game.GAME_STATUS_IN_PROGRESS:
            now = time.time()
            # print(now - self.last_turn_timestamp)
            
            if  (now - self.last_turn_timestamp) >= self.GAME_TURN_SPEED:
                self.last_turn_timestamp = now
                self.game.advance_game_turn()
                        
            self.gui.render()

            # if self.game.turn > 5:
            #     self.game.game_status = self.game.GAME_STATUS_GAME_OVER
        
        else:
            self.gui.render_game_over()
            
        self.after_id = self.gui.root.after(self.CYCLE_SPEED, self.game_loop) #try again in (at least) X ms


    class MadmiralsGUI:
        def __init__(self, parent):
            self.root = tk.Tk()
            self.root.title('Madmirals')
            self.root.config(menu=self.create_menu_bar(self.root))
            self.parent = parent
            self.assets = self.GUI_Assets(r'C:\Users\thema\Documents\Python Scripts\Madmirals\assets\\') # TODO TEMP! 
            self.fog_of_war= False # or True
            
            self.frame_game_board = tk.Frame(master=self.root)
            self.frame_scoreboard = tk.Frame(master=self.root)
            self.frame_win_conditions = tk.Frame(master=self.root)
            
            self.game_cell_Buttons = {}

        class GUI_Assets: 
            MAGIC_NUM_TO_FIX_CELL_SIZE = 5 # tk.Button seems to add 5 px to the height and width 
            
            def __init__(self, dir_img):                
                self.img_mountain   = tk.PhotoImage(file=f'{dir_img}mountain.gif')    
                self.img_swamp      = tk.PhotoImage(file=f'{dir_img}swamp.gif')    

                self.cell_width = self.img_mountain.width() + self.MAGIC_NUM_TO_FIX_CELL_SIZE # assumes all cell images are identically sized
                self.cell_height = self.img_mountain.height() + self.MAGIC_NUM_TO_FIX_CELL_SIZE
            

        def btn_left_click(self, address, event):
            self.parent.game.active_cell = address
            player_id = 0
            self.parent.game.players[player_id].retreat_mode = False
                

        def btn_middle_click(self, address, event):
            player_id = 0
            
            if self.parent.game.active_cell == address: # if we are middle clicking on the already active cell, toggle retreat mode
                self.parent.game.players[player_id].retreat_mode = not self.parent.game.players[player_id].retreat_mode
            else:
                self.parent.game.players[player_id].retreat_mode = True
    
            self.parent.game.active_cell = address
            

        def btn_right_click(self, address, event):
            #print('right click = activate "move half" mode for next action')
            self.parent.game.active_cell = address
            
            player_id = 0
            self.parent.game.players[player_id].retreat_mode = False
            self.parent.game.players[player_id].right_click_pending_address = address
            #self.parent.game.active_cell = address
        
        
        def key_press_handler(self, event):
            # print(event)

            CHAR_ESCAPE = '\x1b'
            
            interesting_chars = ['W', 'w', 'A', 'a', 'S','s', 'D', 'd', 'E', 'e', CHAR_ESCAPE]
            interesting_syms = ['Up', 'Down', 'Left', 'Right']
            player_id = 0
            
            if event.char in interesting_chars or event.keysym in interesting_syms:
                active_cell_address = self.parent.game.active_cell
                
                if event.char == CHAR_ESCAPE:
                    if self.parent.game.active_cell:
                        self.parent.game.active_cell = None
                    else:
                        print('todo toggle pause window on ESC if nothing is selected?')
                
                elif event.char in ['E', 'e']: # undo a step
                    last_action = self.parent.game.players[player_id].player_queue.pop_queued_action(-1)

                    if last_action:
                        self.parent.game.active_cell = last_action.source_address
                        #print('undo event!')

                elif self.parent.game.active_cell:
                    # print(f'char {event.char} pressed. Active cell is {active_cell_address}')
                
                    if   event.char in ['W', 'w'] or event.keysym == 'Up': dir = DIR_UP
                    elif event.char in ['A', 'a'] or event.keysym == 'Left': dir = DIR_LEFT
                    elif event.char in ['S', 's'] or event.keysym == 'Down': dir = DIR_DOWN
                    elif event.char in ['D', 'd'] or event.keysym == 'Right': dir = DIR_RIGHT
                    else:
                        raise ValueError('Unexpected keyboard input')

                    if self.parent.game.players[player_id].right_click_pending_address == active_cell_address:
                        action = self.parent.game.ACTION_MOVE_HALF
                    elif self.parent.game.players[player_id].retreat_mode:
                        action = self.parent.game.ACTION_MOVE_ALL # downstread we will override this when crossing admirals/cities
                    else:
                        action = self.parent.game.ACTION_MOVE_NORMAL
            
                    self.parent.game.players[player_id].player_queue.add_action_to_queue(active_cell_address, action, dir) 
                    self.parent.game.move_active_cell(dir)
                    self.parent.game.players[player_id].right_click_pending_address = None
                    
   

        def create_menu_bar(self, root):
            menubar = tk.Menu(root)
            
            filemenu = tk.Menu(menubar, tearoff=0)
            filemenu.add_command(label='New Game', command=self.restart_game)
            filemenu.add_separator()
            filemenu.add_command(label='About', command=partial(self.open_about_window, root))
            filemenu.add_separator()
            filemenu.add_command(label='Exit', command=self.root.quit)
            
            game_menu = tk.Menu(menubar, tearoff=0)
            game_menu.add_command(label='Toggle Fog of War', command=self.toggle_fog_of_war)
            game_menu.add_command(label='Toggle Debug Mode', command=self.toggle_debug_menu)
            
            menubar.add_cascade(label='File', menu=filemenu)
            menubar.add_cascade(label='Game', menu=game_menu)

            return menubar
        
        def restart_game(self):
            print('TODO Restart game ')

        def toggle_fog_of_war(self):
            self.fog_of_war = not self.fog_of_war

        def toggle_debug_menu(self):
            self.parent.debug_mode = not self.parent.debug_mode

        
        def open_about_window(self, root):
            top= tk.Toplevel(root)
            top.geometry('500x250')
            top.title('About Madmirals')
            tk.Label(top, text= 'All About Madmirals', font=('Helvetica 14 bold')).place(x=150,y=80)

    
        def populate_cell_frame(self):
            self.frame_game_board.destroy()
            self.frame_game_board = tk.Frame(master=self.root)
            
            self.board_cell_buttons = {}

            for i in range(self.parent.game.num_rows):
                for j in range(self.parent.game.num_cols):
                    #self.board_cell_buttons[(i, j)] = tk.Button(master=self.frame_game_board, bg='light grey', textvariable=self.parent.game.game_board[(i,j)].display_text, width=8, height=4) # add cell to the dictionary and establish default behavior
                    self.board_cell_buttons[(i, j)] = tk.Button(master=self.frame_game_board, 
                        textvariable=self.parent.game.game_board[(i,j)].display_text, 
                        width=6, height=3,
                        highlightcolor='orange'                        
                        ) # add cell to the dictionary and establish default behavior
                    self.board_cell_buttons[(i, j)].grid(row=i, column=j) # place the cell in the frame

                    self.board_cell_buttons[(i, j)].bind('<Button-1>', partial(self.btn_left_click, (i,j)))
                    self.board_cell_buttons[(i, j)].bind('<Button-2>', partial(self.btn_middle_click, (i,j)))
                    self.board_cell_buttons[(i, j)].bind('<Button-3>', partial(self.btn_right_click, (i,j)))

            self.root.bind('<Key>', self.key_press_handler)
            self.frame_game_board.grid(row=0, column=0, columnspan=3, rowspan=4, pady=5)
            self.frame_game_board.focus_set()

        def populate_win_conditions_frame(self):
            print('populate_win_conditions_frame')
            self.frame_win_conditions.destroy()
            self.frame_win_conditions = tk.Frame(master=self.root)

            self.lbl_win_header = tk.Label(master=self.frame_win_conditions, text='Win Conditions', font=('Arial 22 bold'))
            self.lbl_win_desc = tk.Label(master=self.frame_win_conditions, text='Capture all Admiral cells', font=('Arial 18 bold'))
            
            self.lbl_lose_header = tk.Label(master=self.frame_win_conditions, text='Lose Conditions', font=('Arial 22 bold'))
            self.lbl_lose_desc = tk.Label(master=self.frame_win_conditions, text='Troop count reaches 0', font=('Arial 18 bold'))
            

            self.lbl_win_header.grid(row=0, column=0)
            self.lbl_win_desc.grid(row = 1, column = 0)
            self.lbl_lose_header.grid(row=2, column=0)
            self.lbl_lose_desc.grid(row = 3, column = 0)




            self.frame_win_conditions.grid(row=1, column=9, sticky='n')


        def populate_scoreboard_frame(self):
            self.frame_scoreboard.destroy()
            self.frame_scoreboard = tk.Frame(master=self.root)

            self.lbl_header = tk.Label(master=self.frame_scoreboard, text='Scoreboard', font=('Arial 22 bold'))
            self.lbl_header.grid(row=0, column=0, columnspan=3, sticky='N')
            

            self.lbl_turn_count = tk.Label(master=self.frame_scoreboard, text='Turn 0', font=('Arial 18 bold'))
            self.lbl_turn_count.grid(row = 1, column = 0)

            self.lbls_name = []
            self.lbls_cells = []
            self.lbls_troops = []

            ROW_OFFSET = 2
            for i in range(self.parent.game.num_players):
                self.lbls_name.append(tk.Label(master=self.frame_scoreboard, text=f'player {i}'))
                self.lbls_cells.append(tk.Label(master=self.frame_scoreboard, text=f'cells {i}'))
                self.lbls_troops.append(tk.Label(master=self.frame_scoreboard, text=f'troops {i}'))

                self.lbls_name[i].grid(row = i + ROW_OFFSET, column = 0)
                self.lbls_cells[i].grid(row = i + ROW_OFFSET, column = 1)
                self.lbls_troops[i].grid(row = i + ROW_OFFSET, column = 2)

            self.frame_scoreboard.grid(row=0, column=9, sticky='n')
        

        def cell_should_be_visible(self, row, col, player_id):
            if self.parent.game.game_board[(row, col)].owner == player_id:
                return True
            elif (
                (row>0 and self.parent.game.game_board[(row-1, col)].owner == player_id) or  # top
                (row>0 and col>0 and self.parent.game.game_board[(row-1, col-1)].owner == player_id) or # top left
                (row>0 and col<(self.parent.game.num_cols-1) and self.parent.game.game_board[(row-1, col+1)].owner == player_id) or # top right
                
                (col>0 and self.parent.game.game_board[(row, col-1)].owner == player_id) or # left
                (col<(self.parent.game.num_cols-1) and self.parent.game.game_board[(row, col+1)].owner == player_id) or # right

                (row<(self.parent.game.num_rows-1) and col>0 and self.parent.game.game_board[(row+1, col-1)].owner == player_id) or # bot left
                (row<(self.parent.game.num_rows-1) and self.parent.game.game_board[(row+1, col)].owner == player_id) or # bot
                (row<(self.parent.game.num_rows-1) and col<(self.parent.game.num_cols-1) and self.parent.game.game_board[(row+1, col+1)].owner == player_id)# bot right
                ):
                    return True
                
            else:
                return False
            

        def render(self):            
            for i in range(self.parent.game.num_rows):
                for j in range(self.parent.game.num_cols):
                    uid = self.parent.game.game_board[(i,j)].owner

                    relief = tk.RAISED if self.parent.game.active_cell == (i,j) else tk.SUNKEN
                    cell_type = self.parent.game.game_board[(i,j)].cell_type

                    if self.fog_of_war and not self.cell_should_be_visible(i, j, player_id=0):
                        bg_color = 'black'
                        fg_color = 'black'
                    else:
                        bg_color = self.parent.game.GameEntity.colors[uid][0]
                        fg_color = self.parent.game.GameEntity.colors[uid][1]
                   

                    #font = ('Arial 18 bold') if cell_type == self.parent.game.MadCell.CELL_TYPE_MOUNTAIN else ('Arial 14')  # ooh this was a fun experiment - mountains stand out more, and clusters of non-mountains look like meadows..
                    font = ('Arial 16 bold')
                    
            
                    if False: #TODO FIX img behavior and add other images
                        img = self.assets.img_mountain if cell_type == self.parent.game.MadCell.CELL_TYPE_MOUNTAIN else None
                    else:
                        img = None


                    self.board_cell_buttons[(i, j)].config(bg=bg_color, fg=fg_color, relief=relief, image=img, font=font)

            
            self.update_score_board()


        def update_score_board(self):
            ##print('updating scoreboard')
            # calculate current troops and land for each player. Sort by troops (desc) for now.. maybe add option to customize
            # then update the text label array for the scoreboard.. [0] should be first sorted, not player 0.
            #TODO HERE next
            dict_names = {}
            dict_land = {}
            dict_troops = {}
            players = self.parent.game.players

            
            self.lbl_turn_count.configure(text=f'Turn {self.parent.game.turn}')

            for i in range(self.parent.game.num_players):
                uid = players[i].user_id
                dict_names[uid] = players[i].user_desc
                dict_land[uid] = players[i].get_land_count()
                dict_troops[uid] = players[i].get_troop_count()

                if players[i].active:
                    bg = self.parent.game.GameEntity.colors[uid][0]
                    fg = self.parent.game.GameEntity.colors[uid][1]
                else:
                    bg = 'light grey'
                    fg = 'dark grey'

                #self.players[victim].active = False

                # TODO determine sort order            
                self.lbls_name[i].configure(text=dict_names[uid], bg=bg, fg=fg)
                self.lbls_cells[i].configure(text=dict_land[uid], bg=bg, fg=fg)
                self.lbls_troops[i].configure(text=dict_troops[uid], bg=bg, fg=fg)

            if False:
                print(f'Turn {self.parent.game.turn}\tland and troops:')
                print(dict_land)
                print(dict_troops)


        def render_game_over(self): # make any visual updates to reflect that the game status is currently game over
            print('render_game_over')
            pass



    class MadmiralsGameInstance:
        GAME_STATUS_INIT = -1 # loading
        GAME_STATUS_READY = 1 # able to start
        GAME_STATUS_IN_PROGRESS = 2 #
        GAME_STATUS_PAUSE = 3 #
        GAME_STATUS_GAME_OVER = 4 # game instance is complete and can no longer be played

        ACTION_MOVE_NORMAL = 1
        ACTION_MOVE_HALF = 2
        ACTION_MOVE_ALL = 3
        ACTION_CHARGE = 777 # idea: start a chain of move_normals that extends to the edge of the board (or until it hits a barrier)
                

        def __init__(self, parent, num_rows, num_cols, game_mode, num_players):
            self.parent = parent
            
            self.game_status = self.GAME_STATUS_INIT
            self.turn = 0

            self.num_rows = num_rows
            self.num_cols = num_cols
            self.num_players = num_players

            self.active_cell = None # cell address 

            self.players = {} # contains the player objects w/ numeric id
            self.turn_order = [] # the initial order of turns.. can be eg shuffled between turns, or assign priority keys and flip flop between whether or high or low has priority
            
            for i in range(num_players):
                bg = self.GameEntity.colors[i][0]
                fg = self.GameEntity.colors[i][1]

                player_id = i

                bot_behavior = None
                if i == 1: bot_behavior = self.GameEntity.BEHAVIOR_PETRI
                if i == 2: bot_behavior = self.GameEntity.BEHAVIOR_PETRI
                if i == 3: bot_behavior = self.GameEntity.BEHAVIOR_PETRI
                if i == 4: bot_behavior = self.GameEntity.BEHAVIOR_AMBUSH_PREDATOR

                self.players[i] = self.GameEntity(self, player_id, f'Player {i}', bg, fg, bot_behavior)
                self.turn_order.append(player_id)
        
            self.game_board = {}
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    self.game_board[(i, j)] = self.MadCell(self, i, j)

            # self.add_dev_starting_condition()


            self.seed = str(random.random())
            # self.seed = str(0.7625310337113341)
            # self.seed = str(0.1234567890123456)
            # self.seed = str(0.7845326548911178)
            # self.seed = str(0.1112223334455666)
            # self.seed = str(0.9999999999999999)


            self.generate_game_world()


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

                # def add_to_queue(self, target_cell, continue_left=False, continue_up=False, continue_down=False, continue_right=False):
                #     item = self.SearchQueueItem()
                #     self.queue.append()
            
            # target_cell.CELL_TYPE_BLANK = 0
            # CELL_TYPE_ADMIRAL = 1
            # CELL_TYPE_MOUNTAIN = 2
            # CELL_TYPE_CITY = 3
            # CELL_TYPE_SWAMP = 4
                
            
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
            print(f'Board size: {self.num_rows}x{self.num_cols}\tNum Players{self.num_players}\tSeed: {self.seed}\t')
                
            def get_digit(number, digit):
            # Returns one of the 16 digits of the seed. I
                
                DIGIT_OFFSET = 2 # because seed is in format '0.xyz'
                str_num = str(number)[DIGIT_OFFSET:]

                return int(str_num[digit % len(str_num)]) # by using modulus we don't need to implement a max digit
                # TODO test what happens w negative numbers and make sure it never gets given invalid input
            

            MIN_DISTANCE_BETWEEN_ADMIRALS = 4

            # Add spawns
            spawn_points_added = 0 
            for p in range(self.num_players):
                spawn_found = False 
                digit = 0
                while(not spawn_found):
                    p_row_target = (get_digit(self.seed, digit+p-1) * get_digit(self.seed, digit+p+1)) % self.num_rows
                    p_col_target = (get_digit(self.seed, digit+p*2) * get_digit(self.seed, digit+p+3)) % self.num_cols
                    # print(f'{p_row_target}x{p_col_target}')
                    
                    target_cell = self.game_board[(p_row_target, p_col_target)]

                    if target_cell.owner == None:
                        if spawn_points_added == 0 or (self.closest_instance_of_entity(target_cell.CELL_TYPE_ADMIRAL, target_cell) >= MIN_DISTANCE_BETWEEN_ADMIRALS):
                            target_cell.owner = self.players[p].user_id
                            target_cell.cell_type = target_cell.CELL_TYPE_ADMIRAL
                            target_cell.troops = 1
                            spawn_points_added +=1
                            
                            spawn_found = True
                            print(f'added admiral to cell ({target_cell.row}, {target_cell.col})')
                        
                        else:
                            print('still looking for a spot')

                    else:
                        digit += 1  
                        print('b')

            MOUNTAIN_SPAWN_RATE = .09
            CITY_SPAWN_RATE = .05

                #             col_order = list(range(self.parent.num_cols))
                # random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
                # random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves

                # for i in row_order: 
                #     for j in col_order:

            


            #             num_attempts = 0
            # num_added = 0
            # if self.parent.debug_mode: attempt_start_time = time.time()

            # while (num_added < num_bombs_to_add):
            #     num_attempts = num_attempts + 1       
            #     target_row = rand.randrange(self.num_rows)
            #     target_col = rand.randrange(self.num_cols)
                
            #     if not self.board[(target_row, target_col)].contains_bomb:
            #         self.board[(target_row, target_col)].contains_bomb = True
            #         self.num_bombs += 1
                    # num_added += 1

            # Add cities and mountains
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    digit_ten = get_digit(self.seed, i)
                    digit_one = get_digit(self.seed, j)
                    # digit_ten = get_digit(self.seed, i^2+j^2)
                    # digit_one = get_digit(self.seed, i*2+j-1)

                    if (digit_ten*10+digit_one)/100 > MOUNTAIN_SPAWN_RATE:
                        pass


                        # print((digit_ten*10+digit_one)/100 )
                        # print('mountain time')
                    else:
                        
                        pass
                        #print('nah')
                    
                    # if (self.game_board[(i, j)].owner == uid) and (self.game_board[(i, j)].cell_type== self.MadCell.CELL_TYPE_ADMIRAL):

   

            # Add mountains and swamps and neutral cities and other starting conditions
            

        def get_admiral_count(self, uid):
            print('get_admiral_count')
            count = 0

            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    if (self.game_board[(i, j)].owner == uid) and (self.game_board[(i, j)].cell_type== self.MadCell.CELL_TYPE_ADMIRAL):

                    # self.MadCell.CELL_TYPE_ADMIRAL
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

                self.active_cell = (row, col)


        def hostile_takeover_of_player(self, victim, victor):
            TAKEOVER_KEEP_RATE = .5

            self.players[victim].active = False
            
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    if self.game_board[(i,j)].owner == victim:
                        self.game_board[(i,j)].owner = victor

                        self.game_board[(i,j)].troops = math.ceil(self.game_board[(i,j)].troops * TAKEOVER_KEEP_RATE)


        def add_dev_starting_condition(self):  
            print('add_dev_starting_condition')          
            self.game_board[(0,0)].owner = 0
            self.game_board[(0,0)].troops = 50
            
            self.game_board[(0,5)].owner = 0
            self.game_board[(0,5)].troops = 40
            self.game_board[(0,6)].owner = 1
            self.game_board[(0,6)].troops = 40
            self.game_board[(0,7)].owner = 2
            self.game_board[(0,7)].troops = 40
            self.game_board[(0,8)].owner = 3
            self.game_board[(0,8)].troops = 40

            self.game_board[(5,1)].cell_type = self.MadCell.CELL_TYPE_MOUNTAIN
            self.game_board[(5,2)].cell_type = self.MadCell.CELL_TYPE_MOUNTAIN
            self.game_board[(7,1)].cell_type = self.MadCell.CELL_TYPE_MOUNTAIN
            self.game_board[(0,3)].cell_type = self.MadCell.CELL_TYPE_MOUNTAIN

            
            self.game_board[(1,1)].owner = 0
            self.game_board[(1,1)].cell_type = self.MadCell.CELL_TYPE_ADMIRAL

            self.game_board[(1,2)].owner = 0
            self.game_board[(1,2)].cell_type = self.MadCell.CELL_TYPE_CITY
            
            self.game_board[(2,2)].owner = 0
            self.game_board[(2,2)].troops = 40
            
            self.game_board[(4,2)].owner = 3
            self.game_board[(4,2)].cell_type = self.MadCell.CELL_TYPE_ADMIRAL
            
            self.game_board[(5,2)].owner = 1
            self.game_board[(5,2)].cell_type = self.MadCell.CELL_TYPE_ADMIRAL
            
            self.game_board[(5,5)].owner = 2
            self.game_board[(5,5)].cell_type = self.MadCell.CELL_TYPE_CITY
            
            self.game_board[(5,6)].owner = 2
            self.game_board[(5,6)].cell_type = self.MadCell.CELL_TYPE_SWAMP
            self.game_board[(5,6)].troops = 5

            for p in range(4):
                for moves in range(6):
                    self.players[p].player_queue.add_action_to_queue((moves, p + 5), self.ACTION_MOVE_NORMAL, DIR_DOWN) 
            
            self.players[0].player_queue.add_action_to_queue((0,0), self.ACTION_MOVE_NORMAL, DIR_DOWN) 
            self.players[0].player_queue.add_action_to_queue((1,0), self.ACTION_MOVE_NORMAL, DIR_DOWN) 
            self.players[0].player_queue.add_action_to_queue((2,0), self.ACTION_MOVE_NORMAL, DIR_DOWN) 
            self.players[0].player_queue.add_action_to_queue((3,0), self.ACTION_MOVE_NORMAL, DIR_RIGHT) 
            self.players[0].player_queue.add_action_to_queue((3,1), self.ACTION_MOVE_NORMAL, DIR_RIGHT) 
            self.players[0].player_queue.add_action_to_queue((3,2), self.ACTION_MOVE_NORMAL, DIR_DOWN) 
            
            self.players[1].player_queue.add_action_to_queue((3,1), self.ACTION_MOVE_NORMAL, DIR_DOWN) 
            self.players[1].player_queue.add_action_to_queue((4,1), self.ACTION_MOVE_NORMAL, DIR_RIGHT) 
            self.players[1].player_queue.add_action_to_queue((4,2), self.ACTION_MOVE_HALF, DIR_DOWN) 
            self.players[1].player_queue.add_action_to_queue((4,2), self.ACTION_MOVE_HALF, DIR_UP) 
            
            #print(self.players[0].player_queue.print_queue())
            

        class GameEntity:
            colors = { # by player id - tuples of (bg color, fg color)
                None: ('light grey', 'black'),
                0: ('dark green', 'white'),
                1: ('light green', 'black'),
                2: ('crimson', 'white'),
                3: ('violet', 'black'),
                4: ('light blue', 'dark grey'),
                5: ('orange', 'black'),
                6: ('red', 'white')
            }

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
                
                self.player_queue = self.ActionQueue(self)

                self.bot_behavior = bot_behavior # what role(s) should this entity perform? None if regular player -- could do this as a dict of one or more behaviors!

                self.right_click_pending_address = None # if the player right clicked on a cell, be ready to move half of troops instead of all
                self.retreat_mode = False # if true, attempt to move ALL troops instead of all but one


            def get_land_count(self):
                num_land = 0
                for i in range(self.parent.num_rows):
                    for j in range(self.parent.num_cols):
                        if self.parent.game_board[(i,j)].owner == self.user_id:
                            num_land += 1

                return num_land

            def get_troop_count(self):
                num_troops = 0
                for i in range(self.parent.num_rows):
                    for j in range(self.parent.num_cols):
                        if self.parent.game_board[(i,j)].owner == self.user_id:
                            num_troops += self.parent.game_board[(i,j)].troops

                return num_troops
            
            class ActionQueue:
                QUEUE_LIMIT = 100 # do not accept new queued moves if the player has this many pending

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
                        else:
                            raise ValueError('Invalid direction provided!')                            
                
                def add_action_to_queue(self, source_address, action, direction):
                    self.queue.append(self.PendingAction(self.parent.user_id, source_address, action, direction))

                def print_queue(self):
                    print(f'Action queue for entity {self.parent.user_desc}')
                    for q in self.queue:
                        print(f'{q.source_address} \t{q.action} \t{q.direction}')

                def pop_queued_action(self, pos=0):
                    #print(len(self.queue))
                    if len(self.queue)>0:
                        #print('have an action')
                        return self.queue.pop(pos)
                    else:
                        #print('no actions to give')
                        return None
                

            def run_ambush_behavior_check(self):
                pass 
                # print(f'run_ambush_behavior_check for: {self.user_desc}')
                

            def run_petri_growth_check(self):
                #print(f'run_petri_growth_check for: {self.user_desc}')
                
                row_order = list(range(self.parent.num_rows))
                col_order = list(range(self.parent.num_cols))
                random.shuffle(row_order) # Shuffle the order to improve the randomness of results 
                random.shuffle(col_order) # - otherwise there would be noticeable waves pf top left to bottom right moves

                for i in row_order: 
                    for j in col_order:

                        if len(self.player_queue.queue) <= self.player_queue.QUEUE_LIMIT:

                            if self.parent.game_board[(i,j)].owner == self.user_id:
                                r1 = random.random() # whether to act
                                r2 = random.choice([self.parent.ACTION_MOVE_NORMAL, self.parent.ACTION_MOVE_HALF, self.parent.ACTION_MOVE_ALL]) # which action to attempt
                                r3 = random.choice([DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT])
                                

                                if r1 > .25: # try adding something
                                #if r1 > .75: # try adding something
                                    #print(f'attempt grow in dir {r3}')
                                    self.player_queue.add_action_to_queue((i,j), action=r2, direction=r3)
                                    
                                    # if r2 < .1: # 
                                    #     act = 
                        else:
                            pass
                            # print(f'Player {self.user_desc} attempted to exceed queue limit!')
                    

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
            
            if start_cell.owner == pending_action.user_id and target_cell.cell_type not in (target_cell.CELL_TYPE_MOUNTAIN,):
                return True
            else:
                return False
             
            # pending_action.action 
            # pending_action.direction
            #print(f'Action pending: {next_action.source_address} \t{next_action.action} \t{next_action.direction}')

        def end_game_check(self):
            #print('end_game_check')
            num_active = 0

            for i in range(self.num_players):
                if self.players[i].active:
                    num_active += 1 
            
            # print(f'num active {num_active}')
            # return False
            return num_active <= 1
            #tkinter.messagebox.askokcancel(title=None, message=None, **options)
        
        
        def advance_game_turn(self): # move / attack / takeover 
            self.turn += 1

            if self.end_game_check():
                tk.messagebox.askokcancel(title='GG', message='gg')
                self.game_status = self.GAME_STATUS_GAME_OVER

            ### Cycle through the players in turn_order[]. If the player's queue is not empty, pop the first element and attempt to perform it
            # Invalid moves: 
            #   - player attempts to move out of bounds or into a mountain, 
            #   - attempts to move from a cell they don't currently own 
            #   - player has fewer than 2 troops in cell
            # advance to the next move in stack if invalid

            def pop_until_valid_or_empty(uid):               
                next_action = self.players[uid].player_queue.pop_queued_action()
                if next_action:
                    #print(f'Action pending: {next_action.source_address} \t{next_action.action} \t{next_action.direction}\tValid move: {self.action_is_valid(next_action)}')
                    
                    if self.action_is_valid(next_action):
                        starting_troops = self.game_board[next_action.source_address].troops
                        if next_action.action == self.ACTION_MOVE_NORMAL:
                            troops_to_move = starting_troops - 1
                        
                        elif next_action.action == self.ACTION_MOVE_HALF:
                            troops_to_move = math.trunc(starting_troops/2) # round down w/ truncate to make sure we never move our last troop

                        elif next_action.action == self.ACTION_MOVE_ALL:
                            # print(f'cell type {self.game_board[next_action.source_address].cell_type} / in ({self.MadCell.CELL_TYPE_ADMIRAL} {self.MadCell.CELL_TYPE_CITY}) ')
                            if self.game_board[next_action.source_address].cell_type in (self.MadCell.CELL_TYPE_ADMIRAL, ): #, self.MadCell.CELL_TYPE_CITY):
                                troops_to_move = starting_troops - 1
                            else:
                                troops_to_move = starting_troops
                                if troops_to_move == 0:
                                    print('renounce land (+1 troops bonus)')
                                    troops_to_move += 1

                        else:
                            raise ValueError('Unexpected action encountered')


                        self.game_board[next_action.source_address].troops -= troops_to_move
                        
                        if self.game_board[next_action.source_address].troops <= 0:
                            self.game_board[next_action.source_address].owner = None

                        # if next_action.action == self.ACTION_MOVE_ALL and troops_to_move == 0:
                        #     self.game_board[next_action.source_address].owner = None
                        
                        if self.game_board[next_action.target_address].owner == next_action.user_id: # combine forces
                            self.game_board[next_action.target_address].troops += troops_to_move
                        
                        else: # combat
                            self.game_board[next_action.target_address].troops -= troops_to_move
                            if self.game_board[next_action.target_address].troops < 0:
                                old_owner = self.game_board[next_action.target_address].owner
                                
                                self.game_board[next_action.target_address].troops *= -1
                                self.game_board[next_action.target_address].owner = next_action.user_id

                                # check if player captured target's last admiral - if so you inherit their kingdom
                                if old_owner is not None and self.game_board[next_action.target_address].cell_type == self.MadCell.CELL_TYPE_ADMIRAL:
                                    if self.get_admiral_count(old_owner) <= 0:
                                        print(f'Player {old_owner} defeated')
                                        self.hostile_takeover_of_player(victim=old_owner, victor=uid)

                    else:
                        pop_until_valid_or_empty(uid)
                                


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
                pop_until_valid_or_empty(self.turn_order[i])


            ### growth phase
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    cell_type = self.game_board[(i,j)].cell_type
                    owner = self.game_board[(i,j)].owner
                    
                    ADMIRAL_GROW_RATE = 2
                    CITY_GROW_RATE = 4
                    BLANK_GROW_RATE = 25
                    SWAMP_DRAIN_RATE = 4

                    if owner is not None:

                        if ((cell_type == self.MadCell.CELL_TYPE_ADMIRAL and self.turn % ADMIRAL_GROW_RATE == 0) or
                            (cell_type == self.MadCell.CELL_TYPE_CITY and self.turn % CITY_GROW_RATE == 0) or
                            (cell_type == self.MadCell.CELL_TYPE_BLANK and self.turn % BLANK_GROW_RATE == 0)):                   
                                self.game_board[(i,j)].troops += 1
                        
                        elif cell_type == self.MadCell.CELL_TYPE_SWAMP and self.turn % SWAMP_DRAIN_RATE == 0:
                            self.game_board[(i,j)].troops -= 1

                        # check for loss of property (eg to swampland)
                        if self.game_board[(i,j)].troops < 0:
                            self.game_board[(i,j)].owner = None
                            self.game_board[(i,j)].troops = 0
                                

            # refresh the text values of each cell
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    self.game_board[(i, j)].update_display_text()


            # Reset the turn order TODO decide on logic (and syntax since apparenty i forget how to shuffle a list)
            ##self.turn_order.shuffle / shuffle() / shuffle(list)???
            self.turn_order.reverse()

        class MadCell:
            CELL_TYPE_BLANK = 0
            CELL_TYPE_ADMIRAL = 1
            CELL_TYPE_MOUNTAIN = 2
            CELL_TYPE_CITY = 3
            CELL_TYPE_SWAMP = 4

            def __init__(self, parent, row, col):
                self.parent = parent
                self.row = row
                self.col = col
                self.cell_type = self.CELL_TYPE_BLANK
                self.owner = None
                self.troops = 0 
                self.display_text = tk.StringVar()
            
            def update_display_text(self):
                str_troops = self.troops if self.troops > 0 else ''
                if self.cell_type == self.CELL_TYPE_CITY:
                    self.display_text.set(f'c{str_troops}')  
                elif self.cell_type == self.CELL_TYPE_ADMIRAL:
                    self.display_text.set(f'a{str_troops}')  
                elif self.cell_type == self.CELL_TYPE_MOUNTAIN:
                    self.display_text.set('M')
                elif self.cell_type == self.CELL_TYPE_SWAMP:
                    self.display_text.set(f's{str_troops}')

                else:
                    self.display_text.set(f'{str_troops}')  


if __name__ == '__main__':
    
    game = MadmiralsGameManager()
    game.gui.root.mainloop()

# idea: add graphics to cells sooner than late
#   - basic easily recognized images to differentiate admirals, cities, mtns, and swamps from regular cells
#   - when taking over cells from a hostile takeover, the controlling player should see a colored border around the newly acquired cells that matches the bg color of the prev owner