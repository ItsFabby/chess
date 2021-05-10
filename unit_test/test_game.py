import unittest
from chess.game import Game

WHITE_PIECES = ['white_pawn', 'white_knight', 'white_bishop', 'white_rook', 'white_queen', 'white_king']
BLACK_PIECES = ['black_pawn', 'black_knight', 'black_bishop', 'black_rook', 'black_queen', 'black_king']


class TestImportPosition(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.state = [['empty' for _ in range(8)] for _ in range(8)]
        self.pieces = {piece: set() for piece in WHITE_PIECES + BLACK_PIECES}

    def test_get_piece(self):
        self.assertEqual(self.game.get_piece('n'), 'black_knight')

    def test_add_piece(self):
        state, pieces = self.game.add_piece('black_queen', self.state, self.pieces, 1, 2)
        self.assertEqual(state[1][2], 'black_queen')
        self.assertEqual(pieces['black_queen'], {(1, 2)})

    def test_import_caste_rights(self):
        self.assertDictEqual(
            self.game.import_castle_rights('Kq'),
            {'white_king_side': True, 'white_queen_side': False, 'black_king_side': False, 'black_queen_side': True}
        )
        self.assertDictEqual(
            self.game.import_castle_rights('-'),
            {'white_king_side': False, 'white_queen_side': False, 'black_king_side': False, 'black_queen_side': False}
        )


class TestUpdatePosition(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.state = [['empty' for _ in range(8)] for _ in range(8)]
        self.pieces = {piece: set() for piece in WHITE_PIECES + BLACK_PIECES}
        self.castle_rights = {'white_king_side': True, 'white_queen_side': True,
                              'black_king_side': True, 'black_queen_side': True}

        self.state[1][3] = 'white_pawn'
        self.state[7][6] = 'white_pawn'
        self.state[2][3] = 'black_queen'
        self.state[7][7] = 'white_rook'

        self.pieces['white_pawn'].add((1, 3))
        self.pieces['white_pawn'].add((7, 6))
        self.pieces['black_queen'].add((2, 3))
        self.pieces['white_rook'].add((7, 7))

    def test_move(self):
        state, pieces, castle_rights, en_passant = \
            self.game.move(self.state, self.pieces, self.castle_rights, (2, 3), (1, 3))
        self.assertEqual(state[1][3], 'black_queen')
        self.assertEqual(state[2][3], 'empty')
        self.assertSetEqual(pieces['black_queen'], {(1, 3)})
        self.assertSetEqual(pieces['white_pawn'], {(7, 6)})
        self.assertEqual(en_passant, None)
        self.assertDictEqual(castle_rights, self.castle_rights)

        state, pieces, castle_rights, en_passant = \
            self.game.move(self.state, self.pieces, self.castle_rights, (1, 3), (3, 3))
        self.assertEqual(state[3][3], 'white_pawn')
        self.assertEqual(state[1][3], 'empty')
        self.assertEqual(state[2][3], 'black_queen')
        self.assertSetEqual(pieces['black_queen'], {(2, 3)})
        self.assertSetEqual(pieces['white_pawn'], {(7, 6), (3, 3)})
        self.assertEqual(en_passant, (3, 3))
        self.assertDictEqual(castle_rights, self.castle_rights)

        state, pieces, castle_rights, en_passant = \
            self.game.move(self.state, self.pieces, self.castle_rights, (7, 7), (7, 6))
        self.assertEqual(castle_rights,
                         {'white_king_side': False, 'white_queen_side': True,
                          'black_king_side': True, 'black_queen_side': True}
                         )

    # def test_get_pseudolegal_moves(self):


if __name__ == '__main__':
    unittest.main()
