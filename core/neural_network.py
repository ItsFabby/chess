import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.layers import Dense, Flatten, Conv2D, Input, BatchNormalization, Activation, Add
import os
import math
from typing import Optional, Dict, Tuple, Any

from game import Game, State
import constants as c

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class NNet:
    """
    Neural network consisting of residual convolutional layers splitting into policy and value outputs.
    """

    def __init__(self, epochs: int = c.DEFAULT_EPOCHS, learning_rate: float = c.DEFAULT_LEARNING_RATE,
                 batch_size: int = c.DEFAULT_BATCH_SIZE, structure: str = c.DEFAULT_STRUCTURE,
                 load_data: bool = True):

        self.epochs = epochs
        self.batch_size = batch_size

        self.structure = structure
        self.model = self._get_model(learning_rate, load_data, structure)

    @classmethod
    def _get_model(cls, learning_rate: float, load_data: bool, structure: str) -> keras.Model:

        inputs = Input(shape=(c.ROWS, c.COLUMNS, 6 * 2 + 6))

        x = Conv2D(filters=256, kernel_size=(3, 3), padding='same')(inputs)
        x = BatchNormalization(axis=3)(x)
        x = Activation('relu')(x)

        for _ in range(5):
            x = cls._res_net(inputs=x, filters=256, kernel_size=(3, 3))

        policy = Conv2D(filters=256, kernel_size=(3, 3), padding='valid')(x)
        policy = BatchNormalization(axis=3)(policy)
        policy = Activation('relu')(policy)
        policy = Flatten()(policy)
        policy = Dense(256, activation='relu')(policy)
        policy = Dense((c.ROWS * c.COLUMNS) ** 2, activation='softmax', name='policy')(policy)

        value = Conv2D(filters=128, kernel_size=(3, 3), padding='valid')(x)
        value = BatchNormalization(axis=3)(value)
        value = Activation('relu')(value)
        value = Flatten()(value)
        value = Dense(1, activation='sigmoid', name='value')(value)

        model = keras.Model(inputs=inputs, outputs=[policy, value])

        model.compile(
            optimizer=tf.optimizers.Adam(learning_rate=learning_rate),
            loss={'value': 'mean_squared_error',
                  'policy': 'categorical_crossentropy'}
        )

        if load_data:
            try:
                model.load_weights(f'{parent_dir}\\weights\\{structure}\\').expect_partial()
            except ValueError:
                print('No saved weights found')

        return model

    @staticmethod
    def _res_net(inputs: Any, filters: int, kernel_size: tuple) -> Any:
        x_shortcut = inputs

        x = Conv2D(filters=filters, kernel_size=kernel_size, padding='same')(inputs)
        x = BatchNormalization(axis=3)(x)
        x = Activation('relu')(x)

        x = Conv2D(filters=filters, kernel_size=kernel_size, padding='same')(x)
        x = BatchNormalization(axis=3)(x)

        x = Add()([x, x_shortcut])
        x = Activation('relu')(x)
        return x

    def train(self, examples: list, save_data=False) -> None:
        """
        Trains the neural network from a list of training examples.

        :param examples: Training data as List[(state,(policy,value))]
        :param save_data: Always saves the new weights if True
        """
        x_train = np.array([self._to_binary_state(example[0]) for example in examples])
        y_policy = np.array([self._to_policy_vector(example[1][0], example[0].player) for example in examples])
        y_value = np.array([self._get_value(example[1][1], example[0].player) for example in examples])

        self.model.fit(x=x_train, y={'policy': y_policy, 'value': y_value},
                       epochs=self.epochs, batch_size=self.batch_size, shuffle=True)
        if save_data:
            self.model.save_weights(f'{parent_dir}\\weights\\{self.structure}\\')

    def prediction(self, state: State) -> Tuple[dict, float]:
        """
        Returns a policy and value prediction for a given state. Value is from the perspective of the player making
        the next move.

        :param state: State to evaluate
        :return: (policy, vector). Policy is given as probability vector and value between 0 and 1.
        """
        binary_state = self._to_binary_state(state)
        prediction = self.model.predict(np.array([binary_state]))

        policy = self._get_policy(prediction[0][0], state)
        value = prediction[1][0][0]
        return policy, value

    # policy vectors are from the perspective of the player making the move
    @classmethod
    def _to_policy_vector(cls, move: tuple, player: str) -> np.array:
        policy = np.zeros(c.ROWS ** 2 * c.COLUMNS ** 2)
        policy[cls._policy_index(move, player)] = 1
        return policy

    @staticmethod
    def _policy_index(move: tuple, player: str) -> int:
        if player == 'black':
            # mirror row of move
            move = ((c.ROWS - move[0][0] - 1, move[0][1]), (c.ROWS - move[1][0] - 1, move[1][1]))
        base = (1, c.ROWS, c.ROWS * c.COLUMNS, c.ROWS * c.COLUMNS * c.ROWS)
        return move[0][0] * base[0] + move[0][1] * base[1] + move[1][0] * base[2] + move[1][1] * base[3]

    @classmethod
    def _get_policy(cls, policy: np.ndarray, state: State) -> Dict:
        legal_moves = Game.get_legal_moves(state)
        policy_dict = {move: policy[cls._policy_index(move, state.player)] for move in legal_moves}
        value_sum = sum(policy_dict.values())
        return {move: value / value_sum for move, value in policy_dict.items()}

    @staticmethod
    def _get_value(evaluation, player):
        evaluation *= c.ALPHA_SIGMOID
        value = 1 / (1 + math.exp(-evaluation))
        if player == 'black':
            value = 1 - value
        return value

    # binary states are from the perspective of the player making the move
    @classmethod
    def _to_binary_state(cls, state: State) -> np.array:
        black = state.player == 'black'
        bin_state = np.zeros(shape=(c.ROWS, c.COLUMNS, 6 * 2 + 6))
        for row in range(c.ROWS):
            for column in range(c.COLUMNS):
                index = cls._piece_index(state.board[row][column])
                if index:
                    piece_index = index[1] + 6 * int(state.player == index[0])
                    bin_state[row, column, piece_index] = 1

                for i, right in enumerate(state.castle_rights):
                    if black:
                        i = i + 2 % 4
                    bin_state[row, column, 12 + i] = 1

                if black:
                    bin_state[row, column, 17] = 1

        if state.en_passant:
            bin_state[state.en_passant[0], state.en_passant[1], 16] = 1

        if black:
            bin_state = np.flip(bin_state, axis=0)
        return bin_state

    @staticmethod
    def _piece_index(piece: str) -> Optional[tuple]:
        if piece == 'empty':
            return None
        piece = piece.split('_')
        typing = {
            'pawn': 0,
            'knight': 1,
            'bishop': 2,
            'rook': 3,
            'queen': 4,
            'king': 5
        }
        return piece[0], typing.get(piece[1])


if __name__ == '__main__':
    nn = NNet()
    game = Game('8/1P3k2/8/8/8/8/4K3/8 w - - 0 1')
    print(nn.prediction(game.state))
