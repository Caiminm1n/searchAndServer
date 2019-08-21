from getTFIDF import TFIDF
import urllib.request
from bs4 import BeautifulSoup as BS
from bs4 import UnicodeDammit
import sys
from PyQt5 import QtCore,QtGui, QtWidgets
import jieba
import re
import threading


__author__ = 'PC'


class htmlDownloader(object):
    ##html页面的下载器 负责html的下载
    def __init__(self):
        self.header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}

    #自带一个header
    def getHtml(self, url):
        req = urllib.request.Request(url=url, headers=self.header_dict)

        try:
            response = urllib.request.urlopen(req, timeout=10).read()
            cod = UnicodeDammit(response)
            coding =cod.original_encoding
            print("url:",url,",coding:",coding)
            html = response.decode(coding,'ignore')
            return html
        except:
            print("网页下载失败！")
            return None


class urlManager(object):
    ##管理url
    def __init__(self):
        self.urlPool = []

    def addUrl(self, url):
        if url not in self.urlPool and url is not None:
            self.urlPool.append(url)
            print("一条url添加完毕!")

    def addUrls(self, urls):
        for url in urls:
            self.addUrl(url)

    def getUrlPool(self):
        return self.urlPool

    def clearUrlPool(self):
        self.urlPool = []


class parseHtml(object):
    def __init__(self):
        pass

    def getUrls(self, html):
        ##得到网页中的url
        try:
            url = []
            soup = BS(html, "html5lib")
            divNodes = soup.find_all("div", "result")

            if divNodes is None:
                return None
            for divNode in divNodes:
                aNode = divNode.find("a")
                url.append(aNode["href"])
        except:
            print("网页下载失败!")
            return None
        return url

    def getText(self, html):
        text = ""
        adv = ["分享", "朋友圈", "空间", "微信", "原标题", "客服热线", "责编", "All Rights Reserved","版权所有" ]
        print('开始')
        soup = BS(html, "html5lib")
        print('结束')
        try:
            pNodes = soup.find_all("p")
            if pNodes == None:
                return None

            for pNode in pNodes:
                if pNode.find("a") == None and pNode.parent.name != "a":
                    text1 = pNode.get_text()
                    for ads in adv:
                        if ads in text1:
                            text1 = ''
                            break
                    text = text + text1 + '\n'
        except:
            return None
        return text


class urlTextManager(object):
    ##管理url text键值对
    def __init__(self):
        self.pool = {}#dict

    def addUrlText(self, url, text):
        self.pool[url] = text
        print("加入一对url:text")

    def getPool(self):
        return self.pool


class spider(object):
    ##爬取
    def __init__(self, kws):
        self.pH = parseHtml()
        self.hD = htmlDownloader()#dict header
        self.uTM = urlTextManager()#dict urlPool
        self.uM = urlManager()#list urlPool

        self.action = "http://news.baidu.com/ns?cl=2&ct=1&tn=news&rn=20&ie=utf-8&bt=0&et=0&word="
        i = 0
        for kw in kws:
            if i == 0:
                self.action = self.action + urllib.request.quote(kw)#对kw编码
            else:
                self.action = self.action + "+" + urllib.request.quote(kw)
        self.action += "&pn="#page
        a = self.action
        print(a)

    def getUrl(self, url):
        html = self.hD.getHtml(url)
        urls = self.pH.getUrls(html)
        return urls


    def getUrls(self):
        id = 0
        lenUrlPool = 0
        while id < 3 or lenUrlPool <60:
            url = self.action
            url += str(id * 20)
            newUrls = self.getUrl(url)
            self.uM.addUrls(newUrls)
            id += 1
            lenUrlPool = len(self.uM.getUrlPool())
        print(lenUrlPool)
        return self.uM.getUrlPool()


    def getResult(self):
        urls = self.getUrls()
        print("urls=", urls)
        if urls:
            for url in urls:
                if 'qq' in url and 'htm' in url:
                    continue
                try:
                    print(url)
                    headers = ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')
                    opener = urllib.request.build_opener()
                    opener.addheaders=[headers]
                    response = opener.open(url, timeout=10).read()
                    cod = UnicodeDammit(response)
                    coding = cod.original_encoding
                    print("url:", url, ",coding:", coding)
                    if coding:
                        if coding == 'windows-1252':
                            html = response.decode('GB2312','ignore')
                        else:
                            html = response.decode(coding,'ignore')
                        text=self.pH.getText(html)
                    else:
                        print('No encoding')
                        continue
                except:
                    continue
                self.uTM.addUrlText(url, text)
        return self.uTM.getPool()


def main_word(allnum, keyword, dict):  # 参数分别是（总文章数，关键词列表， URL:TEXT文章）
    count_word = {}
    dict_text = {}
    TFIDF_dict = {}
    data = []
    # data = keyword
    for word in keyword:
        data.append((' '.join(jieba.cut_for_search(word))).split(' '))#以空格将分词隔开，再用split函数将其分成不同list
    keyword = []
    for wordlist in data:
        for word in wordlist:
            keyword.append(word)
    print('关键词分词以后的数据：', data)
    print(keyword)
    print('\n')
    for word in keyword:
        count_word[word] = 0
    for url, text in dict.items():
        # 计算每篇文章的关键字频率，存储，并统计关键字文章数
        data = TFIDF.jf_word(text)
        freq_word = TFIDF.frequence_word(keyword, data)
        for key, freq in freq_word.items():
            if (freq != 0):
                count_word[key] = count_word[key] + 1
        dict_text[url] = freq_word
    for url, freq_dict in dict_text.items():
        TFIDF_dict[url] = TFIDF.get_TFIDF(allnum, freq_dict, count_word)
    array = sorted(TFIDF_dict.items(), key=lambda e: e[1], reverse=True)
    return list(array)  # 返回按TFIDF值大到小排序的（网址，TFIDF）对


class searchWindow(QtWidgets.QWidget):
    signalSearch = QtCore.pyqtSignal()

    def __init__(self):
        super(searchWindow, self).__init__()
        self.signalSearch.connect(self.showResult)
        self.initUI()

    def initUI(self):

        label = QtWidgets.QLabel('新闻网络爬虫')
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setFont(QtGui.QFont("Roman times",28))
        review = QtWidgets.QLabel('搜索结果')


        self.btn = QtWidgets.QPushButton('开始搜索', self)

        le = QtWidgets.QLineEdit()
        reviewEdit = QtWidgets.QTextEdit()
        self.line = le
        self.review = reviewEdit
        self.review.setReadOnly(True)

        reviewEdit.setStyleSheet(
            "font:20pt '楷体';border-width: 1px;border-style: solid;border-color: rgb(255, 0, 0);")


        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(label, 0, 0)
        grid.addWidget(le, 2, 0)
        grid.addWidget(self.btn, 2, 2)

        grid.addWidget(review, 3, 0)
        grid.addWidget(reviewEdit, 4, 0, 5, 2)

        self.setLayout(grid)
        self.review.setText('')
        self.setGeometry(300, 300, 650, 600)
        self.setWindowTitle('爬虫搜索')
        self.show()
        self.line.returnPressed.connect(self.OnButton)
        self.btn.clicked.connect(self.OnButton)  # btn按钮 的clicked()时间 信号 绑定到addNum这个函数 也叫槽

    def OnButton(self):
        self.btn.setEnabled(False)
        threadGo = threading.Thread()
        skw = self.line.text()  # 获取文本框内容

        keywordList = re.split(r'[；，,;\s]', skw)
        strkey = re.split(r'[；，,;\s]', skw)
        print('关键字', strkey)
        if self.review.toPlainText() != '正在搜索中，请稍后...':
            self.review.setText('正在搜索中，请稍后...')
            threadGo.__init__(target=self.searchPage, args=(strkey, keywordList))
            threadGo.start()

    def searchPage(self, strkey, keywordList):
        s = spider(strkey)
        # print(skw)#在文本框输出传入的数据
        self.dct = s.getResult()
        print('文本下载完毕-----------------', self.dct)

        self.resultList = main_word(len(self.dct), keywordList, self.dct)
        print('tfidf----------', self.resultList)
        print('文本---------', self.dct)

        self.signalSearch.emit()#发出更新UI信号

    def showResult(self):
        print('收到信号--------------')
        self.review.setText('')
        for item in self.resultList:
            font = QtGui.QFont()
            font.setPointSize(10)
            font.setFamily("Arial")
            self.review.setCurrentFont(font)

            self.review.append('url:' + item[0])

            font.setBold(True)
            self.review.setCurrentFont(font)

            self.review.append('TF-IDF:' + str(item[1]))

            font.setPointSize(9)
            font.setFamily('楷体')
            font.setBold(False)

            self.review.setCurrentFont(font)
            self.review.append(self.dct[item[0]])
            self.review.append('\n')
            self.review.verticalScrollBar().setValue(self.review.verticalScrollBar().minimum())
            self.btn.setEnabled(True)


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = searchWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
