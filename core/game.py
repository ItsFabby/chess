import numpy as np
import copy
from typing import Optional, Tuple

import constants as c


class Game:
    """
    Implements chess.

    Attrs:
        state (Object: State): Current state of the game. Contains piece positions, castle rights, en passant, which
        player is next and whether the game has a winner

    Methods on the state of the current instance:
        game_winner() -> Str,
        make_move(origin_pos, target_pos) -> None,
        game_legal_moves() -> Set((origin_pos, target_pos))

    Class methods:
        get_winner(state) -> Str,
        move(state, origin_pos, target_pos) -> State,
        get_legal_moves(state) -> Set((origin_pos, target_pos)),
        is_check(state) -> Bool
    """

    def __init__(self, position=c.DEFAULT_POSITION):
        self.state = State(position)

    def game_winner(self):
        """
        Returns the winner of the current instance of the game.

        :return: 'white', 'black', 'draw' or None
        """
        return self.get_winner(self.state)

    @classmethod
    def get_winner(cls, state: 'State') -> Optional[str]:
        """
        Returns the winner of a given state.

        :param state: State
        :return: 'white', 'black', 'draw' or None
        """
        if state.winner:
            return state.winner
        if cls.get_legal_moves(state):
            return None
        if cls.is_check(state):
            return cls._swap_player(state.player)
        return 'draw'

    @classmethod
    def is_check(cls, state: 'State') -> bool:
        if not state.pieces[f'{state.player}_king']:
            return False
        king_pos = next(iter(state.pieces[f'{state.player}_king']))
        return cls._is_attacked(state, king_pos)

    def make_move(self, origin_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> None:
        """
        Makes a move on the current instance of the game. It automatically applies en passant, castling
        and pawn to queen promotions. Castling is specified by moving the king to squares. This method does not check
        whether a move is legal!

        :param origin_pos: (row, column)
        :param target_pos: (row, column)
        """
        self.state = self.move(self.state, origin_pos, target_pos)

    # this implementation allows taking of own state.pieces and does not check if move is legal
    @classmethod
    def move(cls, state: 'State', origin_pos: Tuple[int, int], target_pos: Tuple[int, int],
             update_winner: bool = True) -> 'State':
        """
        Makes a move on an input state and outputs the resulting state. It automatically applies en passant, castling
        and pawn to queen promotions. Castling is specified by moving the king to squares. This method does not check
        whether a move is legal!

        :param update_winner: Updates the winner attribute of the new State. Option is needed to prevent recursion loop.
        :param state: State
        :param origin_pos: (row, column)
        :param target_pos: (row, column)
        :return: State object
        """

        if not cls._on_board(origin_pos):
            raise ValueError('Origin position not on board!')
        if not cls._on_board(target_pos):
            raise ValueError('Target position not on board!')
        if origin_pos == target_pos:
            raise ValueError('Origin and target position cannot be equal!')
        if state.board[origin_pos[0]][origin_pos[1]] == 'empty':
            raise ValueError('Origin position is empty!')
        state = copy.deepcopy(state)
        old_state = copy.deepcopy(state)

        state = cls._apply_en_passant(state, origin_pos, target_pos)
        state = cls._apply_castling(state, origin_pos, target_pos)
        state = cls._apply_normal_move(state, origin_pos, target_pos)
        state = cls._apply_promotion(state, target_pos)

        state.swap_player()
        state = cls._add_repetition(state, old_state)

        if update_winner:
            state.winner = cls.get_winner(state)

        return state

    @classmethod
    def _apply_normal_move(cls, state: 'State', origin_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> 'State':
        origin_piece = state.entry(origin_pos)
        tar_get_piece = state.entry(target_pos)
        state.board[origin_pos[0]][origin_pos[1]] = 'empty'
        state.pieces[origin_piece].remove(origin_pos)

        state.board[target_pos[0]][target_pos[1]] = origin_piece
        state.pieces[origin_piece].add(target_pos)

        if tar_get_piece != 'empty':
            state.pieces[tar_get_piece].remove(target_pos)
            state.repetition_counter = {}

        state.castle_rights = cls._update_castle_rights(state.castle_rights, origin_piece, origin_pos, target_pos)
        state.en_passant = cls._update_en_passant(origin_piece, origin_pos, target_pos)
        return state

    @staticmethod
    def _apply_promotion(state: 'State', position: Tuple[int, int]) -> 'State':
        piece = state.entry(position)
        if (piece == 'white_pawn' and position[0] == 0) or (piece == 'black_pawn' and position[0] == c.ROWS - 1):
            state.board[position[0]][position[1]] = f'{state.player}_queen'
            state.pieces[f'{state.player}_queen'].add(position)
            state.pieces[f'{state.player}_pawn'].remove(position)
        return state

    @classmethod
    def _apply_castling(cls, state: 'State', origin_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> 'State':
        if not cls._detect_castling(state, origin_pos, target_pos):
            return state
        rook_row = origin_pos[0]
        rook_origin_column = 0 if target_pos[1] == 2 else c.COLUMNS - 1
        rook_target_column = 3 if target_pos[1] == 2 else c.COLUMNS - 3
        if state.entry((rook_row, rook_origin_column)) == 'empty':
            return state
        state = cls.move(state, (rook_row, rook_origin_column), (rook_row, rook_target_column))
        state.swap_player()
        return state

    @staticmethod
    def _detect_castling(state: 'State', origin_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> bool:
        piece = state.entry(origin_pos)
        if piece not in ('white_king', 'black_king'):
            return False
        if abs(origin_pos[1] - target_pos[1]) == 2:
            return True
        return False

    @classmethod
    def _apply_en_passant(cls, state: 'State', origin_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> 'State':
        if not cls._detect_en_passant(state, origin_pos, target_pos):
            return state
        square_to_remove = (origin_pos[0], target_pos[1])
        piece_to_remove = state.entry(square_to_remove)
        state.board[square_to_remove[0]][square_to_remove[1]] = 'empty'
        state.pieces[piece_to_remove].remove(square_to_remove)
        return state

    @staticmethod
    def _detect_en_passant(state: 'State', origin_pos: Tuple[int, int], target_pos: Tuple[int, int]) -> bool:
        piece = state.entry(origin_pos)
        if piece not in ('white_pawn', 'black_pawn'):
            return False
        tar_get_piece = state.entry(target_pos)
        if tar_get_piece == 'empty':
            if abs(origin_pos[0] - target_pos[0]) == 1 and abs(origin_pos[1] - target_pos[1]) == 1:
                return True
        return False

    @staticmethod
    def _update_en_passant(origin_piece: str, origin_pos: Tuple[int, int], target_pos: Tuple[int, int]) \
            -> Optional[Tuple[int, int]]:
        en_passant = None
        if origin_piece in ('white_pawn', 'black_pawn'):
            if origin_pos[0] - target_pos[0] in (-2, 2):
                en_passant = target_pos
        return en_passant

    @staticmethod
    def _update_castle_rights(castle_rights: dict, origin_piece: str, origin_pos: Tuple[int, int],
                              target_pos: Tuple[int, int]) -> dict:
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

    @classmethod
    def _add_repetition(cls, new_state: 'State', old_state: 'State') -> 'State':
        repetition_counter = old_state.repetition_counter
        new_board = tuple(tuple(row) for row in new_state.board)
        if new_board in repetition_counter.keys():
            if repetition_counter[new_board] == 0:
                new_state.repetition_counter[new_board] = 1
            else:
                new_state.winner = 'draw'
            return new_state
        repetition_counter[new_board] = 0
        new_state.repetition_counter = repetition_counter
        return new_state

    @staticmethod
    def _on_board(position: Tuple[int, int]) -> bool:
        return 0 <= position[0] < c.ROWS and 0 <= position[1] < c.COLUMNS

    """Get legal moves"""

    def game_legal_moves(self) -> set:
        """
        Returns all legal move options for the state of the current game instance.

        :return: Set(move) with  move: (origin_position, target_position)
        """
        return self.get_legal_moves(self.state)

    @classmethod
    def get_legal_moves(cls, state: 'State') -> set:
        """
        Returns all legal move options for a given state.

        :param state: State
        :return: Set(move) with  move: (origin_position, target_position)
        """
        moves = cls._get_pseudolegal_moves(state)
        legal_moves = set()
        for move_ in moves:
            new_state = cls.move(state, move_[0], move_[1], update_winner=False)
            new_state.swap_player()
            if not cls.is_check(new_state):
                legal_moves.add(move_)
        return legal_moves

    @classmethod
    def _get_pseudolegal_moves(cls, state: 'State') -> set:
        moves = set()
        for piece_type in c.WHITE_PIECES if state.player == 'white' else c.BLACK_PIECES:
            for piece_pos in state.pieces[piece_type]:
                if piece_type in ('white_pawn', 'black_pawn'):
                    moves.update(cls._get_pawn_moves(piece_type, piece_pos, state))
                    moves.update(cls._get_pawn_takes(piece_type, piece_pos, state))
                else:
                    moves.update(cls._get_normal_moves(piece_type, piece_pos, state))

                if state.castle_rights:
                    if piece_type in ('white_king', 'black_king'):
                        moves.update(cls._get_castle_moves(piece_type, piece_pos, state))
        return moves

    @classmethod
    def _get_normal_moves(cls, piece: str, position: Tuple[int, int], state: 'State') -> set:
        _opponent_pieces = cls._opponent_pieces(piece)
        position_array = np.array(list(position))
        moves = set()
        _directions, is_single_step = cls._directions(piece)

        for direction in _directions:
            current_position = position_array + direction
            while cls._on_board(current_position):
                if state.entry(current_position) in _opponent_pieces + ['empty']:
                    moves.add((position, tuple(current_position)))
                    if state.entry(current_position) != 'empty':
                        break
                    current_position += direction
                else:
                    break
                if is_single_step:
                    break
        return moves

    @staticmethod
    def _directions(piece: str) -> np.array:
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

    @classmethod
    def _get_pawn_moves(cls, piece: str, position: Tuple[int, int], state: 'State') -> set:
        moves = set()
        move_direction = np.array([-1, 0] if piece == 'white_pawn' else [1, 0])

        single_move_pos = np.array(list(position)) + move_direction
        if not cls._on_board(single_move_pos):
            return moves
        if state.entry(single_move_pos) == 'empty':
            moves.add((position, tuple(single_move_pos)))
            # check for double pawn move
            double_move_pos = single_move_pos + move_direction
            if not cls._on_board(double_move_pos):
                return moves
            if (piece == 'white_pawn' and double_move_pos[0] == c.ROWS - 4) \
                    or (piece == 'black_pawn' and double_move_pos[0] == 3):
                if state.entry(double_move_pos) == 'empty':
                    moves.add((position, tuple(double_move_pos)))
        return moves

    @classmethod
    def _get_pawn_takes(cls, piece: str, position: Tuple[int, int], state: 'State') -> set:
        moves = set()
        position_array = np.array(list(position))
        take__directions = np.array([[-1, 1], [-1, -1]] if piece == 'white_pawn' else [[1, 1], [1, -1]])
        for direction in take__directions:
            target_pos = direction + position_array
            if not cls._on_board(target_pos):
                continue
            if state.entry(target_pos) in cls._opponent_pieces(piece):
                moves.add((position, tuple(target_pos)))
            if state.en_passant:
                correct_row = (piece == 'white_pawn' and target_pos[0] == 2 and state.en_passant[0] == 3) \
                              or (piece == 'black_pawn' and target_pos[0] == 5 and state.en_passant[0] == 4)
                correct_column = (target_pos[1] == state.en_passant[1])
                if correct_row and correct_column:
                    moves.add((position, tuple(target_pos)))
        return moves

    @classmethod
    def _get_castle_moves(cls, piece: str, position: Tuple[int, int], state: 'State') -> set:
        moves = set()
        if piece == 'white_king':
            if state.castle_rights['white_king_side']:
                if cls._check_king_side(position, state):
                    moves.add((position, (position[0], position[1] + 2)))
            if state.castle_rights['white_queen_side']:
                if cls._check_queen_side(position, state):
                    moves.add((position, (position[0], position[1] - 2)))
        if piece == 'black_king':
            if state.castle_rights['black_king_side']:
                if cls._check_king_side(position, state):
                    moves.add((position, (position[0], position[1] + 2)))
            if state.castle_rights['black_queen_side']:
                if cls._check_queen_side(position, state):
                    moves.add((position, (position[0], position[1] - 2)))
        return moves

    @classmethod
    def _check_king_side(cls, position: Tuple[int, int], state: 'State') -> bool:
        if cls._is_attacked(state, position):
            return False
        row, column = position[0], position[1]
        for square in ((row, column + 1), (row, column + 2)):
            if not cls._on_board(square):
                raise ValueError('Castling outside board!')
            if state.entry(square) != 'empty':
                return False
            if cls._is_attacked(state, square):
                return False
        return True

    @classmethod
    def _check_queen_side(cls, position: Tuple[int, int], state: 'State') -> bool:
        if cls._is_attacked(state, position):
            return False
        row, column = position[0], position[1]
        for square in ((row, column - 1), (row, column - 2)):
            if not cls._on_board(square):
                raise ValueError('Castling outside board!')
            if state.entry(square) != 'empty':
                return False
            if cls._is_attacked(state, square):
                return False
        if not cls._on_board((row, column - 3)):
            raise ValueError('Castling outside board!')
        if state.entry((row, column - 3)) != 'empty':
            return False
        return True

    @classmethod
    def _is_attacked(cls, state: 'State', position: Tuple[int, int]) -> bool:
        state = copy.deepcopy(state)
        state.castle_rights = None
        state.swap_player()
        opponent_moves = cls._get_pseudolegal_moves(state)
        for op_move in opponent_moves:
            if op_move[1] == position:
                return True
        return False

    @staticmethod
    def _opponent_pieces(piece: str) -> Optional[list]:
        if piece == 'empty':
            return None
        return c.BLACK_PIECES if piece in c.WHITE_PIECES else c.WHITE_PIECES

    @staticmethod
    def _get_player(piece: str) -> str:
        if piece in c.WHITE_PIECES:
            return 'white'
        if piece in c.BLACK_PIECES:
            return 'black'
        raise NameError('Piece belongs to no player!')

    @staticmethod
    def _swap_player(player: str) -> str:
        return 'black' if player == 'white' else 'white'


class State:
    def __init__(self, fen_string: str):
        self.board, self.pieces, self.player, self.castle_rights, self.en_passant \
            = self._import_position(fen_string)
        self.winner = None
        self.repetition_counter = {}

    @classmethod
    def _import_position(cls, fen_position: str) -> Tuple[list, dict, str, dict, Optional[tuple]]:
        fen_position = fen_position.split(' ')

        board, pieces = cls._import_board_position(fen_position[0])
        player = 'white' if fen_position[1] == 'w' else 'black'
        castle_rights = cls._import_castle_rights(fen_position[2])
        en_passant = cls._import_en_passant(fen_position[3])

        return board, pieces, player, castle_rights, en_passant

    def set_position(self, fen_position: str) -> None:
        try:
            self.board, self.pieces, self.player, self.castle_rights, self.en_passant \
                = self._import_position(fen_position)
        except ValueError as E:
            print(f'Error: {E}')

    @classmethod
    def _import_board_position(cls, fen_position: str) -> Tuple[list, dict]:
        board = [['empty' for _ in range(c.ROWS)] for _ in range(c.COLUMNS)]
        pieces = {piece: set() for piece in c.WHITE_PIECES + c.BLACK_PIECES}
        column, row = 0, 0
        for character in fen_position:
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

            piece = cls._get_piece(character)
            board, pieces = cls._add_piece(piece, board, pieces, row, column)
            column += 1

        if column < c.COLUMNS - 1 or row < c.ROWS - 1:
            raise ValueError('Position not valid: Board string too short!')
        return board, pieces

    @staticmethod
    def _get_piece(character: chr) -> str:
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
    def _add_piece(piece: str, board: list, pieces: dict, row: int, column: int) -> Tuple[list, dict]:
        if board[row][column] != 'empty':
            raise ValueError('Target square not empty!')
        if piece not in c.WHITE_PIECES + c.BLACK_PIECES:
            raise NameError('Input piece not valid!')
        board[row][column] = piece
        pieces[piece].add((row, column))
        return board, pieces

    @staticmethod
    def _import_castle_rights(fen_position: str) -> dict:
        castle_rights = {'white_king_side': False, 'white_queen_side': False,
                         'black_king_side': False, 'black_queen_side': False}
        for character in fen_position:
            if character == 'K':
                castle_rights['white_king_side'] = True
            if character == 'Q':
                castle_rights['white_queen_side'] = True
            if character == 'k':
                castle_rights['black_king_side'] = True
            if character == 'q':
                castle_rights['black_queen_side'] = True
        return castle_rights

    @staticmethod
    def _import_en_passant(algebraic: str) -> Optional[tuple]:
        if algebraic == '-':
            return None
        alg = list(algebraic)
        return c.ROWS - int(alg[1]), ord(alg[0]) - 97

    def entry(self, position: Tuple[int, int]) -> str:
        return self.board[position[0]][position[1]]

    def swap_player(self) -> None:
        self.player = 'black' if self.player == 'white' else 'white'


if __name__ == '__main__':
    game = Game()
    # print(game.state.board)
    # game.make_move((1, 3), (3, 3))
    # print(game.state.board, game.en_passant)
    # print(c.WHITE_PIECES)
    for move in game.game_legal_moves():
        print(move)
