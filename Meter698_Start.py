import UI_Meter698, sys, serial, serial.tools.list_ports, threading, Meter698_core, time, UI_Meter698_config, \
    configparser, os
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QTableWidgetItem, QHeaderView,QFileDialog
from PyQt5.QtCore import pyqtSignal
from Comm import makestr, get_list_sum
from binascii import b2a_hex, a2b_hex
from traceback import print_exc


class MainWindow(QMainWindow):
    __switch = pyqtSignal(str)
    _signal_text = pyqtSignal(str)

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = UI_Meter698.Ui_MainWindow()
        self.ui.setupUi(self)
        self.addItem = self.GetSerialNumber()
        self.addItem.sort()
        self.load_ini()
        self.Connect = Connect()
        for addItem in self.addItem:
            self.ui.comboBox.addItem(addItem)
        self.setFixedSize(self.width(), self.height())
        self.ui.pushButton.clicked.connect(self.serial_prepare)
        self._signal_text.connect(self.Warming_message)
        self.config = Config()
        self.ui.toolButton.clicked.connect(self.config.show)
        self.__switch.connect(self.Show_Hidden)

    def load_ini(self):
        self.conf = configparser.ConfigParser()
        try:
            if os.path.exists('config.ini'):
                self.conf.read('config.ini', encoding='utf-8')
                if self.conf.has_section('MeterData') is True:
                    pass
                else:
                    self.ini()
            else:
                self.ini()
        except:
            print_exc(file=open('bug.txt', 'a+'))

    def ini(self):
        ini = open('config.ini', 'w', encoding='utf-8')
        self.conf.add_section('MeterData')
        data = open('source\\698data', 'r', encoding='utf-8')
        while 1:
            text = data.readline()
            if text == '\n':
                break
            text = text.split(' ')
            self.conf.set('MeterData', text[0], text[1] + ' ' + text[2][:-1])
        self.conf.write(ini)

    def serial_prepare(self):
        try:
            self.Connect.setDaemon(True)
            self.Connect.start()
            self.ui.pushButton.disconnect()
            self.ui.pushButton.clicked.connect(self.Connect.switch)
            self.__switch.emit('1')
        except:
            print_exc(file=open('bug.txt', 'a+'))

    def GetSerialNumber(self):
        SerialNumber = []
        port_list = list(serial.tools.list_ports.comports())
        if len(port_list) <= 0:
            print("The Serial port can't find!")
        else:
            for i in list(port_list):
                SerialNumber.append(i[0])
            return SerialNumber

    def Warming_message(self, message):
        if message == 'ERROR':
            QMessageBox.warning(self, 'ERROR', '无法打开串口')
        else:
            self.ui.textEdit.append(message)

    def Show_Hidden(self, num):
        if num == '0':
            self.ui.comboBox.setDisabled(0)
            self.ui.comboBox_2.setDisabled(0)
            self.ui.comboBox_3.setDisabled(0)
            self.ui.comboBox_4.setDisabled(0)
        else:
            self.ui.comboBox.setDisabled(1)
            self.ui.comboBox_2.setDisabled(1)
            self.ui.comboBox_3.setDisabled(1)
            self.ui.comboBox_4.setDisabled(1)


class Connect(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.serial = serial.Serial()
        self.__runflag = threading.Event()
        self.config = Config()

    def switch(self):
        if self.__runflag.isSet():
            MainWindow.ui.pushButton.setText('启动')
            print('关闭')
            MainWindow.Show_Hidden('0')
            self.__runflag.clear()
        else:
            MainWindow.ui.pushButton.setText('关闭')
            print('启动')
            MainWindow.Show_Hidden('1')
            self.__runflag.set()

    def run(self):
        self.__runflag.set()
        while 1:
            if self.__runflag.isSet():
                try:
                    revalue = self.serial_open()
                    print('revalue', revalue)
                    if revalue == 1:
                        print('clear')
                        self.__runflag.clear()
                        MainWindow.Show_Hidden('0')
                        MainWindow.ui.pushButton.setText('启动')
                        continue
                    if revalue is None:
                        continue
                except:
                    print('ERROR')
                    print_exc(file=open('bug.txt', 'a+'))
                    self.__runflag.clear()
            else:
                self.__runflag.wait()
                print('sleep1')

    def serial_open(self):
        self.serial.port = MainWindow.ui.comboBox.currentText()
        self.serial.baudrate = int(MainWindow.ui.comboBox_2.currentText())
        self.serial.parity = MainWindow.ui.comboBox_3.currentText()
        self.serial.stopbits = int(MainWindow.ui.comboBox_4.currentText())
        self.serial.timeout = 1
        if self.serial.isOpen() is True:
            print('close')
            self.serial.close()
        else:
            try:
                self.serial.open()
                MainWindow.ui.pushButton.setText('关闭')
                print('启动')
                global data, relen, LargeOAD, frozenSign, data_list
                data = ''
                while self.__runflag.isSet():
                    time.sleep(0.7)
                    num = self.serial.inWaiting()
                    data = data + str(b2a_hex(self.serial.read(num)))[2:-1]
                    try:
                        if data != '':
                            if data[0] == '6' and data[1] == '8' and data[-1] == '6':
                                if data[-1] == '6' and data[-2] == '1':
                                    print('Received: ', data)
                                    Received_data = '收到:\n' + makestr(data)
                                    MainWindow._signal_text.emit(Received_data)
                                    self.Meter = Meter698_core
                                    sent = self.Meter.Analysis(data.replace(' ', ''))
                                    if sent != 1:
                                        self.serial.write(a2b_hex(sent))
                                        self.Meter.ReturnMessage()
                                        content = self.Meter.ReturnMessage().transport()
                                        print('content:', content)
                                        message = '数据标识:' + get_list_sum(content)
                                        sent = '发送:\n' + makestr(sent)
                                        MainWindow._signal_text.emit(message)
                                        MainWindow._signal_text.emit(sent)
                                        times = time.strftime('%H:%M:%S')
                                        MainWindow._signal_text.emit(times)
                                        MainWindow._signal_text.emit('--------------------------------')
                                        LargeOAD = ''
                                        data_list = []
                                        data = ''
                                        frozenSign = 0
                                        self.Meter.ReturnMessage().clear_OI()
                                    else:
                                        data = ''
                            else:
                                try:
                                    while 1:
                                        print('data:', data)
                                        if data[-1] == '6' and data[-2] == '1':
                                            if data[0] == '6' and data[1] == '8':
                                                print('完整报文:', data)
                                                break
                                            elif data[0] == 'f' and data[1] == 'e':
                                                data = data[2:]
                                                continue
                                        if data[0] == '6' and data[1] == '8':
                                            print('不完整报文!继续接收:', data)
                                            break
                                        if data[0] == 'f' and data[1] == 'e':
                                            data = data[2:]
                                            continue
                                        print('Abort')
                                        data = ''
                                        break
                                except:
                                    pass
                                continue
                        else:
                            continue
                    except:
                        print_exc(file=open('bug.txt', 'a+'))
                        continue
            except:
                MainWindow._signal_text.emit('ERROR')
                print('无法打开串口')
                print_exc(file=open('bug.txt', 'a+'))
                return 1


class Config(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.ui = UI_Meter698_config.Ui_Dialog()
        self.ui.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self.ui.pushButton.clicked.connect(self.get_auto_day_frozon)
        self.ui.pushButton.clicked.connect(self.get_auto_curve_frozon)
        self.ui.pushButton.clicked.connect(self.get_auto_increase)
        self.ui.pushButton.clicked.connect(self.close)
        self.ui.pushButton.clicked.connect(self.list_save)
        self.ui.pushButton_3.clicked.connect(self.list_increas)
        self.ui.pushButton_4.clicked.connect(self.list_decreas)
        self.conf = configparser.ConfigParser()
        self.deal_list()
        self.ui.pushButton_6.clicked.connect(self.clear)
        self.ui.pushButton_5.clicked.connect(self.output_log)

    def output_log(self):
        txt = QFileDialog.getSaveFileName(self,'文件保存','C:/','Text Files (*.txt)')
        try:
            with open(txt[0],'w') as f:
                text = MainWindow.ui.textEdit.toPlainText()
                f.write(text)
        except:
            QMessageBox.about(self,'ERROR','文件保存失败')

    def clear(self):
        x = self.ui.tableWidget.rowCount() - 1
        while x:
            self.ui.tableWidget.removeRow(x)
            x -= 1
        self.deal_list()

    def get_auto_day_frozon(self):
        print('self.ui.checkBox.isChecked()', self.ui.checkBox.isChecked())
        if self.ui.checkBox.isChecked() is True:
            print('get_auto_day_frozon TURE')
            Meter698_core.set_auto_day_frozon(1)
        else:
            print('get_auto_day_frozon FLASE')
            Meter698_core.set_auto_day_frozon(0)
        return self.ui.checkBox.isChecked()

    def get_auto_curve_frozon(self):
        print('curve', self.ui.checkBox_2.isChecked())
        if self.ui.checkBox_2.isChecked() is True:
            print('get_auto_curve_frozon TURE')
            Meter698_core.curve_frozon(1)
        else:
            print('get_auto_curve_frozon FLASE')
            Meter698_core.curve_frozon(0)
        return self.ui.checkBox_2.isChecked()

    def get_auto_increase(self):
        print('increase', self.ui.checkBox_3.isChecked())
        if self.ui.checkBox_3.isChecked() is True:
            print('get_auto_increase TURE')
            Meter698_core.auto_00100200(1)
        else:
            print('get_auto_increase FLASE')
            Meter698_core.auto_00100200(0)
        return self.ui.checkBox_3.isChecked()

    def list_increas(self):
        num = self.ui.tableWidget.currentRow()
        self.ui.tableWidget.insertRow(num)

    def list_decreas(self):
        num = self.ui.tableWidget.currentRow()
        self.ui.tableWidget.removeRow(num)

    def deal_list(self):
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.conf.read('config.ini', encoding='utf-8')
        x = 0  # 行
        text = self.conf.items('MeterData')
        for items in text:
            y = 0
            self.ui.tableWidget.setItem(x, y, QTableWidgetItem(items[0]))
            for item in items[1].split(' '):
                y += 1
                self.ui.tableWidget.setItem(x, y, QTableWidgetItem(item))
            x += 1
            self.ui.tableWidget.insertRow(x)
        self.ui.tableWidget.removeRow(x)

    def list_save(self):
        try:
            x = self.ui.tableWidget.rowCount() - 1
            while x:
                y = 0
                text_0 = self.ui.tableWidget.item(x, y).text()
                text_1 = ''
                while y < 2:
                    y += 1
                    text_1 = text_1 + ' ' + self.ui.tableWidget.item(x, y).text()
                text_1 = text_1
                self.conf.set('MeterData', text_0, text_1)
                x -= 1
            self.conf.write(open('config.ini', 'w', encoding='utf-8'))
        except:
            print_exc(file=open('bug.txt', 'a+'))

    def black_and_white(self):
        if self.ui.radioButton_3.isChecked(): # 未启用
            return 0
        elif self.ui.radioButton.isChecked(): # 黑名单
            return 1,self.ui.textEdit
        elif self.ui.radioButton_2.isChecked(): # 白名单
            return 2,self.ui.textEdit_2


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = MainWindow()
    MainWindow.show()
    sys.exit(app.exec_())
