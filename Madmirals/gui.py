import random
import tkinter as tk 
from tkinter import ttk
from tkinter import colorchooser
from functools import partial
from PIL import Image

### Project modules
from constants import *

def is_color_dark(color):
    # Expects a hex color in format #FF00FF
    r_val = int(color[1:3], base=16)
    g_val = int(color[1:3], base=16)
    b_val = int(color[1:3], base=16)
    
    # # Simpler approach Calculate brightness..
    brightness = (r_val*299 + g_val*587 + b_val*114)/1000 # these seemingly arbitrary values have been used in other functions in other languages
    # return brightness < 185 # threshold can be varied

    # more sophisticatred - calculate luminance
    r2 = r_val/255.0
    if r2 <= 0.04045: r2 =  r2/12.92
    else: r2 = ((r2+0.055)/1.055) ** 2.4

    g2 = g_val/255.0
    if g2 <= 0.04045: g2 =  g2/12.92
    else: g2 = ((g2+0.055)/1.055) ** 2.4
    
    b2 = b_val/255.0
    if b2 <= 0.04045: b2 =  b2/12.92
    else: b2 = ((b2+0.055)/1.055) ** 2.4
    
    luminance = 0.2126 * r2 + 0.7152 * g2 + 0.0722 * b2
    
    print(f'Color {color} has a brightness of {brightness} and luminance of {luminance}')
    return luminance < .179 # threshold of 179 is defined by W3C reccomendation




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
        if self.parent.game is not None and self.parent.game.game_status == GAME_STATUS_IN_PROGRESS:
            self.parent.game.game_status = GAME_STATUS_PAUSE

        self.settings_window = self.SettingsWindow(self)

    class SettingsWindow:
        def __init__(self, parent):
            self.parent = parent 
            self.top = tk.Toplevel(self.parent.root) 
            self.top.title('New Game Settings')
            self.f_gui = tk.Frame(self.top)
            self.define_layout()
            
            
        def define_layout(self):            
            lbl_header = tk.Label(self.f_gui, text='Game Settings', font=('Helvetica 10 bold'))

            #frame_player = self.get_frame_player()
            self.frame_game = tk.Frame(self.f_gui, highlightbackground='black', highlightthickness=2)
            self.frame_player = tk.Frame(self.f_gui, highlightbackground='black', highlightthickness=2)
            self.frame_params = tk.Frame(self.f_gui, highlightbackground='black', highlightthickness=2)
            self.frame_options = tk.Frame(self.f_gui, highlightbackground='black', highlightthickness=2)
            
            self.populate_frame_game()
            self.populate_frame_player()
            self.populate_frame_params()
            self.populate_frame_options()
                        
            btn_ok = tk.Button(master=self.f_gui, text='OK', width=14, height=2, command=self.apply_settings, bg='light blue')
            btn_cancel = tk.Button(self.f_gui, text='Cancel', width=14, height=2, command=self.cancel_settings, bg='light blue')

            lbl_header.grid(row=0, column=0, padx=10, pady=10)
            
            self.frame_game.grid(row=1, column=0, padx=10, pady=10, sticky='news')
            self.frame_player.grid(row=1, column=1, padx=10, pady=10, sticky='news')
            self.frame_params.grid(row=2, column=0, padx=10, pady=10, sticky='news')
            self.frame_options.grid(row=2, column=1, padx=10, pady=10, sticky='news')
            
            btn_ok.grid(row=3, column=0, pady=10, stick='e')
            btn_cancel.grid(row=3, column=1, pady=10, sticky='w')

            self.f_gui.pack()

        def populate_frame_game(self):
            f = self.frame_game

            lbl_seed = tk.Label(f, text= 'Seed', font=('Helvetica 10 bold'))
            f.new_seed = tk.StringVar()
            f.new_seed.set(random.randint(0, 10**10)) # a random seed, same range as default 'New Game'
            seed_entry = tk.Entry(f, textvariable=f.new_seed, width=12)
            btn_generate_new_seed = tk.Button(master=f, text='New Seed', width=14, height=1, highlightcolor='orange', command=self.generate_new_seed, bg='light blue')
            
            lbl_game_mode = tk.Label(f, text= 'Game Mode', font=('Helvetica 10 bold'))
            avail_game_modes = [
                'Free for All',
                'Team Battle',
                'Treasure Hunt',
                'Conway\'s Game of Sealife',
                'Friday'
            ]

            selected_game_mode = tk.StringVar()
            selected_game_mode.set('Free for all')
            dropdown_game_mode = tk.OptionMenu(f, selected_game_mode, *avail_game_modes)
            dropdown_game_mode.config(width=25)
            
            lbl_game_mode.grid(row=0,column=0, sticky='w', padx=10, pady=(5,2))
            dropdown_game_mode.grid(row=1, column=0, columnspan=2, sticky='w', padx=10, pady=(2,2))

            lbl_seed.grid(row=2,column=0, sticky='w', padx=10, pady=(5,2))
            seed_entry.grid(row=3,column=0, sticky='w', padx=10, pady=(2, 10))
            btn_generate_new_seed.grid(row=3,column=1, sticky='w', padx=(2, 10), pady=(2, 10))
            
        def generate_new_seed(self):
            self.frame_game.new_seed.set(random.randint(0, 10**10)) # a random seed, same range as default 'New Game'
            # Update the slider values of row/col/bots if they're set to random
            # Update player color if they haven't set it yet


        def populate_frame_player(self):
            f = self.frame_player # convenience variable
            self.player_name = tk.StringVar()

            if self.parent.parent.game is not None and self.parent.parent.game.player_name is not None:
                self.player_name.set(self.parent.parent.game.player_name )
            else:
                self.player_name.set('Some Square') # a random seed, same range as default 'New Game'
            
            self.player_has_set_a_custom_color = False
            self.player_color_bg = tk.StringVar()
            self.player_color_fg = tk.StringVar()
            
   

            lbl_player = tk.Label(f, text='Player', font=('Helvetica 10 bold'))
            self.player_name_entry = tk.Entry(f, textvariable=self.player_name, width=25, bg='light green', font=('Arial 16 bold'))
    
            # btn_generate_new_user = tk.Button(master=self.top, text='Register', width=14, height=1, highlightcolor='orange', command=generate_new_user, bg='light blue')
            btn_player_color = tk.Button(f, text='Select Color', width=14, height=1, bg='light blue', command=self.prompt_for_user_color)
            btn_reset_color = tk.Button(f, text='Reset Color', width=14, height=1, bg='light blue', command=self.reset_user_color)
            
            lbl_player.grid(row=0,column=0, padx=10, pady=(5,2), sticky='w')
            self.player_name_entry.grid(row=1,column=0, padx=10, pady=(2,2), sticky='w')
            btn_player_color.grid(row=1,column=1, padx=10, pady=(2,2))
            btn_reset_color.grid(row=2,column=1, padx=10, pady=(2, 10))

               
        def prompt_for_user_color(self):
            # Bring up a color picker window. If the user picks a color, check whether fg should be black or white
            # if they cancel, revert to the 'random' default for currently displayed seed
            c_code = colorchooser.askcolor()
            print(c_code)
            if c_code is not None and c_code[0] is not None:
                bg = c_code[1]
                fg = 'white' if is_color_dark(bg) else 'black'
                
                self.player_color_bg.set(bg) # we will grab this value on apply settings
                self.player_color_fg.set(fg)

                self.player_name_entry.config(bg=bg, fg=fg) #TODO HERE MOVE THIS ENTRY TO settingdwindow
                self.player_has_set_a_custom_color = True
                
                # print(is_color_dark(c_code[1]))


        def reset_user_color(self):
            # Reverts the user color to the one generated by the current seed
            #TODO

            bg = 'white'
            fg = 'dark blue'
            
            self.player_color_bg.set(bg) # we will grab this value on apply settings
            self.player_color_fg.set(fg)

            self.player_name_entry.config(bg=bg, fg=fg)
            self.player_has_set_a_custom_color = False

                # print(is_color_dark(c_code[1]))                


        def populate_frame_params(self):
            f = self.frame_params
            lbl_bots = tk.Label(f, text= 'Opponents', font=('Helvetica 10 bold'))
            lbl_rows = tk.Label(f, text= 'Game Board Height', font=('Helvetica 10 bold'))
            lbl_cols = tk.Label(f, text= 'Game Board Width', font=('Helvetica 10 bold'))
            
            f.val_bots = tk.DoubleVar()
            f.val_rows = tk.DoubleVar()
            f.val_cols = tk.DoubleVar()

            slider_bots = tk.Scale(
                f, orient='horizontal', showvalue=True,
                variable=f.val_bots, command=self.slider_changed_bots,
                from_=MIN_BOTS, to=MAX_BOTS, troughcolor='blue', 
                tickinterval=2, length=200, sliderlength=40
            )
            slider_rows = tk.Scale(
                f, orient='horizontal', showvalue=True,
                variable=f.val_rows, command=self.slider_changed_rows,
                from_=MIN_ROW_OR_COL, to=MAX_ROW_OR_COL, troughcolor='blue', 
                tickinterval=2, length=200, sliderlength=40
            )
            slider_cols = tk.Scale(
                f, orient='horizontal', showvalue=True,
                variable=f.val_cols, command=self.slider_changed_cols,
                from_=MIN_ROW_OR_COL, to=MAX_ROW_OR_COL, troughcolor='blue',
                tickinterval=2, length=200, sliderlength=40
            )              
            
            f.bots_rand_or_cust = tk.IntVar()
            f.bots_rand_or_cust.set(USE_DEFAULT) 
            rand_bots = tk.Radiobutton(f, variable=f.bots_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_DEFAULT, text='Random')
            cust_bots = tk.Radiobutton(f, variable=f.bots_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_CUST, text='')

            f.rows_rand_or_cust = tk.IntVar()
            f.rows_rand_or_cust.set(USE_DEFAULT)
            rand_rows = tk.Radiobutton(f, variable=f.rows_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_DEFAULT, text='Random')
            cust_rows = tk.Radiobutton(f, variable=f.rows_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_CUST, text='')
            
            f.cols_rand_or_cust = tk.IntVar()
            f.cols_rand_or_cust.set(USE_DEFAULT)
            rand_cols = tk.Radiobutton(f, variable=f.cols_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_DEFAULT, text='Random')
            cust_cols = tk.Radiobutton(f, variable=f.cols_rand_or_cust, justify=tk.LEFT, anchor='w', value=USE_CUST, text='')
            
            lbl_bots.grid(row=10, column=0, columnspan=2, sticky='w', padx=10, pady=(5,0))
            rand_bots.grid(row=11, column=0, sticky='w', padx=(15,5))
            cust_bots.grid(row=11, column=1, sticky='w', padx=(2,0))
            slider_bots.grid(row=11, column=2, sticky='w', padx=(0,10), pady=(20,0))

            lbl_rows.grid(row=20, column=0, columnspan=2, sticky='w', padx=10, pady=(5,0))
            rand_rows.grid(row=21, column=0, sticky='w', padx=(15,5))
            cust_rows.grid(row=21, column=1, sticky='w', padx=(2,0))
            slider_rows.grid(row=21, column=2, sticky='w', padx=(0,10), pady=(20,0))
            
            lbl_cols.grid(row=30, column=0, columnspan=2, sticky='w', padx=10, pady=(5,0))
            rand_cols.grid(row=31,column=0, sticky='w', padx=(15,5))
            cust_cols.grid(row=31, column=1, sticky='w', padx=(2,0))
            slider_cols.grid(row=31, column=2, sticky='w', padx=(0,10), pady=(20,0))
            

        def slider_changed_bots(self, event):
            self.frame_params.bots_rand_or_cust.set(USE_CUST)

        def slider_changed_rows(self, event):
            self.frame_params.rows_rand_or_cust.set(USE_CUST)

        def slider_changed_cols(self, event):
            self.frame_params.cols_rand_or_cust.set(USE_CUST)


        def populate_frame_options(self):
            f = self.frame_options
            
            print('TODO one more frame here')
            
        
        # def generate_new_user():
        #     print('TODO make new user! And also convert the user entry to a dropdown :)')
        
                
        def apply_settings(self):
            # Validate input; if valid, create a new instance of game with the passed params then kill this window

            num_players = int((self.frame_params.val_bots.get()+1)) if self.frame_params.bots_rand_or_cust.get() == USE_CUST else None
            num_rows = int(self.frame_params.val_rows.get()) if self.frame_params.rows_rand_or_cust.get() == USE_CUST else None
            num_cols = int(self.frame_params.val_cols.get()) if self.frame_params.cols_rand_or_cust.get() == USE_CUST else None
            
            player_color = (self.player_color_bg.get(), self.player_color_fg.get()) if self.player_has_set_a_custom_color else None
            player_name = self.player_name.get()
            
            new_seed_text = self.frame_game.new_seed.get()
            if new_seed_text.isdigit() and (int(new_seed_text)>0):
                seed = int(new_seed_text)
            else:
                seed = None 

            self.parent.parent.create_new_game(num_rows, num_cols, num_players, seed, game_mode=GAME_MODE_FFA_CUST, player_color=player_color, player_name=player_name)
            


            self.top.destroy()
            # self.top = None


        def cancel_settings(self):
            if self.parent.parent.game is not None and self.parent.parent.game.game_status == GAME_STATUS_PAUSE:
                self.parent.parent.game.game_status = GAME_STATUS_IN_PROGRESS

            self.top.destroy()
            # self.top = None
                    


    def populate_game_board_frame(self):
        if not self.frame_game_board is None: self.frame_game_board.destroy()
        #if not canvas is None: canvas.destroy()
        
        self.frame_game_board = tk.Frame(master=self.root, width=250, height=250)
        canvas = tk.Canvas(self.frame_game_board, width=250, height=250, scrollregion=(0, 0, 6000, 6000))
        
        hbar=tk.Scrollbar(self.frame_game_board,orient=tk.HORIZONTAL)
        hbar.grid(row=1, column=0, sticky='ew')
        hbar.config(command=canvas.xview)
        vbar=tk.Scrollbar(self.frame_game_board,orient=tk.VERTICAL)
        vbar.grid(row=0, column=1, sticky='ns')
        vbar.config(command=canvas.yview)
        canvas.config(width=250,height=250)
        canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        canvas.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))

        #TODO STILL NOT WORKING RIGHT

        # self.h_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.HORIZONTAL)
        # self.v_bar = ttk.Scrollbar(self.frame_game_board, orient=tk.VERTICAL)
        
        # canvas.config(width=250,height=250)

        #yscrollcommand=self.v_bar.set, xscrollcommand=self.h_bar.set)
                #canvas.configure(scrollregion=canvas.bbox("all"))
        # canvas.config(width=300,height=300)
        # canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        # canvas.pack(side=LEFT,expand=True,fill=BOTH)

        # canvas = Canvas(root, scrollregion=(0, 0, 1000, 1000), yscrollcommand=v.set, xscrollcommand=h.set)
        # h['command'] = canvas.xview
        # v['command'] = canvas.yview

        # canvas.grid(column=0, row=0, sticky=(tk.N,tk.W,tk.E,tk.S))
        # self.h_bar.grid(column=0, row=1, sticky=(tk.W,tk.E))
        # self.v_bar.grid(column=1, row=0, sticky=(tk.N,tk.S))
        # self.frame_game_board.grid_columnconfigure(0, weight=1)
        # self.frame_game_board.grid_rowconfigure(0, weight=1)

        self.frame_buttons = tk.Frame(master=canvas)
        
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
        self.frame_game_board.grid(row=0, column=0, columnspan=3, rowspan=4, pady=15, padx=(15, 15))
        self.frame_game_board.focus_set()

    def populate_scoreboard_frame(self):
        if not self.frame_scoreboard is None:
            self.frame_scoreboard.destroy()

        self.frame_scoreboard = tk.Frame(master=self.root, highlightbackground='black', highlightthickness=3)
        self.lbl_header = tk.Label(master=self.frame_scoreboard, text='Scoreboard', font=('Arial 22 bold'))
        self.lbl_header.grid(row=0, column=0, columnspan=3, sticky='N')

        self.lbl_turn_count = tk.Label(master=self.frame_scoreboard, text='Turn 0', font=('Arial 18 bold'))
        self.lbl_turn_count.grid(row = 1, column = 0)

        self.bg_frames = []

        self.lbls_name = []
        self.lbls_cells = []
        self.lbls_troops = []

        name_label_width = SCORE_BOARD_WIDTH_NAME_MIN
        for i in range(self.parent.game.num_players):
            if len(self.parent.game.players[i].user_desc) > name_label_width:
                name_label_width = min(len(self.parent.game.players[i].user_desc), SCORE_BOARD_WIDTH_NAME_MAX)

        # print(f'Decided on a scoreboard width of {name_label_width}')
            
        ROW_OFFSET = 2
        for i in range(self.parent.game.num_players):
            self.bg_frames.append(tk.Frame(master=self.frame_scoreboard))
            self.lbls_name.append(tk.Label(master=self.bg_frames[i], text=f'player {i}', width=name_label_width, font=('Arial 16 bold'), anchor='w'))
            self.lbls_cells.append(tk.Label(master=self.bg_frames[i], text=f'cells {i}', width=SCORE_BOARD_WIDTH_LAND, font=('Arial 16 bold'), anchor='e'))
            self.lbls_troops.append(tk.Label(master=self.bg_frames[i], text=f'troops {i}', width=SCORE_BOARD_WIDTH_TROOPS, font=('Arial 16 bold'), anchor='e'))

            self.lbls_name[i].grid_propagate(0)
            self.lbls_cells[i].grid_propagate(0)
            self.lbls_troops[i].grid_propagate(0)
            
            self.bg_frames[i].grid(row=i + ROW_OFFSET, column=0, sticky='w')
            #self. columnconfigure(1, weight=1)
            self.lbls_name[i].grid(row=0, column=0, sticky='ew')
            self.lbls_cells[i].grid(row=0, column=1, sticky='ew')
            self.lbls_troops[i].grid(row=0, column=2, sticky='ew')

        self.frame_scoreboard.grid(row=0, column=9, sticky='n', pady=(15, 0), padx=(15,15), ipady=5)
    
    def populate_win_conditions_frame(self):
        if not self.frame_win_conditions is None:
            self.frame_win_conditions.destroy()

        self.frame_win_conditions = tk.Frame(master=self.root, highlightbackground='black', highlightthickness=3)

        self.lbl_win_header = tk.Label(master=self.frame_win_conditions, text='Win Conditions', font=('Arial 22 bold'))
        self.lbl_win_desc = tk.Label(master=self.frame_win_conditions, text='Capture all Admiral cells', font=('Arial 18 bold'))
        
        self.lbl_lose_header = tk.Label(master=self.frame_win_conditions, text='Lose Conditions', font=('Arial 22 bold'))
        self.lbl_lose_desc = tk.Label(master=self.frame_win_conditions, text='Troop count reaches 0', font=('Arial 18 bold'))
        
        self.lbl_win_header.grid(row=0, column=0)
        self.lbl_win_desc.grid(row = 1, column = 0)
        self.lbl_lose_header.grid(row=2, column=0)
        self.lbl_lose_desc.grid(row = 3, column = 0)
        self.frame_win_conditions.grid(row=1, column=9, sticky='n',  pady=(0, 0), padx=(15,15))
    
    #def populate_tide_frame(self):


    def render(self):  
        tide = self.parent.game.get_tide()

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
                                if tide == TIDE_HIGH:
                                    bg_color = COLOR_TIDE_HIGH
                                    fg_color = 'white'
                                elif tide in (TIDE_COMING_IN, TIDE_GOING_OUT):
                                    bg_color = COLOR_SWAMP_MID_TIDE
                                    fg_color = 'white'                                    
                                else:
                                    bg_color = COLOR_SWAMP
                                    fg_color = 'dark grey'
                            elif cell_type == CELL_TYPE_MOUNTAIN_BROKEN and tide == COLOR_TIDE_HIGH:
                                bg_color = 'dark grey'
                                fg_color = 'black'
                            else:
                                if tide == TIDE_HIGH:
                                    bg_color = COLOR_TIDE_HIGH
                                    fg_color = 'white'
                                elif tide == TIDE_LOW:
                                    bg_color = COLOR_TIDE_LOW
                                    fg_color = 'dark grey'                                
                                elif tide in (TIDE_COMING_IN, TIDE_GOING_OUT):
                                    bg_color = COLOR_TIDE_RISING_3
                                    fg_color = 'white'

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
            
            self.bg_frames[score_i].configure(bg='green')
            self.lbls_name[score_i].configure(text=dict_names[uid], bg=bg, fg=fg)
            self.lbls_cells[score_i].configure(text=dict_land[uid], bg=bg, fg=fg)
            self.lbls_troops[score_i].configure(text=dict_troops[uid], bg=bg, fg=fg)
            
            
            score_i += 1

    def render_game_over(self): # make any visual updates to reflect that the game status is currently game over
        #print('render_game_over')
        pass

