import opensimplex
import numpy as np
import random 
### Project modules
from constants import *
from db import MadDBConnection


class Seedling:
    
    def get_num_rows(seed):
        opensimplex.seed(seed)
        num_players = Seedling.get_num_players(seed)
        num_rows = min(MAX_ROW_OR_COL, max(MIN_ROW_OR_COL, 4 + int(num_players*1.5) + abs(int(opensimplex.noise2(1, 10)*3))))
        return num_rows

    def get_num_cols(seed):
        opensimplex.seed(seed)
        num_players = Seedling.get_num_players(seed)
        num_cols = min(MAX_ROW_OR_COL, max(MIN_ROW_OR_COL, 5 + int(num_players*1.5) + abs(int(opensimplex.noise2(-0.5, 0.5)*6))))
        return num_cols
    
    def get_num_players(seed):
        opensimplex.seed(seed)
        num_players = min(MAX_BOTS + 1, max(MIN_BOTS + 1, 3 + abs(int(opensimplex.noise2(0.123, 0.5)*12))))
        return min(3 + abs(int(opensimplex.noise2(0.5, 0.5)*12)), 10)
    
    def get_3d_noise_result(seed, x, y, z):
        opensimplex.seed(seed)
        rng_x = np.arange(x)
        rng_y = np.arange(y)
        rng_z = np.arange(z)

        return opensimplex.noise3array(rng_z, rng_y, rng_x)
    
    def get_player_colors(parent, seed, num_players):
        num_colors = 8 if num_players <= 8 else num_players
        sql_colors = f'SELECT hex FROM colors ORDER BY color_priority, hex LIMIT {num_colors} '
        list_colors = parent.parent.db.run_sql_select(sql_colors, num_vals_selected=1)
        random.seed(seed) # by setting the random seed to our seed, we can be sure we'll always recreate the same colors
        random.shuffle(list_colors)
        return list_colors[:num_players+1]

    def get_bot_names(parent, seed, num_players):
        sql_names = 'SELECT bot_name FROM bot_names ORDER BY bot_name'
        list_avail_names = parent.parent.db.run_sql_select(sql_names, num_vals_selected=1)
        random.seed(seed) # by setting the random seed to our seed, we can be sure we'll always recreate the same colors
        random.shuffle(list_avail_names)

        return list_avail_names[:num_players+1]
        
    def __init__(self, seed):
        self.name = 'Seedling'

if __name__ == '__main__':

    print('Testing seeds')

    test_seed = 10

    seedling_1 = Seedling(test_seed)
