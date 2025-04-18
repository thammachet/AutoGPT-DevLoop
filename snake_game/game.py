import tkinter as tk
import random

CELL_SIZE = 20
GRID_WIDTH = 20
GRID_HEIGHT = 20
DELAY = 100  # milliseconds

class SnakeGame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid()
        self.direction = 'Right'
        self.snake = [(5, 5), (4, 5), (3, 5)]
        self.food = None
        self.score = 0
        self.running = True

        self.canvas = tk.Canvas(self, width=CELL_SIZE*GRID_WIDTH, height=CELL_SIZE*GRID_HEIGHT, bg='black')
        self.canvas.grid(row=0, column=0)
        self.master.bind('<KeyPress>', self.on_key_press)
        self.place_food()
        self.after(DELAY, self.game_step)

    def place_food(self):
        while True:
            food = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if food not in self.snake:
                self.food = food
                break

    def on_key_press(self, event):
        key = event.keysym
        opposites = {'Left': 'Right', 'Right': 'Left', 'Up': 'Down', 'Down': 'Up'}
        if key in opposites and opposites[key] != self.direction:
            self.direction = key

    def game_step(self):
        if not self.running:
            return
        x, y = self.snake[0]
        if self.direction == 'Left':
            x -= 1
        elif self.direction == 'Right':
            x += 1
        elif self.direction == 'Up':
            y -= 1
        elif self.direction == 'Down':
            y += 1
        new_head = (x, y)

        if (x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT or new_head in self.snake):
            self.running = False
            self.draw()
            self.canvas.create_text(CELL_SIZE*GRID_WIDTH//2, CELL_SIZE*GRID_HEIGHT//2, text='Game Over', fill='red', font=('Arial', 24))
            return

        self.snake = [new_head] + self.snake
        if new_head == self.food:
            self.score += 1
            self.place_food()
        else:
            self.snake.pop()
        self.draw()
        self.after(DELAY, self.game_step)

    def draw(self):
        self.canvas.delete('all')
        # Draw snake
        for x, y in self.snake:
            self.canvas.create_rectangle(x*CELL_SIZE, y*CELL_SIZE, (x+1)*CELL_SIZE, (y+1)*CELL_SIZE, fill='green')
        # Draw food
        fx, fy = self.food
        self.canvas.create_oval(fx*CELL_SIZE, fy*CELL_SIZE, (fx+1)*CELL_SIZE, (fy+1)*CELL_SIZE, fill='red')
        # Draw score
        self.canvas.create_text(40, 10, text=f'Score: {self.score}', fill='white', font=('Arial', 12))
