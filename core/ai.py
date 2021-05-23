from typing import List, Optional
import random
import numpy as np

from game import Game, State
from neural_network import NNet


def move_max(state: 'State', nnet: 'NNet') -> tuple:
    policy = nnet.prediction(state)[0]
    return max(policy, key=policy.get)


def move_weighted(state: 'State', nnet) -> tuple:
    policy = nnet.prediction(state)[0]
    moves = list(policy.keys())
    weights = list(policy.values())
    return random.choices(moves, weights=weights)[0]


def fast_tree_search(state: 'State', nnet, move_number: int, depth: int) -> tuple:
    start_node = Node(None, state, None)
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
            if current_node.state.winner == 'white':
                value = 1
                break
            if current_node.state.winner == 'black':
                value = 1
                break

            current_node.fetch_prediction(nnet)
            value = current_node.value
            current_node.create_children(1)
            current_node = current_node.children[0]

        print(f'{state.player} - move:{child.move}, value:{value}')
        move_values[child.move] = value

    return max(move_values, key=move_values.get)


# def tree_search(state: 'State', nnet, scheme: list):
#     start_node = Node(None, state, None)
#     start_node.fetch_prediction(nnet)
#     start_node.create_children(scheme[0])
#     for child in start_node.children:
#         value = start_node.value
#         for level in range(len(scheme)):
#             pass


class Node:
    def __init__(self, parent: Optional['Node'], state: 'State', move: Optional[tuple]):
        self.state = state
        self.children: List['Node'] = []
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
        self.children.append(Node(self, Game.move(self.state, move[0], move[1]), move))

    def fetch_prediction(self, nnet: 'NNet') -> None:
        self.policy, self.value = nnet.prediction(self.state)
