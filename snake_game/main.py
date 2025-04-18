import tkinter as tk
from game import SnakeGame


def main():
    root = tk.Tk()
    root.title('Snake Game')
    app = SnakeGame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
