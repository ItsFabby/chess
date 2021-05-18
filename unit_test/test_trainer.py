import unittest

from chess import trainer
from chess.neural_network import NNet
from chess.game import State, Game
from chess import constants as c


class TestConversions(unittest.TestCase):
    def test__to_algebraic(self):
        self.assertEqual(trainer._to_algebraic(((0, 1), (2, 3))), 'b8d6')

    def test__from_algebraic(self):
        self.assertEqual(trainer._from_algebraic('b8d6'), ((0, 1), (2, 3)))

    def test_policy1(self):
        state = State(c.DEFAULT_POSITION)
        move = ((6, 2), (4, 2))
        self.assertEqual(NNet._get_policy(NNet._to_policy_vector(move, 'white'), state)[move], 1)

    def test_policy2(self):
        game = Game()
        game.make_move((6, 2), (4, 2))
        move = ((1, 2), (3, 2))
        self.assertEqual(NNet._get_policy(NNet._to_policy_vector(move, 'black'), game.state)[move], 1)

    def test_prediction(self):
        nn = NNet()
        state = State(c.DEFAULT_POSITION)
        self.assertIsInstance(nn.prediction(state), tuple)


if __name__ == '__main__':
    unittest.main()
