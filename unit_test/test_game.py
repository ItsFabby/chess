import unittest
from chess.game import Game, State
from chess import constants as c


class TestImportPosition(unittest.TestCase):
    def setUp(self):
        self.state = State(c.DEFAULT_POSITION)
        self.state.board = [['empty' for _ in range(8)] for _ in range(8)]
        self.state.pieces = {piece: set() for piece in c.WHITE_PIECES + c.BLACK_PIECES}

    def test_get_piece(self):
        self.assertEqual(self.state.get_piece('n'), 'black_knight')

    def test_add_piece(self):
        state, pieces = self.state.add_piece('black_queen', self.state.board, self.state.pieces, 1, 2)
        self.assertEqual(state[1][2], 'black_queen')
        self.assertEqual(pieces['black_queen'], {(1, 2)})

    def test_import_caste_rights(self):
        self.assertDictEqual(
            self.state.import_castle_rights('Kq'),
            {'white_king_side': True, 'white_queen_side': False, 'black_king_side': False, 'black_queen_side': True}
        )
        self.assertDictEqual(
            self.state.import_castle_rights('-'),
            {'white_king_side': False, 'white_queen_side': False, 'black_king_side': False, 'black_queen_side': False}
        )


class TestUpdatePosition(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.state = State(c.EMPTY_BOARD)
        self.state.castle_rights = {'white_king_side': True, 'white_queen_side': True,
                                    'black_king_side': True, 'black_queen_side': True}

        self.state.board[1][3] = 'white_pawn'
        self.state.board[7][6] = 'white_pawn'
        self.state.board[2][3] = 'black_queen'
        self.state.board[7][7] = 'white_rook'
        self.state.board[1][2] = 'black_pawn'
        self.state.board[7][4] = 'white_king'

        self.state.pieces['white_pawn'].add((1, 3))
        self.state.pieces['white_pawn'].add((7, 6))
        self.state.pieces['black_queen'].add((2, 3))
        self.state.pieces['white_rook'].add((7, 7))
        self.state.pieces['black_pawn'].add((1, 2))
        self.state.pieces['white_king'].add((7, 4))

    def test_move1(self):
        state = self.game.move(self.state, (2, 3), (1, 3))
        self.assertEqual(state.board[1][3], 'black_queen')
        self.assertEqual(state.board[2][3], 'empty')
        self.assertSetEqual(state.pieces['black_queen'], {(1, 3)})
        self.assertSetEqual(state.pieces['white_pawn'], {(7, 6)})
        self.assertEqual(state.en_passant, None)
        self.assertDictEqual(state.castle_rights, self.state.castle_rights)

    def test_move2(self):
        state = self.game.move(self.state, (1, 3), (3, 3))
        self.assertEqual(state.board[3][3], 'white_pawn')
        self.assertEqual(state.board[1][3], 'empty')
        self.assertEqual(state.board[2][3], 'black_queen')
        self.assertSetEqual(state.pieces['black_queen'], {(2, 3)})
        self.assertSetEqual(state.pieces['white_pawn'], {(7, 6), (3, 3)})
        self.assertEqual(state.en_passant, (3, 3))
        self.assertDictEqual(state.castle_rights, self.state.castle_rights)

    def test_move3(self):
        state = self.game.move(self.state, (7, 7), (7, 6))
        self.assertEqual(state.castle_rights,
                         {'white_king_side': False, 'white_queen_side': True,
                          'black_king_side': True, 'black_queen_side': True}
                         )

    def test_move_en_passant(self):
        state = self.game.move(self.state, (1, 3), (2, 2))
        self.assertEqual(state.board[2][2], 'white_pawn')
        self.assertEqual(state.board[1][2], 'empty')
        self.assertSetEqual(state.pieces['black_pawn'], set())

    def test_move_castling(self):
        state = self.game.move(self.state, (7, 4), (7, 6))
        self.assertEqual(state.board[7][5], 'white_rook')
        self.assertEqual(state.board[7][7], 'empty')
        self.assertSetEqual(state.pieces['white_rook'], {(7, 5)})
        self.assertEqual(state.player, 'black')

    def test_move_promotion(self):
        state = self.game.move(self.state, (1, 3), (0, 3))
        self.assertEqual(state.board[0][3], 'white_queen')
        self.assertSetEqual(state.pieces['white_queen'], {(0, 3)})
        self.assertSetEqual(state.pieces['white_pawn'], {(7, 6)})


class TestGetLegalMoves(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.state = State(c.EMPTY_BOARD)

        self.state.board[1][2] = 'white_knight'
        self.state.board[5][7] = 'black_knight'
        self.state.board[3][3] = 'white_pawn'
        self.state.board[3][4] = 'black_king'

        self.state.pieces['white_knight'].add((1, 2))
        self.state.pieces['black_knight'].add((5, 7))
        self.state.pieces['white_pawn'].add((3, 3))
        self.state.pieces['black_king'].add((3, 4))

    def test_knight(self):
        self.assertSetEqual(self.game.get_default_moves('white_knight', (1, 2), self.state),
                            {((1, 2), (0, 0)), ((1, 2), (0, 4)), ((1, 2), (2, 0)), ((1, 2), (2, 4)), ((1, 2), (3, 1))})

    def test_is_attacked(self):
        self.assertTrue(self.game.is_attacked(self.state, (3, 3)))
        self.assertFalse(self.game.is_attacked(self.state, (3, 4)))

    def test_pseudo_move(self):
        self.state.player = 'black'
        self.assertIn(((3, 4), (2, 4)), self.game.get_pseudolegal_moves(self.state))
        self.assertNotIn(((3, 4), (2, 4)), self.game.get_legal_moves(self.state))


if __name__ == '__main__':
    unittest.main()
