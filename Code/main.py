"""
main.py

Requirements
------------
    pip install customtkinter matplotlib openpyxl
"""

import sys
import os

# Ensure the Code directory is on the path so all imports resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from gui import MainWindow


def main() -> None:
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
