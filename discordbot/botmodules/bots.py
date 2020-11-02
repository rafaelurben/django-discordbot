from rich import print
from tqdm import tqdm

class VierGewinntBot():
    # Constants
    
    ## Ratings [Sequence], (Points for P1, P2)

    RATING = [
        ([1, 1, 1, 1],      ( 100000000000, -100000000000)),
        ([2, 2, 2, 2],      (-100000000000,  100000000000)), 
        ([0, 1, 1, 1, 0],   ( 1000,         -1000000)),
        ([0, 2, 2, 2, 0],   (-1000000,       1000)), 
        ([0, 1, 1, 1],      ( 100,          -1000000)), 
        ([0, 2, 2, 2],      (-1000000,       100)), 
        ([1, 1, 1, 0],      ( 100,          -1000000)),
        ([2, 2, 2, 0],      (-1000000,       100)),
        ([1, 0, 1, 1],      ( 100,          -1000000)), 
        ([2, 0, 2, 2],      (-1000000,       100)), 
        ([1, 1, 0, 1],      ( 100,          -1000000)), 
        ([2, 2, 0, 2],      (-1000000,       100)), 
        ([0, 1, 1, 0],      ( 10,           -10)), 
        ([0, 2, 2, 0],      (-10,            10)), 
        ([0, 1, 0],         ( 1,            -1)),
        ([0, 2, 0],         (-1,             1)),
    ]

    FINISHED_CRITERIUM = [
        [1, 1, 1, 1],
        [2, 2, 2, 2],
    ]

    # Utils

    @classmethod
    def copyboard(self, board):
        return [l.copy() for l in board]

    @classmethod
    def seq_in_list(self, sequence, listtotest):
        if len(sequence) <= len(listtotest):
            return ', '.join(map(str, sequence)) in ', '.join(map(str, listtotest))
        else:
            return False

    @classmethod
    def get_lines(self, board):
        width, height = len(board[0]), len(board)

        # Horizontal lines
        lines = self.copyboard(board)

        # Vertical lines
        lines += [[board[h][w] for h in range(height)] for w in range(width)]

        # Diagonal lines
        w = 0
        h = height-1
        while w < width:
            dia = []
            _w, _h = w, h

            while _w < width and _h < height:
                dia.append(board[_h][_w])
                _w += 1
                _h += 1

            lines.append(dia)
            if h > 0:
                h -= 1
            else:
                w += 1
        w = 0
        h = 0
        while w < width:
            dia = []
            _w, _h = w, h

            while _w < width and _h >= 0:
                dia.append(board[_h][_w])
                _w += 1
                _h -= 1

            lines.append(dia)
            if h < height-1:
                h += 1
            else:
                w += 1
        return lines

    @classmethod
    def get_rating(self, board, playernr):
        lines = self.get_lines(board)
        score = 0
        for sequence, points in self.RATING:
            for line in lines:
                if self.seq_in_list(sequence, line):
                    if playernr == 1:
                        score += points[0]
                    elif playernr == 2:
                        score += points[1]
        return score

    @classmethod
    def is_finished(self, board):
        lines = self.get_lines(board)
        for seq in self.FINISHED_CRITERIUM:
            for line in lines:
                if self.seq_in_list(seq, line):
                    return True
        return False

    # Preview move

    @classmethod
    def get_move_preview(self, board, position, playernr):
        board = self.copyboard(board)
        for i in range(len(board)-1, -1, -1):
            if board[i][position] == 0:
                board[i][position] = playernr
                return board

    # Recursive

    @classmethod
    def _get_best_move(self, board, playernr=2, level=0, alpha=-100000000000, beta=100000000000, botnr=2, maxdepth=2):
        scores = []
        for i in range(len(board[0])):
            if board[0][i] == 0:
                if level < maxdepth:
                    if not self.is_finished(board):
                        otherplayer = 2 if playernr == 1 else 1

                        score = self._get_best_move(
                            self.get_move_preview(board, i, playernr), 
                            playernr=otherplayer, 
                            level=level+1, 
                            alpha=alpha, 
                            beta=beta, 
                            botnr=botnr, 
                            maxdepth=maxdepth
                        )

                        scores.append(score)

                        alpha = max(alpha, self.get_rating(board, otherplayer))
                        if beta <= alpha:
                            break
                    else:
                        return self.get_rating(board, botnr)
                else:
                    return self.get_rating(board, botnr)
            else:
                return self.get_rating(board, botnr)

        if playernr == botnr:
            return max(scores)
        else:
            return min(scores)

    # Main

    @classmethod
    def get_best_move(self, board, botnr=2, maxdepth=3):
        scores = []
        for i in tqdm(range(len(board[0])), desc="[VierGewinntBot]"):
            if board[0][i] == 0:
                otherplayer = 2 if botnr == 1 else 1

                score = self._get_best_move(
                    self.get_move_preview(board, i, botnr), 
                    playernr=otherplayer, 
                    level=1, 
                    alpha=-100000000000, 
                    beta=100000000000, 
                    botnr=botnr, 
                    maxdepth=maxdepth
                )

                scores.append(score)
            else:
                scores.append(-100000000000)

        bestmove = scores.index(max(scores))

        print(f"[VierGewinntBot] - Result ({ bestmove }):", scores)
        return bestmove
