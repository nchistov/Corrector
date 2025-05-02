from PySide6 import QtWidgets, QtCore

symbols = [' ', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
           'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З','И', 'Й', 'К',
           'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х',
           'Ц', 'Я', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я', '␣',
           '-', '+', '/', '*', '=', '<', '>', '(', ')', '[', ']', '{', '}', '.',
           ',', '!', '?', ';', ':', '\'', '"', '#', '|', '$', '%', '~', '@']

class TapeWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.box = QtWidgets.QGridLayout()

        self.labels = [QtWidgets.QLabel(' ') for _ in range(11)]

        for i, lbl in enumerate(self.labels):
            if i == 5:
                lbl.setStyleSheet('border: 2px solid;')
            else:
                lbl.setStyleSheet('border: 1px solid;')
            lbl.setFixedSize(QtCore.QSize(30, 60))
            self.box.addWidget(lbl, 0, i)

        self.right_btn = QtWidgets.QPushButton('')
        self.left_btn = QtWidgets.QPushButton('')
        self.right_btn.setFixedWidth(30)
        self.left_btn.setFixedWidth(30)

        self.box.addWidget(self.left_btn, 1, 0)
        self.box.addWidget(self.right_btn, 1, 10)

        self.setLayout(self.box)

    def update_tape(self, values):
        for v, l in zip(values, self.labels):
            l.setText(symbols[v-1])
