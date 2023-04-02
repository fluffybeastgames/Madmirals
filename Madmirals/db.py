import sqlite3

class MadDBConnection:
    def __init__(self, db_path):
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def create_new_db(self, default_bot_names, default_colors):
        # Create the core database tables
        self.cur.execute('CREATE TABLE log_games(game_id INTEGER NOT NULL PRIMARY KEY, seed INTEGER, num_rows INTEGER, num_cols INTEGER, num_players INTEGER, winner TEXT, game_status TEXT)') # , num_turns, winner, start_time, end_time)')
        self.cur.execute('CREATE TABLE log_game_moves(move_id INTEGER NOT NULL PRIMARY KEY, game_id INTEGER, turn_num INTEGER, row INTEGER, col INTEGER, cell_type INTEGER, player_id INTEGER, troops INTEGER)')
        self.cur.execute('CREATE TABLE log_game_entities(game_entity_id INTEGER NOT NULL PRIMARY KEY, game_id INTEGER, player_id INTEGER, player_name TEXT, bg TEXT, fg TEXT)')
        self.cur.execute('CREATE TABLE players(player_id INTEGER NOT NULL PRIMARY KEY, player_name TEXT, creation_date TEXT)')
        self.cur.execute('CREATE TABLE bot_names(bot_name_id INTEGER PRIMARY KEY, bot_name TEXT)')
        self.cur.execute('CREATE TABLE entity_colors(entity_color_id INTEGER NOT NULL PRIMARY KEY, bg_color TEXT, fg_color TEXT, description TEXT)')
        self.cur.execute('CREATE TABLE user_settings(user_id INTEGER NOT NULL PRIMARY KEY, profile_desc TEXT, player_id INTEGER, default_language TEXT)')

        # Seed the bot names and color tables with a default list of options. 
        # TODO add the ability for users to customize their lists
        self.cur.executemany("INSERT INTO bot_names (bot_name) VALUES(?)", default_bot_names)
        self.cur.executemany("INSERT INTO entity_colors (bg_color, fg_color, description) VALUES(?, ?, ?)", default_colors)
        self.con.commit() 
    
    def run_sql(self, sql, vals=None, execute_many=False, commit=True):
        if execute_many:
            if vals is not None:
                self.cur.executemany(sql, vals) 
            else:
                self.cur.executemany(sql) 
        else:
            if vals is not None:
                self.cur.execute(sql, vals)
            else:
                self.cur.execute(sql)

        if commit: self.con.commit()
        return self.cur.lastrowid

    def run_sql_select(self, sql, vals=None, num_vals_selected=None): #TODO Fix the jank here
        self.cur.execute(sql)
        if num_vals_selected is None:
            return self.cur.fetchall()
        else:
            out = []
            for row in self.cur.fetchall():
                if num_vals_selected == 1: out.append(row[0])
                elif num_vals_selected == 2: out.append((row[0], row[1]))
                else: raise ValueError('THIS IS TOO JANKY FIX YOUR CODE')
        
        return out
        
    def log_game(self):
        print('TODO Add db entry for game')

    def log_game_moves(self):
        print('TODO Add db entry for game')
    
    def close(self):
        self.con.close()
