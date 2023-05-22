from pathlib import Path

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

default_colors = [ # color name, hex, rgb, and boolean color_preference - lower preference numbers will always be used before higher ones
    ('Red', '#C50F1F',  	    '(197, 15, 31)', 1),
    ('Dark Green', '#0a5a07',   '(10, 90, 7)', 1),
    ('Yellow', '#C19C00',   	'(193, 156, 0)', 1),
    ('Magenta', '#881798',  	'(136, 23, 152)', 1),
    ('white', '#CCCCCC',    	'(204, 204, 204)', 12),
    ('Grey', '#767676',     	'(118, 118, 118)', 10),
    ('Bright Red', '#E74856',   '(231, 72, 86)', 1),
    ('Bright Green', '#16C60C',  '(22, 198, 12)', 2),
    ('Bright Yellow', '#F9F1A5','(249, 241, 165)', 3),
    ('Bright Magenta', '#B4009E','(180, 0, 158)', 1),
    ('Bright Cyan', '#61D6D6',  '(97, 214, 214)', 12),
    ('Bright white', '#F2F2F2', '(242, 242, 242)', 12),
    ('Black', '#0C0C0C',    	'(12, 12, 12)', 9),
    ('cyan', '#3A96DD',     	'(58, 150, 221)', 14),
    ('Bright blue', '#3B78FF',  '(59, 120, 255)', 14),
    ('Blue', '#0037DA',     	'(0, 55, 218)', 14), 
]

def setup_game_env():
    data_dir = Path('../data/')
    data_dir.mkdir(exist_ok=True, parents=True)

    uid = 1
    db_path = data_dir / f'u_{uid}.db'
    if db_path.exists():
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