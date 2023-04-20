# ### MADMIRALS!!!
import time
import sqlite3

### Project modules
from constants import *
from gam_inst import MadmiralsGameInstance
from gui import MadmiralsGUI
from db import MadDBConnection
import setup # todo - use in app.. for when no DB detected but also for adding new user profiles
from image_data import * 


class MadmiralsGameManager:
    GAME_TURN_SPEED = .5 # in s
    CYCLE_SPEED = 20 # ms between checks of game loop

    def __init__(self):
        self.db = MadDBConnection('..\data\mad_dev_test.db')
        # self.con = sqlite3.connect()
        # self.cur = self.con.cursor()
        self.images = ImageData()
        self.gui = MadmiralsGUI(self)
        self.game = MadmiralsGameInstance(self)
        #self.game = None
        self.debug_mode = False # if True, print more statements to console and show seed, maybe add/remove 'toggle fog of war' functionality? and so on (TBD)
        self.fog_of_war = True # whether or not to hide cells not adjacent to the player
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop
        self.game_settings_changed_this_turn = True 
        # self.game.game_status = GAME_STATUS_READY

        self.game_loop() # start the game cycle!

    

    def create_new_replay_game(self, game_id, debug=True):
        print('create_new_replay_game')

        sql = f'SELECT game_id, seed, num_rows, num_cols, num_players FROM log_games WHERE game_id={game_id}'
        game_info = self.db.run_sql_select(sql)
        self.debug_mode = debug
      
        self.game = MadmiralsGameInstance(self, game_id=game_info[0][0], seed=game_info[0][1], num_rows=game_info[0][2], num_cols=game_info[0][3], num_players=game_info[0][4], game_mode=GAME_MODE_REPLAY)
        
        self.gui.populate_game_board_frame()
        self.gui.populate_scoreboard_frame()
        self.gui.populate_tide_frame()
        self.gui.populate_win_conditions_frame()
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop

        self.fog_of_war = False

        self.game.game_status = GAME_STATUS_IN_PROGRESS
    
        self.game_loop() # start the game cycle!


    def create_new_game(self, num_rows=None, num_cols=None, num_players=None, seed=None, game_mode=None, game_id=None, player_color=None, player_name=None, fog=True, debug=False):
        print('create_new_game')
        
        self.debug_mode = debug
        self.game = MadmiralsGameInstance(self, seed=seed, num_rows=num_rows, num_cols=num_cols, game_mode=game_mode, num_players=num_players, player_color=player_color, player_name=player_name, fog=fog)
        
        self.gui.prep_new_game()
        
        self.last_turn_timestamp = time.time()
        self.after_id = None # for repeating the game loop

        self.game.game_status = GAME_STATUS_IN_PROGRESS
        self.game_settings_changed_this_turn = True 
        self.gui.render()

        self.game_loop() # start the game cycle!

    class Replay: # TODO IMPLEMENT instead of current janky setup
        def __init__(self):
            
            self.game_id = 0
            self.turn = 0
            self.data = None


    def game_loop(self):
        # print('game loop')
        if self.game is not None:
            if self.game.game_status == GAME_STATUS_IN_PROGRESS:
                now = time.time()
                # print(now - self.last_turn_timestamp)
                
                if  (now - self.last_turn_timestamp) >= self.GAME_TURN_SPEED:
                    self.last_turn_timestamp = now
                    self.game.tick()
                            
                self.gui.render()
                self.game_settings_changed_this_turn = False # eg zoom, end of game, change of tide.. if so, we will render everything

            elif self.game.game_status == GAME_STATUS_PAUSE:
                self.gui.render()
                pass
            elif self.game.game_status in (GAME_STATUS_GAME_OVER_WIN, GAME_STATUS_GAME_OVER_LOSE):
                self.gui.render_game_over()
            else:
                pass
            
        self.after_id = self.gui.root.after(self.CYCLE_SPEED, self.game_loop) #try again in (at least) X ms


if __name__ == '__main__':
    game = MadmiralsGameManager() # Create/load the game logic and assets and open the connection to the DB
    game.gui.root.mainloop() # run the tkinter loop
    game.db.close() # cleanup: close the db connection
    