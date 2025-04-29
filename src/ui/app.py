from PySide6 import QtWidgets


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.code_input = QtWidgets.QTextEdit()
        self.go_button = QtWidgets.QPushButton('GO')
        self.reset_button = QtWidgets.QPushButton('-')
        self.commands_input = QtWidgets.QLineEdit()

        self.alphabet_labels = [QtWidgets.QLabel('ПУСТО 0 1 2 3 4 5 6'),
                                QtWidgets.QLabel('7 8 9 А Б В Г Д Е Ё Ж'),
                                QtWidgets.QLabel('З И Й К Л М Н О П Р'),
                                QtWidgets.QLabel('С Т У Ф Х Ц Я Ш Щ Ъ'),
                                QtWidgets.QLabel('Ы Ь Э Ю Я ПРОБЕЛ -'),
                                QtWidgets.QLabel('+ / * = < > ( ) [ ] {'),
                                QtWidgets.QLabel('} . , ! ? ; : \' " #'),
                                QtWidgets.QLabel('| $ % ~ @')]

        self.grid = QtWidgets.QGridLayout()
        self.alphabet_box = QtWidgets.QVBoxLayout()
        self.alphabet_group = QtWidgets.QGroupBox('АЛФАВИТ')

        for lbl in self.alphabet_labels:
            self.alphabet_box.addWidget(lbl)
        self.alphabet_group.setLayout(self.alphabet_box)

        self.grid.addWidget(self.code_input, 0, 1, 2, 3)
        self.grid.addWidget(self.reset_button, 2, 1)
        self.grid.addWidget(self.go_button, 2, 2)
        self.grid.addWidget(self.commands_input, 2, 3)
        self.grid.addWidget(self.alphabet_group, 1, 0, 2, 1)

        self.setLayout(self.grid)
