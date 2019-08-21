
"""
file: send.py
socket client
"""

import socket
import threading
import os
import sys
import struct
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import *

class ClientDialog(QtGui.QWidget):

    signalConnect = pyqtSignal()
    signalSend = pyqtSignal()
    signalEnd = pyqtSignal()
    signalError = pyqtSignal()

    def __init__(self):
        super(ClientDialog,self).__init__()
        self.signalConnect.connect(self.showConnect)
        self.signalSend.connect(self.showSend)
        self.signalEnd.connect(self.showEnd)
        self.signalError.connect(self.showError)
        self.initUI();

    def initUI(self):
        label = QtGui.QLabel('fileName')
        review = QtGui.QLabel('client status')

        startBtn = QtGui.QPushButton('startConnect', self)
        sendBtn = QtGui.QPushButton('sendFile',self)

        pb = QtGui.QPushButton()
        pb.setObjectName("browse")
        pb.setText("Browse")

        le = QtGui.QLineEdit()
        reviewEdit = QtGui.QTextEdit()
        self.line = le
        self.review = reviewEdit
        self.review.setReadOnly(True)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(label, 1, 0)
        grid.addWidget(le, 1, 1)
        grid.addWidget(pb,1,2)
        grid.addWidget(startBtn, 8, 2)
        grid.addWidget(sendBtn,2,2)

        grid.addWidget(review, 2, 0)
        grid.addWidget(reviewEdit, 3, 0, 5, 3)

        self.setLayout(grid)
        self.review.setText('')
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('client')
        self.show()

        self.connect(startBtn,QtCore.SIGNAL('clicked()'),self.OnButton)

        self.connect(pb, SIGNAL("clicked()"),self.button_click)

        self.connect(sendBtn,QtCore.SIGNAL('clicked()'),self.OnSend)

    def OnButton(self):
        self.review.setText('start connect')
        threadGo = threading.Thread(target=self.socket_client)
        threadGo.start()

    def button_click(self):
        # absolute_path is a QString object
        absolute_path = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                    '.', "txt files (*.txt)")
        if absolute_path:
            cur_path = QDir('.')
            relative_path = cur_path.relativeFilePath(absolute_path)
            self.line.setText(relative_path)

    def OnSend(self):
        threadSend = threading.Thread(target=self.sendFile)
        threadSend.start()


    def socket_client(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', 6666))
        except socket.error as msg:
            print(msg)
            self.signalError.emit()
            sys.exit(1)
        self.recv = s.recv(1024).decode()
        self.socketReceive = s
        self.signalConnect.emit()

    def sendFile(self):
        while 1:
            filepath = self.line.text().encode()
            #filepath = input('please input file path: ').encode()
            if os.path.isfile(filepath):
                # 定义定义文件信息。128s表示文件名为128bytes长，l表示一个int或log文件类型，在此为文件大小
                fileinfo_size = struct.calcsize('128sl')
                # 定义文件头信息，包含文件名和文件大小
                fhead = struct.pack('128sl', os.path.basename(filepath),
                                    os.stat(filepath).st_size)
                self.socketReceive.send(fhead)
                self.signalSend.emit()
                print('client filepath: {0}'.format(filepath))

                fp = open(filepath, 'rb')
                while 1:
                    data = fp.read(1024)
                    if not data:
                        print('{0} file send over...'.format(filepath))
                        break
                    self.socketReceive.send(data)
            self.socketReceive.close()
            self.signalEnd.emit()
            break

    def showConnect(self):
        self.review.append('')
        self.review.append(self.recv)
        self.review.append('click the Browse to choose file')
    def showSend(self):
        self.review.append('client filepath: {0}'.format(self.line.text()))
    def showEnd(self):
        self.review.append('End sending')
        self.review.append('connect close')
    def showError(self):
        self.review.append('连接失败')

def main():

    app = QtGui.QApplication(sys.argv)
    serverWindow = ClientDialog()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
