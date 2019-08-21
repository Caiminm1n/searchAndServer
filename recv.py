
"""
file: recv.py
socket service
"""


import socket
import threading
import time
import sys
import os
import struct
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import *


class ServerDialog(QtGui.QWidget):

    signalStartServer = pyqtSignal()
    signalConnect = pyqtSignal()
    signalRecv = pyqtSignal()
    signalEnd = pyqtSignal()

    def __init__(self):
        super(ServerDialog,self).__init__()
        self.signalStartServer.connect(self.showResult)
        self.signalConnect.connect(self.showConnect)
        self.signalRecv.connect(self.showRecv)
        self.signalEnd.connect(self.showEnd)
        self.initUI()

    def initUI(self):
        review = QtGui.QLabel('server status')

        startBtn = QtGui.QPushButton('startServer', self)
        endBtn = QtGui.QPushButton('endServer', self)

        reviewEdit = QtGui.QTextEdit()

        self.review = reviewEdit
        self.review.setReadOnly(True)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(startBtn, 8, 3)
        grid.addWidget(endBtn, 8, 1)

        grid.addWidget(review, 1, 2)
        grid.addWidget(reviewEdit, 3, 1, 5, 3)

        self.setLayout(grid)
        self.review.setText('')
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('server')
        self.show()

        self.connect(startBtn,QtCore.SIGNAL('clicked()'),self.OnButton)
        self.connect(endBtn, QtCore.SIGNAL('clicked()'), self.OnEnd)

    def OnButton(self):
        self.review.setText('开启服务中')
        threadGo = threading.Thread(target=self.server_socket)
        threadGo.start()

    def OnEnd(self):
        self.s.close()
        self.review.append('end server')


    def server_socket(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind(('127.0.0.1', 6666))
            self.s.listen(10)
        except socket.error as msg:
            print('启动失败')
            sys.exit(1)
        self.signalStartServer.emit()
        while 1:
            conn, addr = self.s.accept()
            t = threading.Thread(target=self.deal_data, args=(conn, addr))
            t.start()



    def deal_data(self,conn, addr):
        self.address = addr
        self.signalConnect.emit()
        #conn.settimeout(500)

        conn.send('Hi, Welcome to the server!'.encode())

        while 1:
            fileinfo_size = struct.calcsize('128sl')
            buf = conn.recv(fileinfo_size)
            if buf:
                filename, self.filesize = struct.unpack('128sl', buf)
                print(type(filename))
                print(filename)
                fn = filename.decode().strip('\00')
                self.new_filename = os.path.join('./', 'new_' + fn)
                self.signalRecv.emit()

                recvd_size = 0  # 定义已接收文件的大小
                fp = open(self.new_filename, 'wb')
                print('start receiving...')

                while not recvd_size == self.filesize:
                    if self.filesize - recvd_size > 1024:
                        data = conn.recv(1024)
                        recvd_size += len(data)
                    else:
                        data = conn.recv(self.filesize - recvd_size)
                        recvd_size = self.filesize
                    fp.write(data)
                fp.close()
                print('end receive...')
                self.signalEnd.emit()
            conn.close()
            break

    def showResult(self):
        print('收到信号--------------')
        self.review.setText('waiting connection')

    def showConnect(self):
        self.review.append('')
        self.review.append('Accept new connection from {0}'.format(self.address))

    def showRecv(self):
        self.review.append('file new name is {0}, filesize is {1},from{2}'.format(self.new_filename,
                                                                    self.filesize,self.address))
        self.review.append('start receiving')

    def showEnd(self):
        self.review.append('End receiving')
        self.review.append('connect close')

def main():

    app = QtGui.QApplication(sys.argv)
    serverWindow = ServerDialog()
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()
