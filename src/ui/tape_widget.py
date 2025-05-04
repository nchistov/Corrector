from PySide6 import QtWidgets, QtCore

symbols = [' ', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
           'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З','И', 'Й', 'К',
           'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х',
           'Ц', 'Я', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я', '␣',
           '-', '+', '/', '*', '=', '<', '>', '(', ')', '[', ']', '{', '}', '.',
           ',', '!', '?', ';', ':', '\'', '"', '#', '|', '$', '%', '~', '@']

class TapeWidget(QtWidgets.QWidget):
    def __init__(self, vm, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.vm = vm

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(1)

        self.labels = [QtWidgets.QLabel(' ') for _ in range(11)]

        for i, lbl in enumerate(self.labels):
            if i == 5:
                lbl.setStyleSheet('border: 2px solid;')
            else:
                lbl.setStyleSheet('border: 1px solid;')
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedSize(QtCore.QSize(30, 40))
            self.grid.addWidget(lbl, 1, i)

        self.right_btn = QtWidgets.QPushButton('→')
        self.left_btn = QtWidgets.QPushButton('←')
        self.right_btn.setFixedWidth(30)
        self.left_btn.setFixedWidth(30)

        self.box = QtWidgets.QLabel(' ')
        self.box.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.box.setStyleSheet('border: 4px solid brown;')
        self.box.setFixedSize(QtCore.QSize(60, 60))

        self.grid.addWidget(self.box, 0, 9, 1, 2)
        self.grid.addWidget(self.left_btn, 2, 0)
        self.grid.addWidget(self.right_btn, 2, 10)

        self.setLayout(self.grid)

    def update(self):
        for v, l in zip(self.vm.tape.get_preview(), self.labels):
            l.setText(symbols[v])
        self.box.setText(symbols[vm.box])
