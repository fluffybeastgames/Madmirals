from operator import attrgetter
import time 

class AStar:
    
    def __init__(self, board=None):
        self.board = board

    def address_in_list(address, node_set):
    # Returns true if the node exists in the specified list of nodes (open or closed)
        for i in node_set:
            if i.address == address: 
                return True
            
        return False

    def update_node(new_node, node_set):
    # If more than one reference to the same cell exists in the open set, make sure to preserve the one w/ a lower g score, since it's going to result in a lower f
        for i in node_set:
            if i.address == new_node.address: 
                if new_node.g < i.g:
                    i.parent_node = new_node.parent_node
                    i.g = new_node.g
                    i.f = new_node.f # g and h values will be different but h does not rely on origin path
    
    class AStarNode:
        def __init__(self, parent, address, target_address):
            self.parent_node = parent # a previous search node, or None if this is the starting point
            self.address = address # a tuple of (row, col)        
            self.g = 0 if self.parent_node is None else self.parent_node.g + 1 # distance traveled from origin
            self.h = abs(self.address[0]-target_address[0]) + abs(self.address[1]-target_address[1]) # heuristic distance to target
            self.f = self.g + self.h # total cost
            
    class Board:
        class Cell:
            def __init__(self, row, col):
                self.row = row
                self.col = col
                self.traversable = True
                
                # if row%2==0 and col%2==0: self.traversable = False # 'random' little barriers
                # if row%3==0 and col%2==0: self.traversable = False # 'random' little barriers
                # if row%3==0 and col%3==0: self.traversable = False # 'random' little barriers
                # if row == 6 and col == 7: self.traversable = False

        def __init__(self, rows, cols):# start, target):
            self.rows = rows 
            self.cols = cols
            self.board = [[self.Cell(r, c) for c in range(self.cols)] for r in range(self.rows)]

        def print_board(self):
            out = ''
            for r in range(self.rows):
                for c in range(self.cols):
                    out += "- " if self.board[r][c].traversable else "1 "
                out += "\n"
            print(out)

    def find_path(self, start_address, target_address):
    # An implentation of an A* graph traversal program
    # Given a 2d array of Cells in a Board object, each with an address and whether or not the cell is traversable, find the shortest path to the destination
    # https://en.wikipedia.org/wiki/A*_search_algorithm
    # If a path exists, returns a list of address tuples. If no path exists, returns None

        open_set = []
        closed_set = []

        start_node = self.AStarNode(parent=None, address=start_address, target_address=target_address)
        open_set.append(start_node)
        
        target_found = False 
        while len(open_set) > 0 and not target_found:
            open_set = sorted(open_set, key=lambda x: x.f) # sort the open nodes by their F value, ascending, in order to optimize search/final path
        
            current_square = open_set.pop(0)
            closed_set.append(current_square)
        
            if current_square.address == target_address:
                #print('We found it!')
                target_found = True
                
            else:
                if current_square.address[0] > 0 and self.board.board[current_square.address[0] - 1][current_square.address[1]].traversable: # check above
                    new_node = self.AStarNode(parent=current_square, address=(current_square.address[0] - 1, current_square.address[1]), target_address=target_address)
                    
                    if not AStar.address_in_list(new_node.address, closed_set):
                        if AStar.address_in_list(new_node.address, open_set): 
                            AStar.update_node(new_node, open_set)
                            open_set = sorted(open_set, key=lambda x: x.f) # resort the value, in case the update affected F scores
                        else:
                            open_set.append(new_node)
                
                if current_square.address[0] < self.board.rows - 1 and self.board.board[current_square.address[0] + 1][current_square.address[1]].traversable: # check below
                    new_node = self.AStarNode(parent=current_square, address=(current_square.address[0] + 1, current_square.address[1]), target_address=target_address)
                    if not AStar.address_in_list(new_node.address, closed_set):
                        if AStar.address_in_list(new_node.address, open_set): 
                            AStar.update_node(new_node, open_set)
                            open_set = sorted(open_set, key=lambda x: x.f) # resort the value, in case the update affected F scores
                        else:
                            open_set.append(new_node)

                if current_square.address[1] > 0 and self.board.board[current_square.address[0]][current_square.address[1] - 1].traversable: # check left
                    new_node = self.AStarNode(parent=current_square, address=(current_square.address[0], current_square.address[1] - 1), target_address=target_address)
                    if not AStar.address_in_list(new_node.address, closed_set):
                        if AStar.address_in_list(new_node.address, open_set): 
                            AStar.update_node(new_node, open_set)
                            open_set = sorted(open_set, key=lambda x: x.f) # resort the value, in case the update affected F scores
                        else:
                            open_set.append(new_node)


                if current_square.address[1] < self.board.cols - 1 and self.board.board[current_square.address[0]][current_square.address[1] + 1].traversable: # check right
                    new_node = self.AStarNode(parent=current_square, address=(current_square.address[0], current_square.address[1] + 1), target_address=target_address)
                    if not AStar.address_in_list(new_node.address, closed_set):
                        if AStar.address_in_list(new_node.address, open_set): 
                            AStar.update_node(new_node, open_set)
                            open_set = sorted(open_set, key=lambda x: x.f) # resort the value, in case the update affected F scores
                        else:
                            open_set.append(new_node)

                # print(f'Checked square {current_square.address}\tf={current_square.f}\tg={current_square.g}\th={current_square.h}\ttarget: {target_address}')
        
        if target_found:
            final_path = []
            path_node = current_square
            while(path_node is not None):
                final_path.append(path_node.address)
                path_node = path_node.parent_node
                
            final_path.reverse()
            # print(final_path)
            return final_path
        else:
            print(f'Failed to find a match. Final len of open_set: {len(open_set)}\tclosed_set:{len(closed_set)}')
            return None # we never found a path
            
if __name__ == '__main__':
    a_star = AStar()
    a_star.board = a_star.Board(30,99)
    a_star.board.print_board()
    
    start_address = (28,1)
    target_address = (29, 98)

    t1 =  time.time()
    a_star_path = a_star.find_path(start_address, target_address)
    print(a_star_path)
    print(f'Time elapsed: {time.time() - t1}')


