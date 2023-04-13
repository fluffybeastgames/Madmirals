import opensimplex
import numpy as np

### Project modules
from constants import *

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
    
    def __init__(self, seed):
        self.name = 'Seedling'

if __name__ == '__main__':

    print('Testing seeds')

    test_seed = 10

    seedling_1 = Seedling(test_seed)
