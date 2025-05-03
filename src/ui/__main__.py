import sys

from PySide6 import QtWidgets

from .app import Window

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet('''
    QLabel {
        font-size: 15pt;
        font-family: monospace;
    }
    QTextEdit {
        font-size: 12pt;
        font-family: monospace;
    }
    QLineEdit {
        font-size: 12pt;
        font-family: monospace;
    }
    QPushButton {
        font-family: monospace;
    }''')

    w = Window()
    w.setWindowTitle('Корректор')
    w.resize(800, 500)
    w.show()

    sys.exit(app.exec())
