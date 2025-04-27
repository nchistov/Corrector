import sys

from PySide6 import QtWidgets

from app import Window

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = Window()
    w.setWindowTitle('Корректор')
    w.resize(600, 400)
    w.show()

    sys.exit(app.exec())
