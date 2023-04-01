import sqlite3
import os.path
from os import path

import mad_db

default_bot_names = [
    ('Admiral Blunderdome',), 
    ('Admiral Clumso',), 
    ('Admiral Tripfoot',), 
    ('Admiral Klutz',), 
    ('Admiral Fumblebum',), 
    ('Captain Bumblebling',), 
    ('Admiral Fuming Bull',), 
    ('Commodore Rage',), 
    ('Commodore Clumsy',), 
    ('Seadog Scatterbrain',), 
    ('The Crazed Seadog',), 
    ('Admiral Irritable',), 
    ('Captain Crazy',), 
    ('The Mad Mariner',), 
    ('The Lunatic Lighthousekeeper',), 
    ('The Poetic Pirate',), 
    ('The Fiery Fisherman',), 
    ('The Irascible Islander',), 
    ('The Tempestuous Troubadour',), 
    ('The Irate Inventor',), 
    ('The Eccentric Explorer',), 
    ('Tempestuous King Triton',), 
    ('Mad Mariner',), 
    ('Wrathful Wave Rider',), 
    ('Vivid Voyager',), 
    ('Rhyming Rover',), 
    ('Bluemad Admiral Bee',), 
    ('The Scarlet Steersman',), 
    ('Jocular Jade Jack Tar',), 
    ('Captain Kindly',), 
    ('Captain Cruelty',), 
    ('Commodore Limpy',) 
]

default_colors = [
    ('dark red', 'white'),
    ('light green', 'black'),
    ('crimson', 'white'),
    ('violet', 'black'),
    ('orange', 'black'),
    ('yellow', 'black'),
    ('dark orange', 'white'),
    ('purple', 'white'),
    ('dark blue', 'white'),
    ('white', 'black'),
    ('white', 'orange'),
    ('white', 'dark grey'),
    ('white', 'dark blue'),
    ('white', 'crimson'),
    ('white', 'teal'),
    ('white', 'purple')   
]

def setup_game_env():
    if not os.path.exists('..\\data\\'):
        print('Creating data directory')
        os.makedirs('..\\data\\')

    uid = 1
    db_path = f'..\\data\\u_{uid}.db'
    if os.path.exists(db_path):
        print(f'CANNOT CREATE - profile already exists for UID {uid}')
    
    else:
        # Create a new sqlite database and seed it with tables and default values
        db = mad_db.MadDBConnection(db_path)
        db.create_new_db(default_bot_names, default_colors)

        # Describe the new user of the game
        sql_user = 'INSERT INTO user_settings(profile_desc, player_id, default_language) VALUES(?,?,?)'
        vals_user = ('Your name here', 0, 'en')
        db.run_sql(sql_user, vals_user)

        db.close()
        print('All done! Now launch madmirals.py to play!')

if __name__ == '__main__':
    
    setup_game_env()
    
        