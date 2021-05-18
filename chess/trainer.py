from stockfish import Stockfish
import random
# from typing import Optional, Dict, Tuple
import sys
import pandas as pd

from chess.game import Game, State
from chess.db_connector import Connector
from chess import constants as c
from chess.neural_network import NNet


def gen_examples(randomness=0.7, randomness_decline=0.95, max_moves=80, table=c.DEFAULT_TABLE) -> None:
    """
    Generates training examples using Stockfish and stores them in a database in algebraic notation.
    :param table: table the data is stored in
    :param randomness: Probability
    :param randomness_decline:
    :param max_moves:
    :return:
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
            examples.append((stockfish.get_fen_position(), (best_move, value)))

        if best_move and random.random() > randomness:
            move_alg = best_move
            move_tuple = _from_algebraic(move_alg)
        else:
            move_tuple = random.sample(game.game_legal_moves(), 1)[0]
            move_alg = _to_algebraic(move_tuple)

        moves.append(move_alg)
        game.make_move(move_tuple[0], move_tuple[1])
        randomness *= randomness_decline

        if game.game_winner():
            break
    db = Connector()
    db.insert_examples(examples, table)


def train(table=c.DEFAULT_TABLE, structure=c.DEFAULT_STRUCTURE, matches=10,
          threshold=c.DEFAULT_THRESHOLD, learning_rate=c.DEFAULT_LEARNING_RATE, epochs=c.DEFAULT_EPOCHS,
          batch_size=c.DEFAULT_BATCH_SIZE, data_limit=600000):
    new_net = NNet(learning_rate=learning_rate, epochs=epochs, batch_size=batch_size, structure=structure)
    old_net = NNet(structure=structure)
    db = Connector()
    examples = _df_to_examples(db.get_data(data_limit, table))
    new_net.train(examples)
    score = match_series(nnet1=new_net, nnet2=old_net, matches=matches)
    _evaluate_score(new_net, score, structure, threshold)


def match_series(nnet1, nnet2, matches=20) -> int:
    score = 0
    for i in range(int(matches / 2)):
        score += fast_match(nnet1, nnet2)
        score += fast_match(nnet2, nnet1) * -1
        sys.stdout.write(f'\rmatch: {(i + 1) * 2}/{matches}, score: {score}')
        sys.stdout.flush()
    print('')
    return score


def fast_match(nnet1, nnet2) -> int:
    game = Game()
    for _ in range(160):
        if game.state.player == 'white':
            policy = nnet1.prediction(state=game.state)[0]
        else:
            policy = nnet2.prediction(state=game.state)[0]
        moves = list(policy.keys())
        weights = list(policy.values())
        move = random.choices(moves, weights=weights)[0]
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
        nnet.model.save_weights(f'weights/{structure}/')
        print(f'new model accepted with score: {score}')
    else:
        print(f'new model rejected with score: {score}')


def _value(evaluation: float) -> float:
    if evaluation['type'] == 'cp':
        return evaluation['value'] / 100
    else:
        return 100 if evaluation['value'] > 0 else -100


if __name__ == '__main__':
    # while True:
    #     try:
    #         gen_examples()
    #     except ValueError:
    #         print('RIP stockfish')
    while True:
        train(data_limit=50000, epochs=1, learning_rate=0.001, batch_size=512, matches=10, threshold=-1)
