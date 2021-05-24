from stockfish import Stockfish
import random
from typing import Optional
import sys
import os
import pandas as pd

from game import Game, State
from db_connector import Connector
from neural_network import NNet
import constants as c
import ai

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gen_examples(randomness: float = 0.7, randomness_decline: float = 0.95, max_moves: int = 80,
                 table: str = c.DEFAULT_TABLE) -> None:
    """
    Generates training examples using Stockfish and stores them in a database in algebraic notation. Set up a MySQL 
    database first and set the connection in constants.py. Also make sure that Stockfish is installed correctly.

    :param table: Table the data is stored in.
    :param randomness: Starting Probability for proceeding with are random move instead of the best move. This is
        necessary to not simulate the same game each time.
    :param randomness_decline: Factor applied to the randomness with each move. Should be less than 1 to have less 
        randomness later in the game.
    :param max_moves: Stops the simulated game early to prevent too long end games.
    """
    game = Game()
    stockfish = Stockfish()
    examples = []
    moves = []
    for _ in range(max_moves):
        stockfish.set_position(moves)
        best_move = stockfish.get_best_move()

        value = _value(stockfish.get_evaluation())
        if best_move:
            examples.append((_truncate_fen(stockfish.get_fen_position()), (best_move[:4], value)))

        if best_move and random.random() > randomness:
            move_alg = best_move
            move_tuple = _from_algebraic(move_alg)
        else:
            move_tuple = random.sample(game.game_legal_moves(), 1)[0]
            move_alg = _to_algebraic(move_tuple)

        if len(move_alg) == 5:
            print('pawn promotion')

        try:
            game.make_move(move_tuple[0], move_tuple[1])
            moves.append(move_alg)
        except ValueError:
            moves[-1] = moves[-1] + 'q'
            print(examples)

        randomness *= randomness_decline

        if game.game_winner():
            break
    db = Connector()
    db.insert_examples(examples, table)


def train(table: str = c.DEFAULT_TABLE, structure: str = c.DEFAULT_STRUCTURE,
          learning_rate: float = c.DEFAULT_LEARNING_RATE, epochs: int = c.DEFAULT_EPOCHS,
          batch_size: int = c.DEFAULT_BATCH_SIZE, matches: int = 10,
          threshold: int = c.DEFAULT_THRESHOLD, data_limit: Optional[int] = 50000) -> None:
    """
    Trains the network with stored example sin the database. Before saving the new weights, the new network simulates
    a series of game vs. the old network, only accepting the new network if a certain number of matches is won.
    
    :param table: Database table were examples were stored with gen_examples(). 
    :param structure: Determines the save folder for the weights of the neural network.
    :param learning_rate: Network learning rate.
    :param epochs: Number of training epochs.
    :param batch_size: Batch size in training.
    :param matches: Number of matches simulated to test the new network
    :param threshold: Minimum difference of wins and losses from the matches to accept the new network.   
    :param data_limit: Number of examples used to train. Examples are drawn uniformly. None for no limit.
    """
    new_net = NNet(learning_rate=learning_rate, epochs=epochs, batch_size=batch_size, structure=structure)
    old_net = NNet(structure=structure)
    db = Connector()
    examples = _df_to_examples(db.get_data(data_limit, table))
    new_net.train(examples)
    score = _match_series(nnet1=new_net, nnet2=old_net, matches=matches)
    _evaluate_score(new_net, score, structure, threshold)


def _match_series(nnet1: NNet, nnet2: NNet, matches: int = 20) -> int:
    score = 0
    for i in range(int(matches / 2)):
        score += _fast_match(nnet1, nnet2)
        score += _fast_match(nnet2, nnet1) * -1
        sys.stdout.write(f'\rmatch: {(i + 1) * 2}/{matches}, score: {score}')
        sys.stdout.flush()
    print('')
    return score


def _fast_match(nnet1: NNet, nnet2: NNet) -> int:
    game = Game()
    for _ in range(160):
        nn = nnet1 if game.state.player == 'white' else nnet2
        move = ai.move_weighted(game.state, nn)
        game.make_move(move[0], move[1])
        if game.state.winner:
            if game.state.winner == 'draw':
                return 0
            else:
                return 1 if game.state.winner == 'white' else -1
    return 0


def _to_algebraic(move: tuple) -> str:
    return "".join((chr(ord('`') + move[0][1] + 1), str(c.ROWS - move[0][0]),
                    chr(ord('`') + move[1][1] + 1), str(c.ROWS - move[1][0])))


def _from_algebraic(algebraic: str) -> tuple:
    alg = list(algebraic)
    return (c.ROWS - int(alg[1]), ord(alg[0]) - 97), (c.ROWS - int(alg[3]), ord(alg[2]) - 97)


def _df_to_examples(df: pd.DataFrame) -> list:
    examples = []
    for entry in df.to_dict('records'):
        state = State(entry['state'])
        move = _from_algebraic(entry['move'])
        value = entry['val']
        examples.append((state, (move, value)))
    return examples


def _evaluate_score(nnet: NNet, score: int, structure: str, threshold: int) -> None:
    if score > threshold:
        nnet.model.save_weights(f'{parent_dir}\\weights\\{structure}\\')
        print(f'new model accepted with score: {score}')
    else:
        print(f'new model rejected with score: {score}')


def _value(evaluation: dict) -> float:
    if evaluation['type'] == 'cp':
        return evaluation['value'] / 100
    else:
        return 100 if evaluation['value'] > 0 else -100


def _truncate_fen(fen_string: str) -> str:
    fen_list = fen_string.split(' ')
    return ' '.join(fen_list[:4])
