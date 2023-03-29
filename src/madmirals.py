# ### MADMIRALS!!!


# game of life as opponent entity(ies) - can adjust win/lose conditions around ability to influence the preexisting algo
# spinoff idea: petri wars: spend points to decide numner of starting cells and their respective locations and traits.. then it plays out like conway's game of lie, except maybe w/ ability to place powerups to influence gameplay!
import random
import tkinter as tk 
from tkinter import * 
from tkinter import messagebox
from tkinter import ttk
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
    DEFAULT_ROWS = None # 9 - if None, then the world generation will pick one pseudo-randomly
    DEFAULT_COLS = None # 16 - if None, then the world generation will pick one pseudo-randomly

    def __init__(self):
        self.gui = self.MadmiralsGUI(self)
        self.game = self.MadmiralsGameInstance(self)
        
        self.gui.populate_game_board_frame()
        self.gui.populate_scoreboard_frame()
        self.gui.populate_win_conditions_frame()
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop

        self.game.game_status = self.game.GAME_STATUS_IN_PROGRESS

        self.game_loop() # start the game cycle!
    

    def start_or_restart_game(self, num_rows=None, num_cols=None, num_players=None, seed=None):
        print('start_or_restart_game')

        self.game = self.MadmiralsGameInstance(self, seed=seed, num_rows=num_rows, num_cols=num_cols, game_mode='normal', num_players=num_players)
        
        # #self.gui.frame_game_board.destroy()
        # self.gui.frame_game_board = self.gui.populate_game_board_frame()

        # #self.gui.frame_scoreboard.destroy()
        # self.gui.frame_scoreboard = self.gui.populate_scoreboard_frame()
        
        # #self.gui.frame_win_conditions.destroy()
        # self.gui.frame_win_conditions = self.gui.populate_win_conditions_frame()
        
        self.gui.populate_game_board_frame()
        self.gui.populate_scoreboard_frame()
        self.gui.populate_win_conditions_frame()
        # TODO also do the canvas!
        
        self.game_cell_Buttons = {}
        
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
        
            self.frame_game_board = tk.Frame(master=self.root)
            self.frame_scoreboard = tk.Frame(master=self.root)
            self.frame_win_conditions = tk.Frame(master=self.root)
            # self.h_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.HORIZONTAL)
            # self.v_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.VERTICAL)
            self.canvas = Canvas(self.frame_scoreboard)



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
            print('TODO Restart game')

            # Use all random values for now!
            num_rows = None
            num_cols = None
            num_players = None
            seed = None 

            self.parent.start_or_restart_game(num_rows, num_cols, num_players, seed)
            

        def toggle_fog_of_war(self):
            self.parent.game.fog_of_war = not self.parent.game.fog_of_war

        def toggle_debug_menu(self):
            self.debug_mode = not self.debug_mode

        
        def open_about_window(self, root):
            top= tk.Toplevel(root)
            top.geometry('500x250')
            top.title('About Madmirals')
            tk.Label(top, text= 'All About Madmirals', font=('Helvetica 14 bold')).place(x=150,y=80)

        def populate_game_board_frame(self):
            if not self.frame_game_board is None: self.frame_game_board.destroy()
            # if not self.h_bar is None: self.h_bar.destroy()
            # if not self.v_bar is None: self.v_bar.destroy()
            if not self.canvas is None: self.canvas.destroy()
            
            self.frame_game_board = tk.Frame(master=self.root)
        
            self.h_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.HORIZONTAL)
            self.v_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.VERTICAL)
            self.canvas = Canvas(self.frame_game_board, scrollregion=(0, 0, 600, 600), yscrollcommand=self.v_bar.set, xscrollcommand=self.h_bar.set)
            self.h_bar['command'] = self.canvas.xview
            self.v_bar['command'] = self.canvas.yview

            self.canvas.grid(column=0, row=0, sticky=(N,W,E,S))
            self.h_bar.grid(column=0, row=1, sticky=(W,E))
            self.v_bar.grid(column=1, row=0, sticky=(N,S))
            self.frame_game_board.grid_columnconfigure(0, weight=1)
            self.frame_game_board.grid_rowconfigure(0, weight=1)

            self.frame_buttons = tk.Frame(master=self.canvas)
            
            self.board_cell_buttons = {}

            for i in range(self.parent.game.num_rows):
                for j in range(self.parent.game.num_cols):
                    #self.board_cell_buttons[(i, j)] = tk.Button(master=self.frame_game_board, bg='light grey', textvariable=self.parent.game.game_board[(i,j)].display_text, width=8, height=4) # add cell to the dictionary and establish default behavior
                    self.board_cell_buttons[(i, j)] = tk.Button(master=self.frame_buttons, 
                        textvariable=self.parent.game.game_board[(i,j)].display_text, 
                        width=6, height=3,
                        highlightcolor='orange'                        
                        ) # add cell to the dictionary and establish default behavior
                    self.board_cell_buttons[(i, j)].grid(row=i, column=j) # place the cell in the frame

                    self.board_cell_buttons[(i, j)].bind('<Button-1>', partial(self.btn_left_click, (i,j)))
                    self.board_cell_buttons[(i, j)].bind('<Button-2>', partial(self.btn_middle_click, (i,j)))
                    self.board_cell_buttons[(i, j)].bind('<Button-3>', partial(self.btn_right_click, (i,j)))

            self.root.bind('<Key>', self.key_press_handler)
            
            self.frame_buttons.grid(row=0, column=0)
            
            #self.canvas.create_window((0,0), width=5000, height=500, window=self.frame_buttons, anchor=tk.NW)

            #self.frame_buttons.update_idletasks()

            self.frame_game_board.grid(row=0, column=0, columnspan=3, rowspan=4, pady=5)
            #self.frame_game_board.grid(row=0, column=0, pady=5)
            self.frame_game_board.focus_set()

        def populate_win_conditions_frame(self):
            print('populate_win_conditions_frame')
            if not self.frame_win_conditions is None:
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
            if not self.frame_scoreboard is None:
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
                self.lbls_name.append(tk.Label(master=self.frame_scoreboard, text=f'player {i}',  font=('Arial 16 bold')))
                self.lbls_cells.append(tk.Label(master=self.frame_scoreboard, text=f'cells {i}',  font=('Arial 16 bold')))
                self.lbls_troops.append(tk.Label(master=self.frame_scoreboard, text=f'troops {i}',  font=('Arial 16 bold')))

                self.lbls_name[i].grid(row=i + ROW_OFFSET, column=0, sticky=W)
                self.lbls_cells[i].grid(row=i + ROW_OFFSET, column=1, sticky=E)
                self.lbls_troops[i].grid(row=i + ROW_OFFSET, column=2, sticky=E)

            self.frame_scoreboard.grid(row=0, column=9, sticky='n')
        
        def render(self):            
            for i in range(self.parent.game.num_rows):
                for j in range(self.parent.game.num_cols):

                    cell = self.parent.game.game_board[(i,j)]
                    ###print(f'address | owner:\t{(i,j)}\t{cell.owner      }')
                    uid = cell.owner

                    relief = tk.RAISED if self.parent.game.active_cell == (i,j) else tk.SUNKEN
                    cell_type = cell.cell_type
                                       
                    if self.parent.game.fog_of_war and cell.hidden:
                        bg_color = 'black'
                        fg_color = 'grey'
                    else:
                        
                        if uid is None:
                            if cell_type in [cell.CELL_TYPE_MOUNTAIN, cell.CELL_TYPE_MOUNTAIN_CRACKED]:
                                bg_color = 'dark grey'
                                fg_color = 'black'
                            elif cell_type == cell.CELL_TYPE_SWAMP:
                                bg_color = 'green'
                                fg_color = 'dark grey'
                            else:
                                bg_color = 'light blue'
                                fg_color = 'dark grey'

                        else:
                            bg_color = self.parent.game.players[uid].color_bg
                            fg_color = self.parent.game.players[uid].color_fg
                            
                            # bg_color = self.parent.game.GameEntity.player_colors[uid][0]
                            # fg_color = self.parent.game.GameEntity.player_colors[uid][1]

                    

                    #font = ('Arial 18 bold') if cell_type == self.parent.game.MadCell.CELL_TYPE_MOUNTAIN else ('Arial 14')  # ooh this was a fun experiment - mountains stand out more, and clusters of non-mountains look like meadows..
                    font = ('Arial 16 bold')
                    
            
                    if False: #TODO FIX img behavior and add other images
                        img = self.assets.img_mountain if cell_type == self.parent.game.MadCell.CELL_TYPE_MOUNTAIN else None
                    else:
                        img = None


                    self.board_cell_buttons[(i, j)].config(bg=bg_color, fg=fg_color, relief=relief, image=img, font=font)

            
            self.update_score_board()

            # print('todo - if debug mode, show extra frame and update text, otherwise keep it hidden')
            #             if self.parent.debug_mode: 
            #     self.debug_label_text.set(self.get_performance_stats())
            # else:
            #     self.debug_label_text.set('')


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
                    bg = self.parent.game.players[uid].color_bg
                    fg = self.parent.game.players[uid].color_fg
                else:
                    bg = 'light grey'
                    fg = 'dark grey'


                # TODO determine sort order            
                self.lbls_name[i].configure(text=dict_names[uid], bg=bg, fg=fg)
                self.lbls_cells[i].configure(text=dict_land[uid], bg=bg, fg=fg)
                self.lbls_troops[i].configure(text=dict_troops[uid], bg=bg, fg=fg)

            if False:
                print(f'Turn {self.parent.game.turn}\tland and troops:')
                print(dict_land)
                print(dict_troops)


        def render_game_over(self): # make any visual updates to reflect that the game status is currently game over
            #print('render_game_over')
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
                

        def __init__(self, parent, seed=None, num_rows=None, num_cols=None, game_mode=None, num_players=None):
            self.parent = parent
            self.seed = seed
            self.fog_of_war = True
            
            self.game_status = self.GAME_STATUS_INIT
            self.turn = 0

            self.num_rows = num_rows # either a predefined integer value (preferably higher than 5) or None. 
            self.num_cols = num_cols #      If it's None, a pseudo-random value will be assigned in 
            self.num_players = num_players

            self.active_cell = None # cell address 

            self.players = {} # contains the player objects w/ numeric id
            self.turn_order = [] # the initial order of turns.. can be eg shuffled between turns, or assign priority keys and flip flop between whether or high or low has priority
            
            self.game_board = {}
            
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
            if self.seed is None:
                ####self.seed = 33 # TODO temp
                self.seed = random.randint(0, 10**10)

            print(f'Generating world with seed {self.seed}')

            opensimplex.seed(self.seed)
        
            if self.num_players is None:
                self.num_players = min(3 + abs(int(opensimplex.noise2(0.5, 0.5)*12)), 8)

                print(f'Num players: {self.num_players}')

            list_avail_names = self.GameEntity.get_available_bot_names()
            list_avail_colors = self.GameEntity.get_available_player_colors()
        
            for i in range(self.num_players):
                user_desc = list_avail_names.pop(self.seed*123 % len(list_avail_names))
                user_colors = list_avail_colors.pop(self.seed*33 % len(list_avail_colors))
                

                bg = user_colors[0]
                fg = user_colors[1]

                player_id = i

                bot_behavior = None
                if i > 0:    
                    if i % 4 == 0:
                        bot_behavior = self.GameEntity.BEHAVIOR_AMBUSH_PREDATOR
                    else:
                        bot_behavior = self.GameEntity.BEHAVIOR_PETRI

                self.players[i] = self.GameEntity(self, player_id, user_desc, bg, fg, bot_behavior)
                self.turn_order.append(player_id)
        
            if self.num_rows is None:
                self.num_rows = 7 + abs(int(opensimplex.noise2(0.5, 0.5)*9))
                
            if self.num_cols is None:
                self.num_cols = 10 + abs(int(opensimplex.noise2(0.5, 0.5)*6))

            print(f'Rows: {self.num_rows}\tCols: {self.num_cols}\tPlayers{self.num_players}\tSeed{self.seed}')
            
            num_params = 2 # item id; include item or not; how many of item (eg starting 'troops' on idle cities and strength of mtns)

            rng_x = np.arange(self.num_rows)
            rng_y = np.arange(self.num_cols)
            rng_z = np.arange(num_params)
            result = opensimplex.noise3array(rng_z, rng_y, rng_x)


            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    self.game_board[(i, j)] = self.MadCell(self, i, j)


            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    target_cell = self.game_board[(i, j)]
                    target_cell.item_id = result[i][j][0]
                    target_cell.item_amt = result[i][j][1]

                    if target_cell.item_id < -.5:
                        target_cell.cell_type = target_cell.CELL_TYPE_MOUNTAIN
                        target_cell.troops = 25 + int(abs(target_cell.item_amt)*50)
                        
                    elif target_cell.item_id < -.25:
                        target_cell.cell_type = target_cell.CELL_TYPE_CITY
                        target_cell.troops = 35 + int(abs(target_cell.item_amt)*25)

                    elif target_cell.item_id < -.1:
                        target_cell.cell_type = target_cell.CELL_TYPE_SWAMP
            
            
            
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
                 # determine spawn region and then pick a spot within it

                # spawn_region determines which quadrant/9th/16th of the board each player spawns in
                spawn_region = list_spawn_regions.pop(self.seed*321 % len(list_spawn_regions))

                region_map_row = int(spawn_region / math.sqrt(num_regions)) # integer division
                region_map_col = int(spawn_region % math.sqrt(num_regions))

                
                
                top_left_row = int(region_map_row * region_height)
                top_left_col = int(region_map_col * region_width)
                max_item_amt = -999
                max_item_cell = None
                
                for check_r in range(top_left_row, top_left_row+int(region_height)):
                    for check_c in range(top_left_col, top_left_col+int(region_width)):
                        #print(f'checking {check_r}x{check_c} - item_id {self.game_board[(check_r,check_c)].item_amt}')

                        if self.game_board[(check_r,check_c)].item_amt > max_item_amt:
                            max_item_amt = self.game_board[(check_r,check_c)].item_amt
                            max_item_cell = self.game_board[(check_r,check_c)]


                print(f'Player {self.players[p].user_id}\tRegion {spawn_region}\t Location is "row" {region_map_row} x "col" {region_map_col} and spawn found at {max_item_cell.row}x{max_item_cell.col}')

                target_cell = max_item_cell
                target_cell.owner = self.players[p].user_id
                target_cell.cell_type = target_cell.CELL_TYPE_ADMIRAL
                target_cell.troops = 1
                

                # dev bonus
                if p == 0: 
                    target_cell.troops = 500
                    self.players[p].user_desc = 'Zeke'
                # Checks out :)
                # Region 0 Location is "row" 0 x "col" 0
                # Region 1 Location is "row" 0 x "col" 1
                # Region 2 Location is "row" 0 x "col" 2
                # Region 3 Location is "row" 1 x "col" 0
                # Region 4 Location is "row" 1 x "col" 1
                # Region 6 Location is "row" 2 x "col" 0
                # Region 7 Location is "row" 2 x "col" 1
                # Region 8 Location is "row" 2 x "col" 2
                # test!


            print('test!')
            
            # lol fed the function to openAI and forgot to give it a prompt.. it spit out (including the comment char):
            # if spawn_points_added < self.num_players:
            #     print(f'WARNING: not enough spawn points added for all players')

            # print(f'game board {self.game_board}')
            # print(f'game board {self.game_board[(0,3)].cell_type}')
            # print(f'game board {self.game_board[(0,3)].troops}')
            # print(f'game board {self.game_board[(1,4)].cell_type}')
            # print(f'game board {self.game_board[(1,4)].


            # And then I asked it:
            # Explanation of what the code does

            # The code above is a class that generates a game world for a turn-based strategy game. It uses the OpenSimplex library to generate a random seed and then uses that seed to generate a game board with a certain number of rows and columns. It then uses the OpenSimplex library to generate a 3D array of noise values which it uses to determine what type of terrain should be placed in each cell of the game board. It also uses the noise values to determine how many troops should be placed in each cell. Finally, it places a special "Admiral" cell in each corner of the board for each player, which serves as their starting point.


        def generate_game_world_old(self):
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
            
            def get_available_player_colors():
                return [
                    ('dark red', 'white'),
                    ('light green', 'black'),
                    ('crimson', 'white'),
                    ('violet', 'black'),
                    ('orange', 'black'),
                    ('yellow', 'black'),
                    ('dark orange', 'white'),
                    ('purple', 'white'),
                    ('dark blue', 'white'),
                    ('white', 'black')
                ]
            

            def get_available_bot_names():
                return [
                    'Admiral Blunderdome', 
                    'Admiral Clumso', 
                    'Admiral Tripfoot', 
                    'Admiral Klutz', 
                    'Admiral Fumblebum', 
                    'Captain Bumblebling', 
                    'Admiral Fuming Bull', 
                    'Commodore Rage', 
                    'Commodore Clumsy', 
                    'Seadog Scatterbrain', 
                    'The Crazed Seadog', 
                    'Admiral Irritable', 
                    'Captain Crazy', 
                    'The Mad Mariner', 
                    'The Lunatic Lighthousekeeper', 
                    'The Poetic Pirate', 
                    'The Fiery Fisherman', 
                    'The Irascible Islander', 
                    'The Tempestuous Troubadour', 
                    'The Irate Inventor', 
                    'The Eccentric Explorer', 
                    'Tempestuous King Triton', 
                    'Mad Mariner', 
                    'Wrathful Wave Rider', 
                    'Vivid Voyager', 
                    'Rhyming Rover', 
                    'Bluemad Admiral Bee', 
                    'The Scarlet Steersman', 
                    'Jocular Jade Jack Tar', 
                    'Captain Kindly', 
                    'Captain Cruelty', 
                    'Commodore Limpy' 
                ]
                    

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
            #ACTION_MOVE_ALL
            
            if start_cell.owner == pending_action.user_id and (pending_action.action==self.ACTION_MOVE_ALL or target_cell.cell_type not in (target_cell.CELL_TYPE_MOUNTAIN,target_cell.CELL_TYPE_MOUNTAIN_CRACKED)):
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
                # tk.messagebox.askokcancel(title='GG', message='gg')
                self.fog_of_war = False
                self.game_status = self.GAME_STATUS_GAME_OVER
                

            ### Cycle through the players in turn_order[]. If the player's queue is not empty, pop the first element and attempt to perform it
            # Invalid moves: 
            #   - player attempts to move out of bounds or into a mountain (except when Move All-ing into a mtn), 
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
                                    # print('renounce land (+1 troops bonus)')
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
                                
                                # Mountain breaking check
                                if self.game_board[next_action.target_address].cell_type in [self.MadCell.CELL_TYPE_MOUNTAIN, self.MadCell.CELL_TYPE_MOUNTAIN_CRACKED]:
                                    self.game_board[next_action.target_address].cell_type = self.MadCell.CELL_TYPE_MOUNTAIN_BROKEN

                                # check if player captured target's last admiral - if so you inherit their kingdom
                                if old_owner is not None and self.game_board[next_action.target_address].cell_type == self.MadCell.CELL_TYPE_ADMIRAL:
                                    if self.get_admiral_count(old_owner) <= 0:
                                        print(f'Player {old_owner} defeated')
                                        self.hostile_takeover_of_player(victim=old_owner, victor=uid)
                            
                            # Mountain cracking check
                            elif self.game_board[next_action.target_address].cell_type == self.MadCell.CELL_TYPE_MOUNTAIN:
                                self.game_board[next_action.target_address].cell_type = self.MadCell.CELL_TYPE_MOUNTAIN_CRACKED

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
                    SWAMP_DRAIN_RATE = 1
                    BROKEN_MTN_GROW_RATE = 50

                    if owner is not None:

                        if ((cell_type == self.MadCell.CELL_TYPE_ADMIRAL and self.turn % ADMIRAL_GROW_RATE == 0) or
                            (cell_type == self.MadCell.CELL_TYPE_CITY and self.turn % CITY_GROW_RATE == 0) or
                            (cell_type == self.MadCell.CELL_TYPE_BLANK and self.turn % BLANK_GROW_RATE == 0) or
                            (cell_type == self.MadCell.CELL_TYPE_MOUNTAIN_BROKEN and self.turn % BROKEN_MTN_GROW_RATE == 0)):                   
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
                    cell = self.game_board[(i,j)]
                    cell.update_visibility_status(player_id=0)
                    cell.update_display_text()


            # Reset the turn order TODO decide on logic (and syntax since apparenty i forget how to shuffle a list)
            ##self.turn_order.shuffle / shuffle() / shuffle(list)???
            self.turn_order.reverse()

        class MadCell:
            CELL_TYPE_BLANK = 0
            CELL_TYPE_ADMIRAL = 1
            CELL_TYPE_MOUNTAIN = 2
            CELL_TYPE_CITY = 3
            CELL_TYPE_SWAMP = 4
            CELL_TYPE_MOUNTAIN_CRACKED = 5
            CELL_TYPE_MOUNTAIN_BROKEN = 6
            
            def __init__(self, parent, row, col):
                self.parent = parent
                self.row = row
                self.col = col
                self.cell_type = self.CELL_TYPE_BLANK
                self.owner = None # user_id of controlling entity, if any
                self.troops = 0 # the strength of this block (defense) and potential offensive strength, depending on cell type and owner
                self.hidden = True # when true, the player character should not be able to see display text or custom formatting of this cell
                self.display_text = tk.StringVar() # what information should the human player be able to glean about this cell?
                

                self.item_id = None # one of the opensimplex.noise3array values for this cell - used to determine to spawn here - may also be used to determine admiral spawn locations
                self.item_amt = None # another noise3array value - used to determine how much of an item should be here

            def update_visibility_status(self, player_id):
                if not self.parent.fog_of_war:
                    self.hidden = False
                
                elif self.owner == player_id:
                    self.hidden = False
                
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
                    
                else:
                    self.hidden = True             
            
            def update_display_text(self):
                str_troops = self.troops if self.troops > 0 else ''
                
                if self.hidden:
                    if self.cell_type in [self.CELL_TYPE_CITY, self.CELL_TYPE_MOUNTAIN, self.CELL_TYPE_MOUNTAIN_CRACKED]:
                        self.display_text.set('M')
                    else:
                        self.display_text.set('')

                else:
                    if self.cell_type == self.CELL_TYPE_CITY:
                        self.display_text.set(f'C{str_troops}')  
                    elif self.cell_type == self.CELL_TYPE_ADMIRAL:                        
                            self.display_text.set(f'A{str_troops}')  
                    elif self.cell_type == self.CELL_TYPE_MOUNTAIN:
                        self.display_text.set('M')
                    elif self.cell_type == self.CELL_TYPE_MOUNTAIN_CRACKED:
                        self.display_text.set('m')
                    elif self.cell_type == self.CELL_TYPE_MOUNTAIN_BROKEN:
                        self.display_text.set(f'~{str_troops}')
                    elif self.cell_type == self.CELL_TYPE_SWAMP:
                        self.display_text.set(f'S{str_troops}')

                    else:
                        self.display_text.set(f'{str_troops}')  


if __name__ == '__main__':
    
    game = MadmiralsGameManager()
    game.gui.root.mainloop()

# idea: add graphics to cells sooner than late
#   - basic easily recognized images to differentiate admirals, cities, mtns, and swamps from regular cells
#   - when taking over cells from a hostile takeover, the controlling player should see a colored border around the newly acquired cells that matches the bg color of the prev owner