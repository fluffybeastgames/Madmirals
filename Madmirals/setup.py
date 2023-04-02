import os.path
from os import path

### Project modules
from db import MadDBConnection

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
    ('dark red', 'white', 'dark red'),
    ('light green', 'black', 'light green'),
    ('crimson', 'white', 'crimson',),
    ('violet', 'black', 'violet',),
    ('orange', 'black', 'orange',),
    ('yellow', 'black', 'yellow',),
    ('dark orange', 'white', 'dark orange'),
    ('purple', 'white', 'purple',),
    ('dark blue', 'white', 'dark blue'),
    ('white', 'black', 'black on white'),
    ('white', 'orange', 'orange on white'),
    ('white', 'dark grey', 'dark grey on white'),
    ('white', 'dark blue', 'dark blue on white'),
    ('white', 'crimson', 'crimson on white'),
    ('white', 'teal', 'teal on white'),
    ('white', 'purple', 'purple on white'),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', ''),
    # ('', '', '')
       
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
        db = MadDBConnection(db_path)
        db.create_new_db(default_bot_names, default_colors)

        # Describe the new user of the game
        sql_user = 'INSERT INTO user_settings(profile_desc, player_id, default_language) VALUES(?,?,?)'
        vals_user = ('Your name here', 0, 'en')
        db.run_sql(sql_user, vals_user)

        db.close()
        print('All done! Now launch madmirals.py to play!')

if __name__ == '__main__':
    
    setup_game_env()
    
        