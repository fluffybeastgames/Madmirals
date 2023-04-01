# ### MADMIRALS!!!


# game of life as opponent entity(ies) - can adjust win/lose conditions around ability to influence the preexisting algo
# spinoff idea: petri wars: spend points to decide numner of starting cells and their respective locations and traits.. then it plays out like conway's game of lie, except maybe w/ ability to place powerups to influence gameplay!
import time
import math
import random
import sqlite3
import opensimplex
import numpy as np
import tkinter as tk 
from tkinter import ttk
from functools import partial
from PIL import Image

DIR_UP = 1 
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4
DIR_NOWHERE = -1

class MadmiralsGameManager:
    GAME_TURN_SPEED = .5 # in s
    CYCLE_SPEED = 100 # ms between checks of game loop
    DEFAULT_ROWS = None # 9 - if None, then the world generation will pick one pseudo-randomly
    DEFAULT_COLS = None # 16 - if None, then the world generation will pick one pseudo-randomly

    def __init__(self):
        self.con = sqlite3.connect('..\data\mad_dev_test.db')
        self.cur = self.con.cursor()

        self.gui = self.MadmiralsGUI(self)
        #self.game = self.MadmiralsGameInstance(self)
        self.game = None
        self.debug_mode = False # if True, print more statements to console and show seed, maybe add/remove 'toggle fog of war' functionality? and so on (TBD)
        self.fog_of_war = True # whether or not to hide cells not adjacent to the player
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop

        # self.game.game_status = self.game.GAME_STATUS_READY

        self.game_loop() # start the game cycle!
    

    def create_new_replay_game(self, game_id):
        print('create_new_replay_game')

        sql = f'SELECT game_id, seed, num_rows, num_cols, num_players FROM log_games WHERE game_id={game_id}'
        self.cur.execute(sql)
        game_info = self.cur.fetchall()

        self.game = self.MadmiralsGameInstance(self, game_id=game_info[0][0], seed=game_info[0][1], num_rows=game_info[0][2], num_cols=game_info[0][3], num_players=game_info[0][4], game_mode=self.MadmiralsGameInstance.GAME_MODE_REPLAY)
        
        self.gui.populate_game_board_frame()
        self.gui.populate_scoreboard_frame()
        self.gui.populate_win_conditions_frame()
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop

        self.fog_of_war = False

        self.game.game_status = self.game.GAME_STATUS_IN_PROGRESS
    
        self.game_loop() # start the game cycle!
                    



    def create_new_game(self, num_rows=None, num_cols=None, num_players=None, seed=None, game_mode=None, game_id=None):
        print('create_new_game')

        self.game = self.MadmiralsGameInstance(self, seed=seed, num_rows=num_rows, num_cols=num_cols, game_mode=game_mode, num_players=num_players)
        
        self.gui.populate_game_board_frame()
        self.gui.populate_scoreboard_frame()
        self.gui.populate_win_conditions_frame()
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop

        self.game.game_status = self.game.GAME_STATUS_IN_PROGRESS

        self.game_loop() # start the game cycle!


    class Replay: # TODO IMPLEMENT instead of current janky setup
        def __init__(self):
            
            self.game_id = 0
            self.turn = 0
            self.data = None


    def game_loop(self):
        # print('game loop')
        if self.game is not None:
            if self.game.game_status == self.game.GAME_STATUS_IN_PROGRESS:
                now = time.time()
                # print(now - self.last_turn_timestamp)
                
                if  (now - self.last_turn_timestamp) >= self.GAME_TURN_SPEED:
                    self.last_turn_timestamp = now
                    self.game.advance_game_turn()
                            
                self.gui.render()

                # if self.game.turn > 5:
                #     self.game.game_status = self.game.GAME_STATUS_GAME_OVER_WIN
            
            else:
                self.gui.render_game_over()
            
        self.after_id = self.gui.root.after(self.CYCLE_SPEED, self.game_loop) #try again in (at least) X ms


    class MadmiralsGUI:
        MIN_FONT_SIZE = 6
        MAX_FONT_SIZE = 32
        DEFAULT_FONT_SIZE = 10

        def __init__(self, parent):
            self.root = tk.Tk()
            self.root.title('Madmirals')
            self.root.config(menu=self.create_menu_bar(self.root))
            self.parent = parent
            self.assets = self.GUI_Assets(r'C:\Users\thema\Documents\Python Scripts\Madmirals\assets\\') # TODO TEMP! 
        
            self.frame_game_board = tk.Frame(master=self.root)
            self.frame_scoreboard = tk.Frame(master=self.root)
            self.frame_win_conditions = tk.Frame(master=self.root)
            self.canvas = tk.Canvas(self.frame_scoreboard)

            self.cell_font_size = self.DEFAULT_FONT_SIZE
            self.apply_bindings()

            self.about_window = None # except while open
            self.settings_window = None # except while open
            


        def apply_bindings(self):
            # Apply keyboard
            self.root.bind('<Key>', self.key_press_handler)
            self.root.bind('<MouseWheel>', self.zoom_wheel_handler) # Windows OS support
            # self.root.bind('<Button-4>', self.zoom_wheel_handler) # Linux OS support
            # self.root.bind('<Button-5>', self.zoom_wheel_handler) # Linux OS support
            self.root.bind('<Control-Q>', self.quit_game)
            self.root.bind('<Control-q>', self.quit_game)
            self.root.bind('<Control-N>', self.open_game_settings)          # WARNING this will be reversed if caps lock is on.. look into 
            self.root.bind('<Control-n>', self.new_game)                    # bind_caps_lock = e1.bind('<Lock-KeyPress>', caps_lock_on)  
            # self.root.bind('<Control-M>', self.open_game_settings)
            # self.root.bind('<Control-m>', self.open_game_settings)
            self.root.bind('<Control-F>', self.toggle_fog_of_war)
            self.root.bind('<Control-f>', self.toggle_fog_of_war)
            self.root.bind('<Control-D>', self.toggle_debug_mode)
            self.root.bind('<Control-O>', self.open_replay_window)
            self.root.bind('<Control-o>', self.open_replay_window)

            
            

        def zoom_wheel_handler(self, event):
            # event.num for Linux, event.delta for Windows
            if event.num == 5 or event.delta == -120:
                self.zoom_out(increment=1)
            if event.num == 4 or event.delta == 120:
                self.zoom_in(increment=1)            

        def quit_game(self, event=None):
            print('test')
            self.root.destroy()
 
        def new_game(self, event=None):
            num_rows = None
            num_cols = None
            num_players = None
            seed = None 
            game_mode = self.parent.MadmiralsGameInstance.GAME_MODE_FFA

            self.parent.create_new_game(num_rows=num_rows, num_cols=num_cols, num_players=num_players, seed=seed, game_mode=game_mode)            

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
            self.parent.game.players[player_id].commando_mode = False
                
        def btn_middle_click(self, address, event):
            player_id = 0
            
            if self.parent.game.active_cell == address: # if we are middle clicking on the already active cell, toggle retreat mode
                self.parent.game.players[player_id].commando_mode = not self.parent.game.players[player_id].commando_mode
            else:
                self.parent.game.players[player_id].commando_mode = True
    
            self.parent.game.active_cell = address
            
        def btn_right_click(self, address, event):
            #print('right click = activate "move half" mode for next action')
            self.parent.game.active_cell = address
            player_id = 0 # TODO THIS NEEDS TO BE UPDATED
            self.parent.game.players[player_id].commando_mode = False
            self.parent.game.players[player_id].right_click_pending_address = address
        
        def key_press_handler(self, event):
            CHAR_ESCAPE = '\x1b'
            interesting_chars = ['W', 'w', 'A', 'a', 'S','s', 'D', 'd', 'E', 'e', CHAR_ESCAPE, '-', '=', '0']
            interesting_syms = ['Up', 'Down', 'Left', 'Right']
            player_id = 0 # TODO THIS NEEDS TO BE UPDATED
            
            if self.parent.game is not None and (event.char in interesting_chars or event.keysym in interesting_syms):
                active_cell_address = self.parent.game.active_cell
                
                if event.char == CHAR_ESCAPE:
                        if self.parent.game.active_cell:
                            self.parent.game.active_cell = None
                        else:
                            print('todo toggle pause window on ESC if nothing is selected?')
                
                elif event.char in ['-', '=', '0']: # zoom control
                    if event.char == '-':
                        self.zoom_out()
                    elif event.char == '=':
                        self.zoom_in()
                    else:
                        self.zoom_reset()


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
                    elif self.parent.game.players[player_id].commando_mode:
                        list_ship_cell_types = [self.parent.game.MadCell.CELL_TYPE_SHIP, self.parent.game.MadCell.CELL_TYPE_SHIP_2, self.parent.game.MadCell.CELL_TYPE_SHIP_3, self.parent.game.MadCell.CELL_TYPE_SHIP_4]
                        if self.parent.game.game_board[active_cell_address].cell_type in list_ship_cell_types:
                            action = self.parent.game.ACTION_MOVE_CITY # downstread we will override this when crossing admirals/cities
                        else:
                            action = self.parent.game.ACTION_MOVE_ALL # downstread we will override this when crossing admirals/cities
                    else:
                        action = self.parent.game.ACTION_MOVE_NORMAL
            
                    self.parent.game.players[player_id].player_queue.add_action_to_queue(active_cell_address, action, dir) 

                    self.parent.game.move_active_cell(dir)
                    self.parent.game.players[player_id].right_click_pending_address = None
                
                
                    

        def create_menu_bar(self, root):
            menubar = tk.Menu(root)
            
            filemenu = tk.Menu(menubar, tearoff=0)
            filemenu.add_command(label='New Game', command=self.new_game, accelerator='Ctrl+N')
            filemenu.add_command(label='Game Settings', command=self.open_game_settings, accelerator='Ctrl+Shift+N')
            filemenu.add_command(label='Open Replay', command=self.open_replay_window, accelerator='Ctrl+O')
            filemenu.add_separator()
            filemenu.add_command(label='About', command=self.open_about_window)
            filemenu.add_separator()
            filemenu.add_command(label='Exit', command=self.root.quit, accelerator='Ctrl+Q')
            
            game_menu = tk.Menu(menubar, tearoff=0)
            game_menu.add_command(label='Zoom In', command=self.zoom_in, accelerator='=')
            game_menu.add_command(label='Zoom Out', command=self.zoom_out, accelerator='-')
            game_menu.add_command(label='Reset Zoom', command=self.zoom_reset, accelerator='0')
            
            game_menu.add_command(label='Toggle Fog of War', command=self.toggle_fog_of_war, accelerator='Ctrl+F')
            game_menu.add_command(label='Toggle Debug Mode', command=self.toggle_debug_mode, accelerator='Ctrl+D')
            
            menubar.add_cascade(label='File', menu=filemenu)
            menubar.add_cascade(label='Game', menu=game_menu)

            return menubar
  
        def zoom_in(self, increment=3):
            if self.cell_font_size < self.MAX_FONT_SIZE:
                self.cell_font_size = min(self.cell_font_size+increment, self.MAX_FONT_SIZE)
                        
        def zoom_out(self, increment=3):
            if self.cell_font_size > self.MIN_FONT_SIZE:
                self.cell_font_size = max(self.cell_font_size-increment,self.MIN_FONT_SIZE)

        def zoom_reset(self):
            self.cell_font_size = self.DEFAULT_FONT_SIZE

        def toggle_fog_of_war(self, event=None):
            if self.parent.game is not None:
                print('Toggling fog of war')
                self.parent.fog_of_war = not self.parent.fog_of_war

        def toggle_debug_mode(self, event=None):
            self.parent.debug_mode = not self.parent.debug_mode
            print(f'Set debug mode to {self.parent.debug_mode}')

        def open_replay_window(self, event=None):
            print('Open replay')
            # TODO add a window w/ list of replays and other options
            game_id = 192

            self.parent.create_new_replay_game(game_id=game_id)     

        def open_game_settings(self, event=None):
            # print(self.settings_window)
            # if self.settings_window is not None:
            #     pass
            # else:
                self.settings_window = tk.Toplevel(self.root)
                # self.settings_window.geometry('500x550')
                self.settings_window.title('New Game Settings')
                lbl_header = tk.Label(self.settings_window, text= 'Game Settings', font=('Helvetica 10 bold'))
                lbl_player = tk.Label(self.settings_window, text= 'Player Name:', font=('Helvetica 10 bold'))
                lbl_bots = tk.Label(self.settings_window, text= 'Number of Bots:', font=('Helvetica 10 bold'))
                lbl_rows = tk.Label(self.settings_window, text= 'Row Count:', font=('Helvetica 10 bold'))
                lbl_cols = tk.Label(self.settings_window, text= 'Column Count:', font=('Helvetica 10 bold'))
                lbl_seed = tk.Label(self.settings_window, text= 'Game Seed:', font=('Helvetica 10 bold'))

                MIN_BOTS = 1
                MAX_BOTS = 15
                MIN_ROW_OR_COL = 4
                MAX_ROW_OR_COL = 20

                USE_DEFAULT = 0
                USE_CUST = 1

                self.settings_window.val_bots = tk.DoubleVar()
                self.settings_window.val_rows = tk.DoubleVar()
                self.settings_window.val_cols = tk.DoubleVar()
                
                def slider_changed_bots(event):
                    self.settings_window.bots_rand_or_cust.set(USE_CUST)

                def slider_changed_rows(event):
                    self.settings_window.rows_rand_or_cust.set(USE_CUST)

                def slider_changed_cols(event):
                    self.settings_window.cols_rand_or_cust.set(USE_CUST)

                self.settings_window.slider_bots = tk.Scale(
                    self.settings_window, orient='horizontal', showvalue=True,
                    variable=self.settings_window.val_bots, command=slider_changed_bots,
                    from_=MIN_BOTS, to=MAX_BOTS, troughcolor='blue', 
                    tickinterval=2, length=200, sliderlength=40
                )
                self.settings_window.slider_rows = tk.Scale(
                    self.settings_window, orient='horizontal', showvalue=True,
                    variable=self.settings_window.val_rows, command=slider_changed_rows,
                    from_=MIN_ROW_OR_COL, to=MAX_ROW_OR_COL, troughcolor='blue', 
                    tickinterval=2, length=200, sliderlength=40
                )
                self.settings_window.slider_cols = tk.Scale(
                    self.settings_window, orient='horizontal', showvalue=True,
                    variable=self.settings_window.val_cols, command=slider_changed_cols,
                    from_=MIN_ROW_OR_COL, to=MAX_ROW_OR_COL, troughcolor='blue',
                    tickinterval=2, length=200, sliderlength=40
                )                

                self.settings_window.bots_rand_or_cust = tk.IntVar()
                self.settings_window.bots_rand_or_cust.set(USE_DEFAULT) 
                self.settings_window.rand_bots = tk.Radiobutton(self.settings_window, variable=self.settings_window.bots_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_DEFAULT, text='Random')
                self.settings_window.cust_bots = tk.Radiobutton(self.settings_window, variable=self.settings_window.bots_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_CUST, text='')
                
                self.settings_window.rows_rand_or_cust = tk.IntVar()
                self.settings_window.rows_rand_or_cust.set(USE_DEFAULT)
                self.settings_window.rand_rows = tk.Radiobutton(self.settings_window, variable=self.settings_window.rows_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_DEFAULT, text='Random')
                self.settings_window.cust_rows = tk.Radiobutton(self.settings_window, variable=self.settings_window.rows_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_CUST, text='')
                
                self.settings_window.cols_rand_or_cust = tk.IntVar()
                self.settings_window.cols_rand_or_cust.set(USE_DEFAULT)
                self.settings_window.rand_cols = tk.Radiobutton(self.settings_window, variable=self.settings_window.cols_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_DEFAULT, text='Random')
                self.settings_window.cust_cols = tk.Radiobutton(self.settings_window, variable=self.settings_window.cols_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_CUST, text='')
                
                self.settings_window.new_seed = tk.StringVar()
                self.settings_window.new_seed.set(random.randint(0, 10**10)) # a random seed, same range as default 'New Game'
                self.settings_window.seed_entry = tk.Entry(self.settings_window, textvariable=self.settings_window.new_seed, width=20)

                def generate_new_seed():
                    self.settings_window.new_seed.set(random.randint(0, 10**10)) # a random seed, same range as default 'New Game'

                def generate_new_user():
                    print('TODO make new user! And also convert the user entry to a dropdown :)')

                self.settings_window.btn_generate_new_seed = tk.Button(master=self.settings_window, text='New Seed', width=14, height=1, highlightcolor='orange', command=generate_new_seed, bg='light blue')
                self.settings_window.btn_generate_new_user = tk.Button(master=self.settings_window, text='Register', width=14, height=1, highlightcolor='orange', command=generate_new_user, bg='light blue')

                self.settings_window.player_name = tk.StringVar()
                self.settings_window.player_name.set('Name') # a random seed, same range as default 'New Game'
                self.settings_window.player_name_entry = tk.Entry(self.settings_window, textvariable=self.settings_window.player_name, width=20)
                
                def okthen():
                    print('okey')
                    # Validate input; if valid, create a new instance of game with the passed params then kill this window
                
                    num_players = int((self.settings_window.val_bots.get()+1)) if self.settings_window.bots_rand_or_cust.get() == USE_CUST else None
                    num_rows = int(self.settings_window.val_rows.get()) if self.settings_window.rows_rand_or_cust.get() == USE_CUST else None
                    num_cols = int(self.settings_window.val_cols.get()) if self.settings_window.cols_rand_or_cust.get() == USE_CUST else None
                    
                    new_seed_text = self.settings_window.new_seed.get()
                    if new_seed_text.isdigit() and (int(new_seed_text)>0):
                        seed = int(new_seed_text)
                    else:
                        seed = None 

                    self.parent.create_new_game(num_rows, num_cols, num_players, seed, game_mode=self.parent.MadmiralsGameInstance.GAME_MODE_FFA_CUST)
                    
                    self.settings_window.destroy()
                    # self.settings_window = None


                def okcancel():
                    self.settings_window.destroy()
                    # self.settings_window = None
                    
                self.settings_window.btn_ok = tk.Button(master=self.settings_window, text='OK', width=14, height=3, highlightcolor='orange', command=okthen, bg='light blue')
                self.settings_window.btn_cancel = tk.Button(self.settings_window, text='Cancel', width=14, height=3, highlightcolor='orange', command=okcancel, bg='light blue')
                
                # Layout 
                lbl_header.grid(row=0, column=0, columnspan=4)
                
                lbl_player.grid(row=10, column=0)
                self.settings_window.player_name_entry.grid(row=10, column=2, columnspan=3, sticky='w')
                self.settings_window.btn_generate_new_user.grid(row=10,column=4, columnspan=2, sticky='w')
                
                lbl_bots.grid(row=30,column=0, sticky='e', padx=10)
                lbl_rows.grid(row=31,column=0, sticky='e', padx=10)
                lbl_cols.grid(row=32,column=0, sticky='e', padx=10)
                self.settings_window.rand_bots.grid(row=30,column=2, sticky='w')
                self.settings_window.rand_rows.grid(row=31,column=2, sticky='w')
                self.settings_window.rand_cols.grid(row=32,column=2, sticky='w')
                self.settings_window.cust_bots.grid(row=30,column=3, sticky='w')
                self.settings_window.cust_rows.grid(row=31,column=3, sticky='w')
                self.settings_window.cust_cols.grid(row=32,column=3, sticky='w')                        
                self.settings_window.slider_bots.grid(row=30,column=4, sticky='w', padx=10)
                self.settings_window.slider_rows.grid(row=31,column=4, sticky='w', padx=10)
                self.settings_window.slider_cols.grid(row=32,column=4, sticky='w', padx=10)
                
                lbl_seed.grid(row=40,column=0, sticky='w')
                self.settings_window.seed_entry.grid(row=40,column=2, columnspan=2, sticky='w')
                self.settings_window.btn_generate_new_seed.grid(row=40,column=4, columnspan=2, sticky='w')
                
                self.settings_window.btn_ok.grid(row=50,column=2, pady=10)
                self.settings_window.btn_cancel.grid(row=50,column=4, pady=10)
                

        def open_about_window(self):
            self.about_window = tk.Toplevel(self.root)
            # self.about_window.geometry('500x250')
            self.about_window.title('About Madmirals')
            tk.Label(self.about_window, text='Madmirals', font=('Helvetica 14 bold')).grid(row=0,column=0)
            tk.Label(self.about_window, text='A game by Matt Carleton', font=('Helvetica 12')).grid(row=1,column=0, sticky='w')

            tk.Label(self.about_window, text='How to Play', font=('Helvetica 12 bold')).grid(row=2,column=0, sticky='w')
            tk.Label(self.about_window, text='1. Starting a new game', font=('Helvetica 10 bold')).grid(row=3,column=0, sticky='w')
            tk.Label(self.about_window, text='Click New Game in the File menu (shortcut Ctrl+N) to create a new game with randomized parameters', font=('Helvetica 10')).grid(row=4,column=0, sticky='w')
            tk.Label(self.about_window, text='To customize the parameters of the game, click on Game Settings in the File menu (shortcut Ctrl+Shift+N)', font=('Helvetica 10')).grid(row=5,column=0, sticky='w')
            



        def populate_game_board_frame(self):
            if not self.frame_game_board is None: self.frame_game_board.destroy()
            # if not self.h_bar is None: self.h_bar.destroy()
            # if not self.v_bar is None: self.v_bar.destroy()
            if not self.canvas is None: self.canvas.destroy()
            
            self.frame_game_board = tk.Frame(master=self.root)
        
            self.h_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.HORIZONTAL)
            self.v_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.VERTICAL)
            self.canvas = tk.Canvas(self.frame_game_board, scrollregion=(0, 0, 600, 600), yscrollcommand=self.v_bar.set, xscrollcommand=self.h_bar.set)
            self.h_bar['command'] = self.canvas.xview
            self.v_bar['command'] = self.canvas.yview

            self.canvas.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
            self.h_bar.grid(column=0, row=1, sticky=(tk.W,tk.E))
            self.v_bar.grid(column=1, row=0, sticky=(tk.N,tk.S))
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
            
            self.frame_buttons.grid(row=0, column=0)
            self.frame_game_board.grid(row=0, column=0, columnspan=3, rowspan=4, pady=5)
            self.frame_game_board.focus_set()

        def populate_win_conditions_frame(self):
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

                self.lbls_name[i].grid(row=i + ROW_OFFSET, column=0, sticky='w')
                self.lbls_cells[i].grid(row=i + ROW_OFFSET, column=1, sticky='e')
                self.lbls_troops[i].grid(row=i + ROW_OFFSET, column=2, sticky='e')

            self.frame_scoreboard.grid(row=0, column=9, sticky='n')
        
        def render(self):  
            if self.parent.game is not None:          
                for i in range(self.parent.game.num_rows):
                    for j in range(self.parent.game.num_cols):
                        cell = self.parent.game.game_board[(i,j)]
                        uid = cell.owner
                        relief = tk.RAISED if self.parent.game.active_cell == (i,j) else tk.SUNKEN
                        cell_type = cell.cell_type
                                        
                        if self.parent.fog_of_war and cell.hidden:
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
                       

                        #font = ('Arial 18 bold') if cell_type in [self.parent.game.MadCell.CELL_TYPE_MOUNTAIN,] else ('Arial 14')  # ooh this was a fun experiment - mountains stand out more, and clusters of non-mountains look like meadows..
                        font = (f'Arial {self.cell_font_size} bold')
                        
                
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
            dict_names = {}
            dict_land = {}
            dict_troops = {}
            players = self.parent.game.players

            # Update turn count
            self.lbl_turn_count.configure(text=f'Turn {self.parent.game.turn}')
            
            score_i = 0
            for i in sorted(self.parent.game.players,key=lambda uid:self.parent.game.players[uid].troops, reverse=True):
                # print(f'Turn: {self.parent.game.turn} Key: {i}\tTroops:{self.parent.game.players[i].troops}')
                uid = players[i].user_id
                dict_names[uid] = players[i].user_desc
                dict_land[uid] = players[i].land
                dict_troops[uid] = players[i].troops

                if players[i].active:
                    bg = self.parent.game.players[uid].color_bg
                    fg = self.parent.game.players[uid].color_fg
                else:
                    bg = 'light grey'
                    fg = 'dark grey'

                self.lbls_name[score_i].configure(text=dict_names[uid], bg=bg, fg=fg)
                self.lbls_cells[score_i].configure(text=dict_land[uid], bg=bg, fg=fg)
                self.lbls_troops[score_i].configure(text=dict_troops[uid], bg=bg, fg=fg)
                score_i += 1

        def render_game_over(self): # make any visual updates to reflect that the game status is currently game over
            #print('render_game_over')
            pass


    class MadmiralsGameInstance:
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
                
        def __init__(self, parent, seed=None, num_rows=None, num_cols=None, game_mode=None, num_players=None, game_id=None):
            self.parent = parent
            self.seed = seed # the world seed used for generating the level
            self.game_id = game_id # the id of the game in table game_logs
            self.game_mode = game_mode
            self.game_status = self.GAME_STATUS_INIT
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

            if self.game_mode == self.GAME_MODE_REPLAY:
                sql = f'SELECT turn_num, row, col, cell_type, player_id, troops FROM log_game_moves WHERE game_id={self.game_id} ORDER BY turn_num, row, col'
                self.parent.cur.execute(sql)
                self.replay_data = self.parent.cur.fetchall()


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
                self.seed = random.randint(0, 10**10)

            print(f'Generating world with seed {self.seed}')

            opensimplex.seed(self.seed)
        
            if self.num_players is None:
                self.num_players = min(3 + abs(int(opensimplex.noise2(0.5, 0.5)*12)), 8)

                print(f'Num players: {self.num_players}')

            list_avail_names = self.GameEntity.get_available_bot_names(self.parent.cur)
            list_avail_colors = self.GameEntity.get_available_player_colors(self.parent.cur)

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
                self.num_rows = 4 + int(self.num_players*1.5) + abs(int(opensimplex.noise2(0.5, 0.5)*3))
                
            if self.num_cols is None:
                self.num_cols = 5 + int(self.num_players*1.5) + abs(int(opensimplex.noise2(0.5, 0.5)*4))

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

                    if target_cell.item_id < -.25:
                        target_cell.cell_type = target_cell.CELL_TYPE_MOUNTAIN
                        target_cell.troops = 25 + int(abs(target_cell.item_amt)*50)
                        
                    elif target_cell.item_id < -.15:
                        target_cell.cell_type = target_cell.CELL_TYPE_SHIP
                        target_cell.troops = 35 + int(abs(target_cell.item_amt)*25)

                    elif target_cell.item_id < -.5:
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
                target_cell.cell_type = target_cell.CELL_TYPE_ADMIRAL
                target_cell.troops = 10 # consider playing w/ starting troops
                
                # dev bonus
                if p == 0: 
                    #target_cell.troops = 255 #500
                    self.players[p].user_desc = 'Zeke'


        def add_game_to_log(self):
            # Add an entry to the database for this game
            values = (self.seed, self.num_rows, self.num_cols, self.num_players) # list of tuples
            sql = 'INSERT INTO log_games (seed, num_rows, num_cols, num_players) VALUES(?,?,?,?)'
            self.parent.cur.execute(sql, values)
            self.game_id = self.parent.cur.lastrowid
            self.parent.con.commit() 
        
        def record_starting_conditions(self):
            # Mark the starting layout as 'moves' on turn 0            
            
            list_entities = []
            for i in range(self.num_players):
                list_entities.append((self.game_id, self.players[i].user_id, self.players[i].user_desc, self.players[i].color_bg, self.players[i].color_fg ))

            sql = 'INSERT INTO log_game_entities (game_id, player_id, player_name, bg, fg) VALUES (?,?,?,?,?)'
            self.parent.cur.executemany(sql, list_entities)
            self.parent.con.commit() 

            list_changes = []
            for i in range(self.num_rows):
                for j in range(self.num_cols):
                    cell = self.game_board[(i,j)]
                    list_changes.append((self.game_id, self.turn, i, j, cell.cell_type, cell.owner, cell.troops))
            
            sql = 'INSERT INTO log_game_moves (game_id, turn_num, row, col, cell_type, player_id, troops) VALUES(?,?,?,?,?,?,?)'
            self.parent.cur.executemany(sql, list_changes)
            self.parent.con.commit() 


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

                if self.game_board[(row, col)].hidden:
                    self.active_cell = (row, col)
                else:
                    # check if we can stop the active cell from moving
                    if self.game_board[(row, col)].cell_type not in [self.MadCell.CELL_TYPE_MOUNTAIN, self.MadCell.CELL_TYPE_MOUNTAIN_CRACKED]:
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

            def get_available_player_colors(cur_local): # static class(?)
                sql = 'SELECT bg_color, fg_color FROM entity_colors ORDER BY bg_color, fg_color'
                cur_local.execute(sql)
                rows = cur_local.fetchall()
                out = []
                for row in rows:
                    out.append((row[0], row[1]))        
                
                return out
                
            def get_available_bot_names(cur_local): # static class(?)
                sql = 'SELECT bot_name FROM bot_names ORDER BY bot_name'
                cur_local.execute(sql)
                rows = cur_local.fetchall()
                out = []
                for row in rows:
                    out.append(row[0])

                return out            
            
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

            if pending_action.action==self.ACTION_MOVE_NONE: # rest move, valid if player still occupying cell
                return start_cell.owner == pending_action.user_id
            
            elif pending_action.action==self.ACTION_MOVE_CITY:

                if (
                    start_cell.cell_type in [start_cell.CELL_TYPE_SHIP, start_cell.CELL_TYPE_SHIP_2, start_cell.CELL_TYPE_SHIP_3, start_cell.CELL_TYPE_SHIP_4] and
                    target_cell.cell_type in [target_cell.CELL_TYPE_BLANK, target_cell.CELL_TYPE_SHIP, target_cell.CELL_TYPE_SHIP_2, target_cell.CELL_TYPE_SHIP_3, target_cell.CELL_TYPE_SHIP_4]
                ):  
                    print('move city!')
                    #TODO move this logic elswhere and make it work if player active celled past here quickly
                    self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), self.parent.game.ACTION_MOVE_NONE, DIR_NOWHERE)
                    self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), self.parent.game.ACTION_MOVE_NONE, DIR_NOWHERE)
                    self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), self.parent.game.ACTION_MOVE_NONE, DIR_NOWHERE)
                    self.parent.game.players[pending_action.user_id].player_queue.add_action_to_queue((target_cell.row, target_cell.col), self.parent.game.ACTION_MOVE_NONE, DIR_NOWHERE)
                    return True
                else:
                    return False 
                
            elif pending_action.action==self.ACTION_MOVE_ALL: # move all cells, leaving only 1 cell in admiral cells
                return start_cell.owner == pending_action.user_id
            
            elif pending_action.action in [self.ACTION_MOVE_NORMAL, self.ACTION_MOVE_HALF]:
                if start_cell.owner == pending_action.user_id:
                    return target_cell.cell_type not in (target_cell.CELL_TYPE_MOUNTAIN, target_cell.CELL_TYPE_MOUNTAIN_CRACKED)
            else:
                raise ValueError('Unexpected action detected')
            
            
            if start_cell.owner == pending_action.user_id and (pending_action.action==self.ACTION_MOVE_ALL or target_cell.cell_type not in (target_cell.CELL_TYPE_MOUNTAIN,target_cell.CELL_TYPE_MOUNTAIN_CRACKED)):
                return True
            else:
                return False
             
            # pending_action.action 
            # pending_action.direction
            #print(f'Action pending: {next_action.source_address} \t{next_action.action} \t{next_action.direction}')

        # GAME_STATUS_INIT = -1 # loading
        # GAME_STATUS_READY = 1 # able to start
        # GAME_STATUS_IN_PROGRESS = 2 #
        # GAME_STATUS_PAUSE = 3 #
        # GAME_STATUS_GAME_OVER_WIN = 4 # game instance is complete and can no longer be played
        # GAME_STATUS_GAME_OVER_LOSE = 5 # game instance is complete and can no longer be played

        def update_game_status(self):
            # print('update_game_status')

            # If game is
            # Check win conditions - if all met, then GAME_STATUS_GAME_OVER_WIN

            num_active = 0
            for i in range(self.num_players):
                if not self.players[i].active:
                    if self.players[i].user_id == 0: # TODO player's user id
                        self.game_status == self.GAME_STATUS_GAME_OVER_LOSE
                        break

                else:
                    num_active += 1 
           
            if num_active <= 1: # if you lost but everyone else also lost, then you win.. using FTL: Faster Than Light logic
                self.game_status == self.GAME_STATUS_GAME_OVER_WIN

            else:
                self.game_status == self.GAME_STATUS_IN_PROGRESS
                
            #tkinter.messagebox.askokcancel(title=None, message=None, **options)
        
    
        def pop_until_valid_or_empty(self, uid):               
            next_action = self.players[uid].player_queue.pop_queued_action()
            if next_action:
                if self.action_is_valid(next_action):
                    source_cell = self.game_board[next_action.source_address]
                    target_cell = self.game_board[next_action.target_address]

                    starting_troops = source_cell.troops
                    if next_action.action == self.ACTION_MOVE_NORMAL:
                        troops_to_move = starting_troops - 1
                    
                    elif next_action.action == self.ACTION_MOVE_HALF:
                        troops_to_move = math.trunc(starting_troops/2) # round down w/ truncate to make sure we never move our last troop

                    elif next_action.action == self.ACTION_MOVE_CITY:
                        troops_to_move = starting_troops
                                                
                    elif next_action.action == self.ACTION_MOVE_ALL:
                        # print(f'cell type {source_cell.cell_type} / in ({self.MadCell.CELL_TYPE_ADMIRAL} {self.MadCell.CELL_TYPE_SHIP}) ')
                        if source_cell.cell_type in (self.MadCell.CELL_TYPE_ADMIRAL, ): #, self.MadCell.CELL_TYPE_SHIP):
                            troops_to_move = starting_troops - 1
                        else:
                            troops_to_move = starting_troops
                            if troops_to_move == 0:
                                # print('renounce land (+1 troops bonus)')
                                troops_to_move += 1

                    elif next_action.action == self.ACTION_MOVE_NONE:
                        troops_to_move = 0

                    else:
                        raise ValueError('Unexpected action encountered')


                    source_cell.troops -= troops_to_move
                    source_cell.changed_this_turn = True

                    if source_cell.troops <= 0:
                        source_cell.owner = None
                        
                        if next_action.action == self.ACTION_MOVE_CITY:
                            invading_ship_count = 0
                            
                            if source_cell.cell_type == source_cell.CELL_TYPE_SHIP: invading_ship_count = 1
                            elif source_cell.cell_type == source_cell.CELL_TYPE_SHIP_2: invading_ship_count = 2
                            elif source_cell.cell_type == source_cell.CELL_TYPE_SHIP_3: invading_ship_count = 3
                            elif source_cell.cell_type == source_cell.CELL_TYPE_SHIP_4: invading_ship_count = 4
                            else: invading_ship_count = 0

                            if target_cell.cell_type == target_cell.CELL_TYPE_SHIP: invading_ship_count += 1
                            elif target_cell.cell_type == target_cell.CELL_TYPE_SHIP_2: invading_ship_count += 2
                            elif target_cell.cell_type == target_cell.CELL_TYPE_SHIP_3: invading_ship_count += 3
                            elif target_cell.cell_type == target_cell.CELL_TYPE_SHIP_4: invading_ship_count += 4
                                
                            output_type = source_cell.CELL_TYPE_SHIP

                            if invading_ship_count == 2:
                                output_type = source_cell.CELL_TYPE_SHIP_2
                            elif invading_ship_count == 3:
                                output_type = source_cell.CELL_TYPE_SHIP_3
                            elif invading_ship_count == 4:
                                output_type = source_cell.CELL_TYPE_SHIP_4
                            elif invading_ship_count > 4:
                                output_type = source_cell.CELL_TYPE_ADMIRAL

                            source_cell.cell_type = self.MadCell.CELL_TYPE_BLANK
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
                            if target_cell.cell_type in [self.MadCell.CELL_TYPE_MOUNTAIN, self.MadCell.CELL_TYPE_MOUNTAIN_CRACKED]:
                                target_cell.cell_type = self.MadCell.CELL_TYPE_MOUNTAIN_BROKEN
                                target_cell.changed_this_turn = True

                            # check if player captured target's last admiral - if so you inherit their kingdom
                            if old_owner is not None and target_cell.cell_type == self.MadCell.CELL_TYPE_ADMIRAL:
                                if self.get_admiral_count(old_owner) <= 0:
                                    print(f'Player {old_owner} defeated')
                                    self.hostile_takeover_of_player(victim=old_owner, victor=uid)
                        
                        # Mountain cracking check
                        elif target_cell.cell_type == self.MadCell.CELL_TYPE_MOUNTAIN:
                            target_cell.cell_type = self.MadCell.CELL_TYPE_MOUNTAIN_CRACKED
                            target_cell.changed_this_turn = True

                else:
                    self.pop_until_valid_or_empty(uid)
                    
        def advance_game_turn(self): # move / attack / takeover 
            self.turn += 1

            if self.game_mode == self.GAME_MODE_REPLAY:
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
                            self.game_status == self.GAME_STATUS_GAME_OVER_WIN
                            
                else:
                    self.game_status == self.GAME_STATUS_GAME_OVER_WIN



            elif self.game_mode in [self.GAME_MODE_FFA, self.GAME_MODE_FFA_CUST]: 
                
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

                            if ((cell_type == self.MadCell.CELL_TYPE_ADMIRAL and self.turn % ADMIRAL_GROW_RATE == 0) or
                                (cell_type == self.MadCell.CELL_TYPE_SHIP and self.turn % CITY_GROW_RATE == 0) or
                                (cell_type == self.MadCell.CELL_TYPE_BLANK and self.turn % BLANK_GROW_RATE == 0) or
                                (cell_type == self.MadCell.CELL_TYPE_MOUNTAIN_BROKEN and self.turn % BROKEN_MTN_GROW_RATE == 0)):                   
                                    self.game_board[(i,j)].troops += 1
                                    self.game_board[(i,j)].changed_this_turn = True
                            
                            elif cell_type == self.MadCell.CELL_TYPE_SWAMP and self.turn % SWAMP_DRAIN_RATE == 0:
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


            if self.game_mode in [self.GAME_MODE_FFA, self.GAME_MODE_FFA_CUST]: 
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
                self.parent.cur.executemany(sql, list_changes)
                self.parent.con.commit() 

                self.update_game_status()

                if self.game_status == self.GAME_STATUS_GAME_OVER_WIN:
                    tk.messagebox.askokcancel(title='GG', message='gg')
                    self.fog_of_war = False
                    
                    # Determine winner
                    active_id = None
                    num_active = 0
                    for i in range(self.num_players):
                        if self.players[i].active:
                            num_active += 1 
                            active_id = self.players[i].user_id

                    sql = f'UPDATE log_games SET game_status={self.GAME_STATUS_GAME_OVER_WIN}, winner={active_id} WHERE game_id={self.game_id}'
                    self.parent.cur.execute(sql)
                    self.parent.con.commit() 


        class MadCell:
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
            CELL_TYPE_PUP_UNKNOWN = 7 # an unopened powerup!
            CELL_TYPE_PUP_FOG_OF_WAR_LIFTED = 8 # briefly lift fog of war (seed will determine duration - with a chance of it lasting all game)
            CELL_TYPE_PUP_FAR_SIGHT = 9 # increases the distance the player can see (duration via seed)
            CELL_TYPE_PUP_GROWTH_MULTIPLIER = 10 # increases or decreases the player's spawn rates across all cell types! duration and multiplier via seed.. perhaps allow multipliers between 0 and 1 to reduce generation.. and even negative to cause troops to shrink! 
            CELL_TYPE_PUP_POISON = 11 # if ALL player cells lose, eg. 1 troop per 2 turns for 25 turns, it makes sense to use the 'shore up' functionality to reduce number of cells temporarily

            # ooh what about introducing tides!!! every 100 turns or so the tide goes in and out.. 'blank' cells get washed away during high tide (so growth rate is negative), ships aka cities don't produce troops during low tide (growth rate is 0), broken mtn growth rate affected by tides too (produce 0 at high tide, low at low tide?)
            # color would be light blue at low tide and darker blue at high tide
            # low chance of a storm coming by and wrecking random cells 

            def __init__(self, parent, row, col):
                self.parent = parent
                self.row = row
                self.col = col
                self.cell_type = self.CELL_TYPE_BLANK
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
                        if self.cell_type == self.CELL_TYPE_SHIP:
                            self.display_text.set('C')  
                        elif self.cell_type == self.CELL_TYPE_ADMIRAL:                        
                                self.display_text.set('A')  
                        elif self.cell_type in [self.CELL_TYPE_MOUNTAIN, self.CELL_TYPE_MOUNTAIN_CRACKED]:
                            self.display_text.set('M')
                        elif self.cell_type == self.CELL_TYPE_SWAMP:
                            self.display_text.set('S')
                        else:
                            self.display_text.set('')

                    elif self.cell_type in [self.CELL_TYPE_SHIP, self.CELL_TYPE_MOUNTAIN, self.CELL_TYPE_MOUNTAIN_CRACKED, self.CELL_TYPE_MOUNTAIN_BROKEN]:
                        self.display_text.set('M?')
                    else:
                        self.display_text.set('')

                else:
                    if self.cell_type == self.CELL_TYPE_SHIP:
                        self.display_text.set(f'C{str_troops}')  
                    elif self.cell_type == self.CELL_TYPE_ADMIRAL:                        
                            self.display_text.set(f'A{str_troops}')  
                    elif self.cell_type == self.CELL_TYPE_MOUNTAIN:
                        self.display_text.set('M')
                    elif self.cell_type == self.CELL_TYPE_MOUNTAIN_CRACKED:
                        self.display_text.set(f'm{str_troops}')
                    elif self.cell_type == self.CELL_TYPE_MOUNTAIN_BROKEN:
                        self.display_text.set(f'~{str_troops}')
                    elif self.cell_type == self.CELL_TYPE_SWAMP:
                        self.display_text.set(f'S{str_troops}')

                    else:
                        self.display_text.set(f'{str_troops}')  


if __name__ == '__main__':
    game = MadmiralsGameManager() # Create/load the game logic and assets and open the connection to the DB
    game.gui.root.mainloop() # run the tkinter loop
    game.con.close() # cleanup: close the db connection
    