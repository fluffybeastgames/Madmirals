import sqlite3

def create_maddata_db(con, cur):
    def create_tables(cur):
        cur.execute('CREATE TABLE log_games(game_id INTEGER NOT NULL PRIMARY KEY, seed INTEGER, num_rows INTEGER, num_cols INTEGER, num_players INTEGER, winner TEXT, game_status TEXT)') # , num_turns, winner, start_time, end_time)')
        cur.execute('CREATE TABLE log_game_moves(move_id INTEGER NOT NULL PRIMARY KEY, game_id INTEGER, turn_num INTEGER, row INTEGER, col INTEGER, cell_type INTEGER, player_id INTEGER, troops INTEGER)')
        cur.execute('CREATE TABLE log_game_entities(game_entity_id INTEGER NOT NULL PRIMARY KEY, game_id INTEGER, player_id INTEGER, player_name TEXT, bg TEXT, fg TEXT)')
        cur.execute('CREATE TABLE players(player_id INTEGER NOT NULL PRIMARY KEY, player_name TEXT, creation_date TEXT)')
        cur.execute('CREATE TABLE bot_names(bot_name_id INTEGER PRIMARY KEY, bot_name TEXT)')
        cur.execute('CREATE TABLE entity_colors(entity_color_id INTEGER NOT NULL PRIMARY KEY, bg_color TEXT, fg_color TEXT)')
        cur.execute('CREATE TABLE user_settings(user_id INTEGER NOT NULL PRIMARY KEY, profile_desc TEXT, player_id INTEGER, default_language TEXT)')

    def populate_bot_names(con, cur):
        values = [
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

        cur.executemany("INSERT INTO bot_names (bot_name) VALUES(?)", values)
        con.commit() 

    def populate_entity_colors(con, cur):
        values = [
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

        cur.executemany("INSERT INTO entity_colors (bg_color, fg_color) VALUES(?, ?)", values)
        con.commit()  # Remember to commit the transaction after executing INSERT.

    create_tables(cur)
    populate_bot_names(con, cur)
    populate_entity_colors(con, cur)

def log_game():
    print('TODO Add db entry for game')

def log_game_moves():
    print('TODO Add db entry for game')
    

if __name__ == '__main__':
    print('hey')
    con = sqlite3.connect('..\data\mad_dev_test.db')
    cur = con.cursor()
    create_maddata_db(con, cur)
    con.close()
    print('done')

    

    