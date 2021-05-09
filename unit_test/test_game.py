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


if __name__ == '__main__':
    unittest.main()
