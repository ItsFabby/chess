# position in FEN notation
DEFAULT_POSITION = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
EMPTY_BOARD = '8/8/8/8/8/8/8/8 w - -'
NINE_TIMES_NINE = 'rnbqkqbnr/ppppppppp/9/9/9/9/9/PPPPPPPPP/RNBQKQBNR w KQkq - 0 1'

WHITE_PIECES = ['white_pawn', 'white_knight', 'white_bishop', 'white_rook', 'white_queen', 'white_king']
BLACK_PIECES = ['black_pawn', 'black_knight', 'black_bishop', 'black_rook', 'black_queen', 'black_king']

COLUMNS = 8
ROWS = 8

SQUARE_SIZE = 64
COLOR1 = '#b58863'
COLOR2 = '#f0d9b5'

"""Neural Network"""
DEFAULT_MODEL_NAME = 'model0'

ALPHA_SIGMOID = 0.4

"""Training"""
DEFAULT_LEARNING_RATE = 0.00003
DEFAULT_BATCH_SIZE = 256
DEFAULT_EPOCHS = 1
DEFAULT_THRESHOLD = 0
DEFAULT_TRAINING_NOISE = 0.5

"""Database"""
DEFAULT_TABLE = 'training_data0'

HOST_NAME = 'localhost'
USER_NAME = 'root'
PASSWORD = 'password'
DATABASE = 'chess'
