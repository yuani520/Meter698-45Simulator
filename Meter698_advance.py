from Meter698_Start import Config
import threading,UI_Meter698_config
from PyQt5.QtWidgets import QDialog

class Config_advance(QDialog,threading.Thread):
    def __init__(self):
        QDialog.__init__(self)
        threading.Thread.__init__(self)
        self.ui = UI_Meter698_config.Ui_Dialog()

    def run(self):
        while 1:
            self.Curve_leak()

    def Curve_leak(self):
        if self.ui.checkBox_6.isChecked():
            self.ui.label_4.isEnabled()
            self.ui.label_5.isEnabled()
            self.ui.timeEdit.isEnabled()
            self.ui.timeEdit_2.isEnabled()
        else:
            self.ui.label_4.setDisabled(1)
            self.ui.label_5.setDisabled(1)
            self.ui.timeEdit.setDisabled(1)
            self.ui.timeEdit_2.setDisabled(1)
