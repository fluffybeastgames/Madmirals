import random
import tkinter as tk 
from tkinter import ttk
from functools import partial
from PIL import Image

### Project modules
from constants import *

class MadmiralsGUI:

    def __init__(self, parent):
        self.root = tk.Tk()
        self.root.title('Madmirals')
        
        self.about_window = None # self.AboutWindow(self)
        self.settings_window = None # except while open

        self.root.config(menu=self.create_menu_bar(self.root))
        self.parent = parent
        self.assets = self.GUI_Assets(r'C:\Users\thema\Documents\Python Scripts\Madmirals\assets\\') # TODO TEMP! 
    
        self.frame_game_board = tk.Frame(master=self.root)
        self.frame_scoreboard = tk.Frame(master=self.root)
        self.frame_win_conditions = tk.Frame(master=self.root)
        self.canvas = tk.Canvas(self.frame_scoreboard)

        self.cell_font_size = DEFAULT_FONT_SIZE
        self.apply_bindings()



    class AboutWindow:
        def __init__(self, parent):
            self.window = tk.Toplevel(parent.root)
            
            # self.window.geometry('500x250')
            self.window.title('About Madmirals')
            tk.Label(self.window, text='Madmirals', font=('Helvetica 14 bold')).grid(row=0,column=0)
            tk.Label(self.window, text='A game by Matt Carleton', font=('Helvetica 12')).grid(row=1,column=0, sticky='w')

            tk.Label(self.window, text='How to Play', font=('Helvetica 12 bold')).grid(row=2,column=0, sticky='w')
            tk.Label(self.window, text='1. Starting a new game', font=('Helvetica 10 bold')).grid(row=3,column=0, sticky='w')
            tk.Label(self.window, text='Click New Game in the File menu (shortcut Ctrl+N) to create a new game with randomized parameters', font=('Helvetica 10')).grid(row=4,column=0, sticky='w')
            tk.Label(self.window, text='To customize the parameters of the game, click on Game Settings in the File menu (shortcut Ctrl+Shift+N)', font=('Helvetica 10')).grid(row=5,column=0, sticky='w')
        
        def show(self):
            self.window.deiconify()

        def hide(self):
            self.window.withdraw()

    def open_about_window(self):
        #self.about_window = self.AboutWindow(self)
        if self.about_window is None: 
            self.about_window = self.AboutWindow(self)
        else:
            # self.about_window.show()
            # TODO figure out how to get the window to deiconify so we can keep it in memory
            self.about_window = self.AboutWindow(self)
            

    # class GameBoardArea:
    #     pass 

    # class Scoreboard:
    #     pass 

    # class SettingsWindow(top):
    #     pass 

    # class 

        
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
        game_mode = GAME_MODE_FFA

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
                    action = ACTION_MOVE_HALF
                elif self.parent.game.players[player_id].commando_mode:
                    list_ship_cell_types = [CELL_TYPE_SHIP, CELL_TYPE_SHIP_2, CELL_TYPE_SHIP_3, CELL_TYPE_SHIP_4]
                    if self.parent.game.game_board[active_cell_address].cell_type in list_ship_cell_types:
                        action = ACTION_MOVE_CITY # downstread we will override this when crossing admirals/cities
                    else:
                        action = ACTION_MOVE_ALL # downstread we will override this when crossing admirals/cities
                else:
                    action = ACTION_MOVE_NORMAL
        
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
        if self.cell_font_size < MAX_FONT_SIZE:
            self.cell_font_size = min(self.cell_font_size+increment, MAX_FONT_SIZE)
                    
    def zoom_out(self, increment=3):
        if self.cell_font_size > MIN_FONT_SIZE:
            self.cell_font_size = max(self.cell_font_size-increment, MIN_FONT_SIZE)

    def zoom_reset(self):
        self.cell_font_size = DEFAULT_FONT_SIZE

    def toggle_fog_of_war(self, event=None): # TODO move to game manager (or game?)
        if self.parent.game is not None:
            print('Toggling fog of war')
            self.parent.fog_of_war = not self.parent.fog_of_war

    def toggle_debug_mode(self, event=None): # TODO move to game manager
        self.parent.debug_mode = not self.parent.debug_mode
        print(f'Set debug mode to {self.parent.debug_mode}')

    def open_replay_window(self, event=None):
        # TODO use top.withdraw() and top.deiconify() to hide/show windows
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

                self.parent.create_new_game(num_rows, num_cols, num_players, seed, game_mode=GAME_MODE_FFA_CUST)
                
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
                            if cell_type in [CELL_TYPE_MOUNTAIN, CELL_TYPE_MOUNTAIN_CRACKED]:
                                bg_color = 'dark grey'
                                fg_color = 'black'
                            elif cell_type == CELL_TYPE_SWAMP:
                                bg_color = 'green'
                                fg_color = 'dark grey'
                            else:
                                bg_color = 'light blue'
                                fg_color = 'dark grey'

                        else:
                            bg_color = self.parent.game.players[uid].color_bg
                            fg_color = self.parent.game.players[uid].color_fg
                    

                    #font = ('Arial 18 bold') if cell_type in [CELL_TYPE_MOUNTAIN,] else ('Arial 14')  # ooh this was a fun experiment - mountains stand out more, and clusters of non-mountains look like meadows..
                    font = (f'Arial {self.cell_font_size} bold')
                    
            
                    if False: #TODO FIX img behavior and add other images
                        img = self.assets.img_mountain if cell_type == CELL_TYPE_MOUNTAIN else None
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

