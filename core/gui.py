import tkinter as tk
from threading import Thread
from PIL import Image, ImageTk
import copy
import time
import math
from typing import Any, Tuple
import os

from game import Game
from neural_network import NNet
import constants as c
import ai

image_dir = f'{os.path.dirname(os.path.abspath(__file__))}\\images'


class GUI(tk.Frame):
    def __init__(self, fen_position: str = c.DEFAULT_POSITION):
        super().__init__()
        self.game = Game(fen_position)
        start = time.time()
        self.nn = NNet()
        print('loading nn takes: ', time.time() - start)
        self.images = self._import_images()

        self.selected = None
        self.legal_moves = self.game.game_legal_moves()
        self.ai_lock = False

        """GUI elements"""
        self.header = tk.Label(self)
        self.header.grid(row=0, column=0)

        self.board = tk.Canvas(self, borderwidth=0, highlightthickness=0,
                               width=c.COLUMNS * c.SQUARE_SIZE, height=c.ROWS * c.SQUARE_SIZE)
        self.board.grid(row=1, column=0, padx=2, pady=2)

        self.restart_button = tk.Button(self, text='Restart game', command=self._restart)
        self.restart_button.grid(row=3, column=0)

        self.player_selection = tk.Frame(self)
        self.player_selection.grid(row=4, column=0)

        self.player1 = tk.StringVar(self)
        self.player1.set('Human')
        self.player1_label = tk.Label(self.player_selection, text='White: ')
        self.player1_label.grid(row=0, column=0)
        self.player1_box = tk.OptionMenu(self.player_selection, self.player1, *['Human', 'Neural Network'],
                                         command=self._option_trigger)
        self.player1_box.grid(row=0, column=1)

        self.player2 = tk.StringVar(self)
        self.player2.set('Neural Network')
        self.player2_label = tk.Label(self.player_selection, text='Black: ')
        self.player2_label.grid(row=0, column=3)
        self.player2_box = tk.OptionMenu(self.player_selection, self.player2, *['Human', 'Neural Network'],
                                         command=self._option_trigger)
        self.player2_box.grid(row=0, column=4)

        self.pack()

        """Bind"""
        self.board.bind('<Button-1>', self._move_event)
        self._draw_board()
        self._update_header()
        self.mainloop()

    def _option_trigger(self, _event) -> None:
        # overwriting the current game to prevent still ongoing threads from interacting
        state = copy.deepcopy(self.game.state)
        self.game = Game()
        self.game.state = state

        self._check_ai()

    def _restart(self) -> None:
        self.game = Game()
        self.board.delete('highlight')
        self.game.player = 'white'
        self.selected = None
        self.legal_moves = self.game.game_legal_moves()
        self._update_board()
        self._update_header()
        self._check_ai()

    def _move_event(self, event: Any) -> None:
        if self.game.state.winner or self._is_nnet(self.game.state.player):
            return
        if self.selected:
            target_pos = self._coords_to_grid(event.x, event.y)
            if self.selected == target_pos:
                self.board.delete('highlight')
                self._update_board()
                self.selected = None
                return

            if (self.selected, target_pos) in self.legal_moves:
                self.game.make_move(self.selected, target_pos)
                self._highlight_last_move(self.selected, target_pos)
                self.legal_moves = self.game.game_legal_moves()
                self._update_header()

                self.selected = None
                self.board.delete('highlight')
                self._update_board()
                self._check_ai()
                return
        self.board.delete('highlight')
        self._update_board()
        self.selected = None

        select_pos = self._coords_to_grid(event.x, event.y)
        piece = self.game.state.entry(select_pos)
        if not (self.game.state.player == 'white' and piece in c.WHITE_PIECES) and not (
                self.game.state.player == 'black' and piece in c.BLACK_PIECES):
            self.board.delete('highlight')
            self._update_board()
            return
        if self._highlight_legal_moves(select_pos):
            self.selected = select_pos
            self._highlight_square('orange red', select_pos, 'highlight')
        self._update_board()

    @staticmethod
    def _coords_to_grid(x: float, y: float) -> Tuple[int, int]:
        column = math.floor(x / c.SQUARE_SIZE)
        row = math.floor(y / c.SQUARE_SIZE)
        return row, column

    def _is_nnet(self, player: str) -> bool:
        if player == 'white':
            return self.player1.get() == 'Neural Network'
        else:
            return self.player2.get() == 'Neural Network'

    def _check_ai(self) -> None:
        self._update_header()
        if self._is_nnet(self.game.state.player) and not self.game.state.winner:
            if self.ai_lock:
                return
            self.ai_lock = True
            Thread(target=self._ai_move).start()

    def _ai_move(self) -> None:
        start = time.time()
        # move = ai.move_max(self.game.state, self.nn)
        move = ai.fast_tree_search(self.game.state, self.nn, 2, 2)
        print('Calculating move took ', time.time() - start)
        if move in self.legal_moves:
            self.game.make_move(move[0], move[1])
            self._highlight_last_move(move[0], move[1])
        self.legal_moves = self.game.game_legal_moves()
        self._update_board()
        self.ai_lock = False
        time.sleep(0)
        self._check_ai()

    def _update_header(self) -> None:
        if self.game.state.winner == 'draw':
            self.header.config(text="It's a draw!")
            return
        if self.game.state.winner:
            self.header.config(text=f"{'White' if self.game.state.winner == 'white' else 'Black'} won!")
            return
        self.header.config(
            text=f"{'White' if self.game.state.player == 'white' else 'Black'}'s turn: "
                 f"{'The AI is calculating.' if self._is_nnet(self.game.state.player) else 'Make a move!'}"
        )

    def _draw_board(self) -> None:
        self.board.delete('square')
        color = c.COLOR2
        for row in range(c.ROWS):
            if c.ROWS % 2 == 0:
                color = c.COLOR1 if color == c.COLOR2 else c.COLOR2
            for column in range(c.COLUMNS):
                x1 = (column * c.SQUARE_SIZE)
                y1 = ((c.ROWS - row - 1) * c.SQUARE_SIZE)
                x2 = x1 + c.SQUARE_SIZE
                y2 = y1 + c.SQUARE_SIZE
                self.board.create_rectangle(x1, y1, x2, y2, outline="black", tags="square", fill=color)
                color = c.COLOR1 if color == c.COLOR2 else c.COLOR2
        self._update_board()

    def _update_board(self) -> None:
        self.board.delete('piece')
        for row in range(c.ROWS):
            for column in range(c.COLUMNS):
                piece = self.game.state.entry((row, column))
                if piece != 'empty':
                    image_x, image_y = self._get_position(row, column)
                    self.board.create_image(image_x, image_y, image=self.images[piece], tags='piece', anchor='c')
        self.board.tag_raise('highlight')
        self.board.tag_raise('piece')

    def _highlight_square(self, color: str, position: tuple, tag: str) -> None:
        row, column = position[0], position[1]
        x0 = (column * c.SQUARE_SIZE) + 1
        x1 = (column + 1) * c.SQUARE_SIZE
        y0 = (row * c.SQUARE_SIZE) + 1
        y1 = (row + 1) * c.SQUARE_SIZE
        self.board.create_rectangle(x0, y0, x1, y1, fill=color, tags=tag, outline="")

    def _highlight_legal_moves(self, position: tuple) -> bool:
        move_exists = False
        for move in self.legal_moves:
            if move[0] == position:
                self._highlight_square('light coral', move[1], 'highlight')
                move_exists = True
        return move_exists

    def _highlight_last_move(self, origin_pos: tuple, target_pos: tuple) -> None:
        self.board.delete('last_move')
        self._highlight_square('steel blue', origin_pos, 'last_move')
        self._highlight_square('sky blue', target_pos, 'last_move')

    @staticmethod
    def _get_position(row: int, column: int) -> tuple:
        y = row * c.SQUARE_SIZE + int(c.SQUARE_SIZE / 2)
        x = column * c.SQUARE_SIZE + int(c.SQUARE_SIZE / 2)
        return x, y

    @staticmethod
    def _import_images():
        return {
            piece_type:
                ImageTk.PhotoImage(Image.open(f'{image_dir}\\{piece_type}.png').resize((c.SQUARE_SIZE, c.SQUARE_SIZE)))
            for piece_type in (c.WHITE_PIECES + c.BLACK_PIECES)
        }


if __name__ == '__main__':
    gui = GUI()
