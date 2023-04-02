

import opensimplex
import numpy as np


class Seedling:
    def __init__(self, seed):
        self.name = 'Seedling'
        self.seed = seed

    def get_num_rows(self):
        opensimplex.seed(self.seed)
        num_players = self.get_num_players()
        return 4 + int(num_players*1.5) + abs(int(opensimplex.noise2(0.5, 0.5)*3))

    def get_num_cols(self):
        opensimplex.seed(self.seed)
        num_players = self.get_num_players()
        return 5 + int(num_players*1.5) + abs(int(opensimplex.noise2(0.5, 0.5)*4))
    
    def get_num_players(self):
        opensimplex.seed(self.seed)
        return min(3 + abs(int(opensimplex.noise2(0.5, 0.5)*12)), 10)
    
    def get_3d_noise_result(self, x, y, z):
        opensimplex.seed(self.seed)
        rng_x = np.arange(x)
        rng_y = np.arange(y)
        rng_z = np.arange(z)

        return opensimplex.noise3array(rng_z, rng_y, rng_x)
    
    #def get_cell_type_at_world_gen



if __name__ == '__main__':

    print('Testing seeds')

    test_seed = 10

    seedling_1 = Seedling(test_seed)

