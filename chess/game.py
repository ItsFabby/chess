import numpy as np
import copy

from chess import constants as c


class Game:
    def __init__(self, position=c.DEFAULT_POSITION):
        self.state, self.pieces, self.player, self.castle_rights, self.en_passant \
            = self.import_position(position)

    """Importing of a position"""

    def import_position(self, position_string):
        position_string = position_string.split(' ')

        state, pieces = self.import_board_position(position_string[0])
        player = 'white' if position_string[1] == 'w' else 'black'
        castle_rights = self.import_castle_rights(position_string[2])
        # broken
        en_passant = None  # if position_string[3] == '-' else position_string[3]

        return state, pieces, player, castle_rights, en_passant

    def import_board_position(self, position_string):
        state = [['empty' for _ in range(c.ROWS)] for _ in range(c.COLUMNS)]
        pieces = {piece: set() for piece in c.WHITE_PIECES + c.BLACK_PIECES}
        column, row = 0, 0
        for character in position_string:
            if character == '/':
                if column < c.COLUMNS:
                    raise ValueError('Position not valid: Board string too short!')
                if column > c.COLUMNS:
                    raise ValueError('Position not valid: Board string too long!')
                row += 1
                column = 0
                continue

            if column > c.COLUMNS - 1 or row > c.ROWS - 1:
                raise ValueError('Position not valid: Board string too long!')

            if character.isdigit():
                column += int(character)
                continue

            piece = self.get_piece(character)
            state, pieces = self.add_piece(piece, state, pieces, row, column)
            column += 1

        if column < c.COLUMNS - 1 or row < c.ROWS - 1:
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
    def add_piece(piece, state, piece_list, row, column):
        if state[row][column] != 'empty':
            raise ValueError('Target square not empty!')
        if piece not in c.WHITE_PIECES + c.BLACK_PIECES:
            raise NameError('Input piece not valid!')
        state[row][column] = piece
        piece_list[piece].add((row, column))
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
            self.state, self.pieces, self.player, self.castle_rights, self.en_passant \
                = self.import_position(position)
        except ValueError as E:
            print(f'Error: {E}')

    """Updating of position"""

    # executes a move and updates the class attributes
    def make_move(self, origin_pos, target_pos):
        self.state, self.pieces, self.castle_rights, self.en_passant \
            = self.move(self.state, self.pieces, self.castle_rights, origin_pos, target_pos)
        self.player = self.swap_player(self.player)

    # this implementation allows taking of own pieces and does not check if move is legal
    def move(self, state, pieces, castle_rights, origin_pos, target_pos):
        if not self.on_board(origin_pos):
            raise ValueError('Origin position not on board!')
        if not self.on_board(target_pos):
            raise ValueError('Target position not on board!')
        if origin_pos == target_pos:
            raise ValueError('Origin and target position cannot be equal!')
        if state[origin_pos[0]][origin_pos[1]] == 'empty':
            raise ValueError('Origin position is empty!')

        state = copy.deepcopy(state)
        pieces = copy.deepcopy(pieces)
        castle_rights = copy.deepcopy(castle_rights)

        origin_piece = state[origin_pos[0]][origin_pos[1]]
        target_piece = state[target_pos[0]][target_pos[1]]

        self.apply_en_passant(state, pieces, origin_pos, target_pos)
        state, pieces, castle_rights, _ = self.apply_castling(state, pieces, castle_rights, origin_pos, target_pos)

        state[origin_pos[0]][origin_pos[1]] = 'empty'
        pieces[origin_piece].remove(origin_pos)

        state[target_pos[0]][target_pos[1]] = origin_piece
        pieces[origin_piece].add(target_pos)

        if target_piece != 'empty':
            pieces[target_piece].remove(target_pos)

        castle_rights = self.update_castle_rights(castle_rights, origin_piece, origin_pos, target_pos)
        en_passant = self.update_en_passant(origin_piece, origin_pos, target_pos)

        return state, pieces, castle_rights, en_passant

    def apply_castling(self, state, pieces, castle_rights, origin_pos, target_pos):
        if not self.detect_castling(state, origin_pos, target_pos):
            return state, pieces, castle_rights, None
        rook_row = origin_pos[0]
        rook_origin_column = 0 if target_pos[1] == 2 else 7
        rook_target_column = 3 if target_pos[1] == 2 else 5
        if self.state_entry(state, (rook_row, rook_origin_column)) == 'empty':
            return state, pieces, castle_rights, None
        return self.move(state, pieces, castle_rights, (rook_row, rook_origin_column), (rook_row, rook_target_column))

    def detect_castling(self, state, origin_pos, target_pos):
        piece = self.state_entry(state, origin_pos)
        if piece not in ('white_king', 'black_king'):
            return False
        if abs(origin_pos[1] - target_pos[1]) == 2:
            return True
        return False

    def apply_en_passant(self, state, pieces, origin_pos, target_pos):
        if not self.detect_en_passant(state, origin_pos, target_pos):
            return
        square_to_remove = (origin_pos[0], target_pos[1])
        piece_to_remove = self.state_entry(state, square_to_remove)
        state[square_to_remove[0]][square_to_remove[1]] = 'empty'
        pieces[piece_to_remove].remove(square_to_remove)
        return

    def detect_en_passant(self, state, origin_pos, target_pos):
        piece = self.state_entry(state, origin_pos)
        if piece not in ('white_pawn', 'black_pawn'):
            return False
        target_piece = self.state_entry(state, target_pos)
        if target_piece == 'empty':
            if abs(origin_pos[0] - target_pos[0]) == 1 and abs(origin_pos[1] - target_pos[1]) == 1:
                return True
        return False

    @staticmethod
    def update_en_passant(origin_piece, origin_pos, target_pos):
        en_passant = None
        if origin_piece in ('white_pawn', 'black_pawn'):
            if origin_pos[0] - target_pos[0] in (-2, 2):
                en_passant = target_pos
        return en_passant

    @staticmethod
    def update_castle_rights(castle_rights, origin_piece, origin_pos, target_pos):
        if origin_piece == 'white_king':
            castle_rights['white_king_side'] = False
            castle_rights['white_queen_side'] = False
        if origin_piece == 'black_king':
            castle_rights['black_king_side'] = False
            castle_rights['black_queen_side'] = False

        if (0, 0) in (origin_pos, target_pos):
            castle_rights['black_queen_side'] = False
        if (0, 7) in (origin_pos, target_pos):
            castle_rights['black_king_side'] = False
        if (7, 0) in (origin_pos, target_pos):
            castle_rights['white_queen_side'] = False
        if (7, 7) in (origin_pos, target_pos):
            castle_rights['white_king_side'] = False

        return castle_rights

    @staticmethod
    def on_board(position):
        return 0 <= position[0] < c.ROWS and 0 <= position[1] < c.COLUMNS

    @staticmethod
    def swap_player(player):
        return 'black' if player == 'white' else 'white'

    """Get legal moves"""

    def game_legal_moves(self):
        return self.get_legal_moves(self.player, self.state, self.pieces, self.en_passant, self.castle_rights)

    def get_legal_moves(self, player, state, pieces, en_passant, castle_rights):
        moves = self.get_pseudolegal_moves(player, state, pieces, en_passant, castle_rights)
        legal_moves = set()
        for move_ in moves:
            new_state, new_pieces, _, _ = self.move(state, pieces, castle_rights, move_[0], move_[1])
            if not self.is_check(new_state, new_pieces, player):
                legal_moves.add(move_)
        return legal_moves

    def get_pseudolegal_moves(self, player, state, pieces, en_passant, castle_rights=None):
        moves = set()
        for piece_type in c.WHITE_PIECES if player == 'white' else c.BLACK_PIECES:
            for piece_pos in pieces[piece_type]:
                if piece_type in ('white_pawn', 'black_pawn'):
                    moves.update(self.get_pawn_moves(piece_type, piece_pos, state))
                    moves.update(self.get_pawn_takes(piece_type, piece_pos, state, en_passant))
                else:
                    moves.update(self.get_default_moves(piece_type, piece_pos, state))

                if castle_rights:
                    if piece_type in ('white_king', 'black_king'):
                        moves.update(self.get_castle_moves(piece_type, piece_pos, state, pieces, castle_rights))
        return moves

    def get_default_moves(self, piece, position, state):
        opponent_pieces = self.opponent_pieces(piece)
        position_array = np.array(list(position))
        moves = set()
        directions, is_single_step = self.directions(piece)

        for direction in directions:
            current_position = position_array + direction
            while self.on_board(current_position):
                if self.state_entry(state, current_position) in opponent_pieces + ['empty']:
                    moves.add((position, tuple(current_position)))
                    if self.state_entry(state, current_position) != 'empty':
                        break
                    current_position += direction
                else:
                    break
                if is_single_step:
                    break
        return moves

    @staticmethod
    def directions(piece):
        # 2nd output is True if piece does only a single step
        if piece in ('white_queen', 'black_queen'):
            return np.array([[1, 1], [-1, 1], [1, -1], [-1, -1], [1, 0], [0, 1], [-1, 0], [0, -1]]), False
        if piece in ('white_rook', 'black_rook'):
            return np.array([[1, 0], [0, 1], [-1, 0], [0, -1]]), False
        if piece in ('white_bishop', 'black_bishop'):
            return np.array([[1, 1], [-1, 1], [1, -1], [-1, -1]]), False
        if piece in ('white_knight', 'black_knight'):
            return np.array([[1, 2], [2, 1], [-1, 2], [2, -1], [1, -2], [-2, 1], [-1, -2], [-2, -1]]), True
        if piece in ('white_king', 'black_king'):
            return np.array([[1, 1], [-1, 1], [1, -1], [-1, -1], [1, 0], [0, 1], [-1, 0], [0, -1]]), True
        raise NameError('Piece not valid!')

    def get_pawn_moves(self, piece, position, state):
        moves = set()
        move_direction = np.array([-1, 0] if piece == 'white_pawn' else [1, 0])

        single_move_pos = np.array(list(position)) + move_direction
        if self.state_entry(state, single_move_pos) == 'empty':
            moves.add((position, tuple(single_move_pos)))
            # check for double pawn move
            double_move_pos = single_move_pos + move_direction
            if (piece == 'white_pawn' and double_move_pos[0] == 4) \
                    or (piece == 'black_pawn' and double_move_pos[0] == 3):
                if self.state_entry(state, double_move_pos) == 'empty':
                    moves.add((position, tuple(double_move_pos)))
        return moves

    def get_pawn_takes(self, piece, position, state, en_passant):
        moves = set()
        position_array = np.array(list(position))
        take_directions = np.array([[-1, 1], [-1, -1]] if piece == 'white_pawn' else [[1, 1], [1, -1]])
        for direction in take_directions:
            target_pos = direction + position_array
            if not self.on_board(target_pos):
                continue
            if self.state_entry(state, target_pos) in self.opponent_pieces(piece):
                moves.add((position, tuple(target_pos)))
            if en_passant:
                correct_row = (piece == 'white_pawn' and target_pos[0] == 2 and en_passant[0] == 3) \
                              or (piece == 'black_pawn' and target_pos[0] == 5 and en_passant[0] == 4)
                correct_column = (target_pos[1] == en_passant[1])
                if correct_row and correct_column:
                    moves.add((position, tuple(target_pos)))
        return moves

    def get_castle_moves(self, piece, position, state, pieces, castle_rights):
        moves = set()
        if piece == 'white_king':
            if castle_rights['white_king_side']:
                if self.check_king_side(position, state, pieces, 'white'):
                    moves.add((position, (position[0], position[1] + 2)))
            if castle_rights['white_queen_side']:
                if self.check_queen_side(position, state, pieces, 'white'):
                    moves.add((position, (position[0], position[1] - 2)))
        if piece == 'black_king':
            if castle_rights['black_king_side']:
                if self.check_king_side(position, state, pieces, 'black'):
                    moves.add((position, (position[0], position[1] + 2)))
            if castle_rights['black_queen_side']:
                if self.check_queen_side(position, state, pieces, 'black'):
                    moves.add((position, (position[0], position[1] - 2)))
        return moves

    def check_king_side(self, position, state, pieces, player):
        if self.is_attacked(state, pieces, position, player):
            return False
        row, column = position[0], position[1]
        for square in ((row, column + 1), (row, column + 2)):
            if not self.on_board(square):
                raise ValueError('Castling outside board!')
            if self.state_entry(state, square) != 'empty':
                return False
            if self.is_attacked(state, pieces, square, player):
                return False
        return True

    def check_queen_side(self, position, state, pieces, player):
        if self.is_attacked(state, pieces, position, player):
            return False
        row, column = position[0], position[1]
        for square in ((row, column - 1), (row, column - 2)):
            if not self.on_board(square):
                raise ValueError('Castling outside board!')
            if self.state_entry(state, square) != 'empty':
                return False
            if self.is_attacked(state, pieces, square, player):
                return False
        if not self.on_board((row, column - 3)):
            raise ValueError('Castling outside board!')
        if self.state_entry(state, (row, column - 3)) != 'empty':
            return False
        return True

    def is_check(self, state, pieces, player):
        if not pieces[f'{player}_king']:
            return None
        king_pos = next(iter(pieces[f'{player}_king']))
        return self.is_attacked(state, pieces, king_pos, player)

    def is_attacked(self, state, pieces, position, player):
        opponent_moves = self.get_pseudolegal_moves(self.swap_player(player), state, pieces, None, None)
        for op_move in opponent_moves:
            if op_move[1] == position:
                return True
        return False

    @staticmethod
    def opponent_pieces(piece):
        if piece == 'empty':
            return None
        return c.BLACK_PIECES if piece in c.WHITE_PIECES else c.WHITE_PIECES

    @staticmethod
    def state_entry(state, position):
        return state[position[0]][position[1]]

    @staticmethod
    def get_player(piece):
        if piece in c.WHITE_PIECES:
            return 'white'
        if piece in c.BLACK_PIECES:
            return 'black'
        raise NameError('Piece belongs to no player!')


if __name__ == '__main__':
    game = Game()
    # print(game.state)
    # game.make_move((1, 3), (3, 3))
    # print(game.state, game.en_passant)
    # print(c.WHITE_PIECES)
    for move in game.game_legal_moves():
        print(move)
