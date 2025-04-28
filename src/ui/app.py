from PySide6 import QtWidgets


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.code_input = QtWidgets.QTextEdit()
        self.go_button = QtWidgets.QPushButton('GO')
        self.reset_button = QtWidgets.QPushButton('-')
        self.commands_input = QtWidgets.QLineEdit()

        self.grid = QtWidgets.QGridLayout()

        self.grid.addWidget(self.code_input, 0, 0, 1, 3)
        self.grid.addWidget(self.reset_button, 1, 0)
        self.grid.addWidget(self.go_button, 1, 1)
        self.grid.addWidget(self.commands_input, 1, 2)

        self.setLayout(self.grid)
