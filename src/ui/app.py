from PySide6 import QtWidgets

from .tape_widget import TapeWidget
from ..compiler import Compiler
from ..errors import CorrectorException
from ..vm import Vm


class Window(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.vm = Vm()
        self.compiler = Compiler()

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

        self.go_button.clicked.connect(self.run_command)
        self.commands_input.returnPressed.connect(self.run_command)
        self.reset_button.clicked.connect(self.reset)

        self.go_button.setFixedWidth(30)
        self.reset_button.setFixedWidth(30)

        self.grid = QtWidgets.QGridLayout()
        self.alphabet_box = QtWidgets.QVBoxLayout()
        self.alphabet_group = QtWidgets.QGroupBox('АЛФАВИТ')

        self.tape = TapeWidget(self.vm)

        for lbl in self.alphabet_labels:
            self.alphabet_box.addWidget(lbl)
        self.alphabet_group.setLayout(self.alphabet_box)

        self.grid.addWidget(self.code_input, 0, 1, 3, 3)
        self.grid.addWidget(self.reset_button, 3, 1)
        self.grid.addWidget(self.go_button, 3, 2)
        self.grid.addWidget(self.commands_input, 3, 3)
        self.grid.addWidget(self.alphabet_group, 2, 0, 2, 1)
        self.grid.addWidget(self.tape, 0, 0, 2, 1)

        self.setLayout(self.grid)

    def reset(self):
        self.vm = Vm()
        self.compiler = Compiler()

    def run_command(self):
        command = self.commands_input.text()
        code = self.code_input.toPlainText()

        try:
            bc = self.compiler.compile(code)
            command_bc = self.compiler.compile_one_command(command)

            self.vm.run(bc, command_bc)
            self.tape.update()
        except CorrectorException as e:
            self.error(e)

    def error(self, e):
        if len(e.args) > 1:
            line = e.args[1]
            start = e.args[2]
            end = e.args[3]

            text = self.code_input.toPlainText().splitlines()
            result = '<pre>' + '<br>'.join(text[:line])
            if text[:line]:
                result += '<br>'
            result += text[line][:start] + '<span style="background-color: red;">' + text[line][start:end] + '</span>' + text[line][end:] + '<br>'
            result += '<br>'.join(text[line+1:]) + '</pre>'
            self.code_input.setHtml(result)

        QtWidgets.QMessageBox.critical(
            self,
            "Ошибка",
            e.args[0],
            buttons=QtWidgets.QMessageBox.Ok,
            defaultButton=QtWidgets.QMessageBox.Ok,
        )
        self.code_input.setText(self.code_input.toPlainText())
