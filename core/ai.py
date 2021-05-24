from typing import List, Optional
import random
import numpy as np

from game import Game, State
from neural_network import NNet


def move_max(state: State, nnet: NNet) -> tuple:
    """
    Returns the move with the maximal probability from the neural network.

    :param state: State to evaluate
    :param nnet: Neural network used for evaluation
    :return: Best move as ((origin_row, origin_column),(target_row,target_column)
    """
    policy = nnet.prediction(state)[0]
    return max(policy, key=policy.get)


def move_weighted(state: State, nnet: NNet) -> tuple:
    """
    Returns are random move with weighted probabilities from the neural network.

    :param state: State to evaluate
    :param nnet: Neural network used for evaluation
    :return: Move as ((origin_row, origin_column),(target_row,target_column)
    """
    policy = nnet.prediction(state)[0]
    moves = list(policy.keys())
    weights = list(policy.values())
    return random.choices(moves, weights=weights)[0]


def fast_tree_search(state: State, nnet: NNet, move_number: int, depth: int) -> tuple:
    """
    For a given start state the moves with the highest policy are evaluated. For each of these the series of most likely
    best moves is considered up to a certain depth. At that depth the predicted values resulting from each initial move
    are compared and the move with the highest value is returned.

    :param state: State to evaluate
    :param nnet: Neural network used for evaluation
    :param move_number: Number of moves considered for the initial state
    :param depth: Length of the series of moves evaluated going out from each initial move
    :return: Best move as ((origin_row, origin_column),(target_row,target_column)
    """
    start_node = _Node(None, state, None)
    start_node.fetch_prediction(nnet)
    start_node.create_children(move_number)
    move_values = {}

    for child in start_node.children:
        current_node = child
        value = None
        for _ in range(depth):
            if current_node.state.winner == 'draw':
                value = 0.5
                break
            if current_node.state.winner == start_node.state.player:
                value = 1
                break
            if current_node.state.winner == Game.swap_player(start_node.state.player):
                value = 0
                break

            current_node.fetch_prediction(nnet)
            value = current_node.value
            current_node.create_children(1)
            current_node = current_node.children[0]

        print(f'{state.player} - move:{child.move}, value:{value}')
        move_values[child.move] = value

    return max(move_values, key=move_values.get)


class _Node:
    def __init__(self, parent: Optional['_Node'], state: State, move: Optional[tuple]):
        self.state = state
        self.children: List['_Node'] = []
        self.parent = parent
        self.move = move

        self.policy: np.array = None
        self.value = 0.5

    def create_children(self, max_number: int) -> None:
        if not self.policy:
            raise ValueError('Fetch network predictions first!')

        sorted_policy = sorted(self.policy, key=self.policy.get, reverse=True)
        for i in range(min(max_number, len(sorted_policy))):
            move = sorted_policy[i]
            self._create_child(move)

    def _create_child(self, move: tuple) -> None:
        self.children.append(_Node(self, Game.move(self.state, move[0], move[1]), move))

    def fetch_prediction(self, nnet: NNet) -> None:
        self.policy, self.value = nnet.prediction(self.state)
