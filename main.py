#!/usr/bin/env python
import tkinter as tk
from src.ui.main_window import MainWindow

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.geometry("900x700")
    root.minsize(600, 400)
    root.mainloop()

if __name__ == "__main__":
    main()
