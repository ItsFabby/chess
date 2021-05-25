# Chess AI with Neural Network

## About the Project
DeepMind's [AlphaZero](https://deepmind.com/blog/article/alphazero-shedding-new-light-grand-games-chess-shogi-and-go) revolutionized the world of chess in 2017 by creating a neural network that learned chess all by itself and being able to beat the top engines at the time. To train and run the network, the team had access to Google's supercomputer infrastructure. 

This project trains a neural network on a standard home computer, by scaling down the structure of the network and using supervised learning with examples generated from Stockfish.

## Build With
- [Tensorflow](https://www.tensorflow.org/)
- [Stockfish](https://stockfishchess.org/)
- [MySQL](https://www.mysql.com/)

## Getting Started
- Install the prerequisites listed in `requirement.txt`

Playing against the pretrained network:
  - Run `__main__.py` with a Python interpreter.
  
Training a network:
  - Install [Stockfish](https://stockfishchess.org/) and set up the correct path in `core/constants.py`.
  - Set up a [MySQL](https://www.mysql.com/) database and adjust the login credentials in `core/constants.py`.
  - Generate training data using `gen_examples()` in `core/trainer.py`.
  - Train the network using `train()` in `core/trainer.py`.
  
  Make sure to change `model_name` when training a new network (either by giving a keyword argument or by changing the default in `core/constants.py`), otherwise the old weights will be overwritten! \
  Feel free to change the structure of the network in `core/neural_network.py`.

## License
Distributed under the MIT License. See `LICENSE` for more information.
