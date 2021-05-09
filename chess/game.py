import numpy as np

import constants as c

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
                y += 1
                x = 0
                continue

            if character.isdigit():
                x += int(character)
                continue

            piece = self.get_piece(character)
            state, pieces = self.add_piece(piece, state, pieces, x, y)
            x += 1
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
        return switcher.get(character, 'empty')

    @staticmethod
    def add_piece(piece, state, piece_list, x, y):
        state[x][y] = piece
        if piece != 'empty':
            piece_list[piece].add((x, y))
        return state, piece_list

    @staticmethod
    def import_castle_rights(position_string):
        castle_rights = {'white_king': False, 'white_queen': False,
                         'black_king': False, 'black_queen': False}
        for character in position_string:
            if character == 'K':
                castle_rights['white_king'] = True
            if character == 'Q':
                castle_rights['white_queen'] = True
            if character == 'k':
                castle_rights['black_king'] = True
            if character == 'q':
                castle_rights['black_queen'] = True
        return castle_rights


if __name__ == '__main__':
    game = Game()
    # print(game.game_state)
    pos = game.import_position(c.DEFAULT_POSITION)
    for element in pos:
        print(element)
    # print(WHITE_PIECES)
