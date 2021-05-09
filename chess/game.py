# import numpy as np

from chess import constants as c

WHITE_PIECES = ['white_pawn', 'white_knight', 'white_bishop', 'white_rook', 'white_queen', 'white_king']
BLACK_PIECES = ['black_pawn', 'black_knight', 'black_bishop', 'black_rook', 'black_queen', 'black_king']


class Game:
    def __init__(self):
        self.game_state, self.pieces, self.player, self.castle_rights, self.en_passant \
            = self.import_position(c.DEFAULT_POSITION)

    """Importing of a position"""

    def import_position(self, position_string):
        position_string = position_string.split(' ')

        state, pieces = self.import_board_position(position_string[0])
        player = 'white' if position_string[1] == 'w' else 'black'
        castle_rights = self.import_castle_rights(position_string[2])
        en_passant = None if position_string[3] == '-' else position_string[3]

        return state, pieces, player, castle_rights, en_passant

    def import_board_position(self, position_string):
        state = [['empty' for _ in range(c.COLUMNS)] for _ in range(c.ROWS)]
        pieces = {piece: set() for piece in WHITE_PIECES + BLACK_PIECES}
        x, y = 0, 0
        for character in position_string:
            if character == '/':
                if x < c.COLUMNS:
                    raise ValueError('Position not valid: Board string too short!')
                if x > c.COLUMNS:
                    raise ValueError('Position not valid: Board string too long!')
                y += 1
                x = 0
                continue

            if x > c.COLUMNS - 1 or y > c.ROWS - 1:
                raise ValueError('Position not valid: Board string too long!')

            if character.isdigit():
                x += int(character)
                continue

            piece = self.get_piece(character)
            state, pieces = self.add_piece(piece, state, pieces, x, y)
            x += 1

        if x < c.COLUMNS - 1 or y < c.ROWS - 1:
            raise ValueError('Position not valid: Board string too short!')
        return state, pieces

    @staticmethod
    def get_piece(character):
        switcher = {
            'p': 'black_pawn',
            'P': 'white_pawn',
            'n': 'black_knight',
            'N': 'white_knight',
            'b': 'black_bishop',
            'B': 'white_bishop',
            'r': 'black_rook',
            'R': 'white_rook',
            'q': 'black_queen',
            'Q': 'white_queen',
            'k': 'black_king',
            'K': 'white_king'
        }
        return switcher.get(character)

    @staticmethod
    def add_piece(piece, state, piece_list, x, y):
        state[x][y] = piece
        if piece != 'empty':
            piece_list[piece].add((x, y))
        return state, piece_list

    @staticmethod
    def import_castle_rights(position_string):
        castle_rights = {'white_king_side': False, 'white_queen_side': False,
                         'black_king_side': False, 'black_queen_side': False}
        for character in position_string:
            if character == 'K':
                castle_rights['white_king_side'] = True
            if character == 'Q':
                castle_rights['white_queen_side'] = True
            if character == 'k':
                castle_rights['black_king_side'] = True
            if character == 'q':
                castle_rights['black_queen_side'] = True
        return castle_rights

    def set_position(self, position):
        try:
            self.game_state, self.pieces, self.player, self.castle_rights, self.en_passant \
                = self.import_position(position)
        except ValueError as E:
            print(f'Error: {E}')


if __name__ == '__main__':
    game = Game()
    # print(game.game_state)
    game.set_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    print(game.game_state)
    # print(WHITE_PIECES)
