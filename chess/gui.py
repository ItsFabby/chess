import tkinter as tk
# from threading import Thread
from PIL import Image, ImageTk

import math

from chess.game import Game
from chess import constants as c


class GUI(tk.Frame):
    def __init__(self):
        super().__init__()
        self.game = Game()
        self.images = self.import_images()

        self.selected = None
        self.legal_moves = self.game.game_legal_moves()

        """GUI elements"""
        self.header = tk.Label(self)
        self.header.grid(row=0, column=0)

        self.board = tk.Canvas(self, borderwidth=0, highlightthickness=0,
                               width=c.COLUMNS * c.SQUARE_SIZE, height=c.ROWS * c.SQUARE_SIZE)
        self.board.grid(row=1, column=0, padx=2, pady=2)

        self.restart_button = tk.Button(self, text='Restart game', command=self.restart)
        self.restart_button.grid(row=3, column=0)

        self.pack()

        """Bind"""
        self.board.bind('<Button-1>', self.move_event)
        self.redraw()
        self.update_header()
        self.mainloop()

    def restart(self):
        self.game = Game()
        self.board.delete('highlight')
        self.game.player = 'white'
        self.selected = None
        self.legal_moves = self.game.game_legal_moves()
        self.redraw()
        self.update_header()
        self.check_ai()

    def move_event(self, event):
        if self.game.winner:
            return
        if self.selected:
            target_pos = self.coords_to_grid(event.x, event.y)
            if self.selected == target_pos:
                self.board.delete('highlight')
                self.redraw()
                self.selected = None
                return

            if (self.selected, target_pos) in self.legal_moves:
                self.game.make_move(self.selected, target_pos)
                self.legal_moves = self.game.game_legal_moves()
                self.update_header()

                self.selected = None
                self.board.delete('highlight')
                self.redraw()
                return
        self.board.delete('highlight')
        self.redraw()
        self.selected = None

        select_pos = self.coords_to_grid(event.x, event.y)
        piece = self.game.state_entry(self.game.state, select_pos)
        if not (self.game.player == 'white' and piece in c.WHITE_PIECES) and not (
                self.game.player == 'black' and piece in c.BLACK_PIECES):
            self.board.delete('highlight')
            self.redraw()
            return
        if self.highlight_legal_moves(select_pos):
            self.selected = select_pos
            self.highlight_square('lightblue', select_pos)
        self.redraw()

    @staticmethod
    def coords_to_grid(x, y):
        column = math.floor(x / c.SQUARE_SIZE)
        row = math.floor(y / c.SQUARE_SIZE)
        return row, column

    def is_nnet(self, player):
        return False
        # if player == 1:
        #     return self.game.player1.get() == 'Neural Network'
        # else:
        #     return self.game.player2.get() == 'Neural Network'

    def check_ai(self):
        return
        # self.update_header()
        # if self.is_nnet(self.game.player) and not self.game.finished:
        #     Thread(target=self.ai_move).start()

    def ai_move(self):
        return
        # self.game.make_move(self.game.decide_move('nnet', iterations=self.difficulty.get()))
        # self.redraw()
        # self.check_ai()

    def update_header(self):
        if self.game.winner == 'draw':
            self.header.config(text="Stalemate: It's a draw!")
            return
        if self.game.winner:
            self.header.config(text=f"{'White' if self.game.winner == 'white' else 'Black'} won!")
            return
        self.header.config(text=f"{'White' if self.game.player == 'white' else 'Black'}'s turn: "
                                f"{'The AI is calculating.' if self.is_nnet(self.game.player) else 'Make a move!'}"
                           )

    # else:
    #     self.header.config(text=f"{'Red' if self.game.winner == 1 else 'Blue'} has won!")

    def redraw(self):
        self.board.delete('square')
        self.board.delete('piece')
        color = c.COLOR2
        for row in range(c.ROWS):
            color = c.COLOR1 if color == c.COLOR2 else c.COLOR2
            for column in range(c.COLUMNS):
                x1 = (column * c.SQUARE_SIZE)
                y1 = ((c.ROWS - row - 1) * c.SQUARE_SIZE)
                x2 = x1 + c.SQUARE_SIZE
                y2 = y1 + c.SQUARE_SIZE
                self.board.create_rectangle(x1, y1, x2, y2, outline="black", tags="square", fill=color)
                color = c.COLOR1 if color == c.COLOR2 else c.COLOR2

                piece = self.game.state_entry(self.game.state, (row, column))
                if piece != 'empty':
                    image_x, image_y = self.get_position(row, column)
                    self.board.create_image(image_x, image_y, image=self.images[piece], tags='piece', anchor='c')
        self.board.tag_raise('highlight')
        self.board.tag_raise('piece')

    def highlight_square(self, color, position):
        row, column = position[0], position[1]
        x0 = (column * c.SQUARE_SIZE) + 1
        x1 = (column + 1) * c.SQUARE_SIZE
        y0 = (row * c.SQUARE_SIZE) + 1
        y1 = (row + 1) * c.SQUARE_SIZE
        self.board.create_rectangle(x0, y0, x1, y1, fill=color, tags='highlight', outline="")

    def highlight_legal_moves(self, position):
        move_exists = False
        for move in self.legal_moves:
            if move[0] == position:
                self.highlight_square('red', move[1])
                move_exists = True
        return move_exists

    @staticmethod
    def get_position(row, column):
        y = row * c.SQUARE_SIZE + int(c.SQUARE_SIZE / 2)
        x = column * c.SQUARE_SIZE + int(c.SQUARE_SIZE / 2)
        return x, y

    @staticmethod
    def import_images():
        return {
            piece_type:
                ImageTk.PhotoImage(Image.open(f"images/{piece_type}.png").resize((c.SQUARE_SIZE, c.SQUARE_SIZE)))
            for piece_type in (c.WHITE_PIECES + c.BLACK_PIECES)
        }


if __name__ == '__main__':
    gui = GUI()
