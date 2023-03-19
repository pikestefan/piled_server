# -*- coding: utf-8 -*-
"""
Created on Sat Mar 18 13:31:16 2023

@author: L
"""

from PyQt5.QtWidgets import (
    QPushButton,
    QLabel,
    QDialog,
    QWidget,
    QApplication,
    QColorDialog,
    QGridLayout,
    QSpinBox,
    QMainWindow,
    QSizePolicy,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
import sys
from pathlib import Path
import yaml
from piledserver.core.piled_client import PILedClient


class EditPositionDialog(QDialog):
    def __init__(self, init_val=0):
        super().__init__()

        layout = QGridLayout()

        layout.addWidget(QLabel("New position:"), 0, 0)
        self.position = QSpinBox()
        self.position.setValue(init_val)
        layout.addWidget(self.position, 0, 1)

        self.okbtn = QPushButton("OK")
        self.clbtn = QPushButton("Cancel")

        layout.addWidget(self.okbtn, 1, 2)
        layout.addWidget(self.clbtn, 1, 3)

        self.okbtn.clicked.connect(self.accept)
        self.clbtn.clicked.connect(self.close)

        self.setLayout(layout)


class FirstTimeDialog(QDialog):
    dialogAccepted = pyqtSignal(int, int, int, int)
    dialogRejected = pyqtSignal()

    def __init__(self):
        super().__init__()

        glayout = QGridLayout()

        label = QLabel(
            "Looks like you are a first-time user! Please pick the position of your experiment"
            " (preferably reflecting the order of the experiments  in the lab) and a color."
        )

        glayout.addWidget(label, 0, 0, 1, 4)
        self.setLayout(glayout)

        label = QLabel("Experiment position:")
        self.position_widget = QSpinBox()
        glayout.addWidget(label, 1, 0)
        glayout.addWidget(self.position_widget, 1, 1)

        self.colorpicker = QColorDialog()
        glayout.addWidget(self.colorpicker, 2, 0, 1, 4)

        self.colorpicker.colorSelected.connect(self.dialog_accepted)
        self.colorpicker.rejected.connect(self.dialog_rejected)

    def dialog_accepted(self, color):
        r, g, b, _ = color.getRgb()
        self.dialogAccepted.emit(self.position_widget.value(), r, g, b)
        self.close()

    def dialog_rejected(self):
        self.dialogRejected.emit()
        self.close()


class LedClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LED client")

        self.widg = QWidget()
        self.setCentralWidget(self.widg)

        self.setGeometry(200, 200, 0, 0)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.led_client = PILedClient()

        self.cfg_path = Path(__file__).parents[1] / "configs/client.cfg"

        self.posrgb_array = None
        self.close_requested = False

        with open(self.cfg_path, "r") as file:
            self.configs = yaml.safe_load(file)

        if "position" not in self.configs:
            self.show_dialog()
        else:
            self.posrgb_array = [self.configs["position"]] + self.configs[
                "led color"
            ]

        layout = QGridLayout()

        self.ledButton = QPushButton("LED on")
        self.ledButton.setObjectName("ledButton")
        self.ledButton.setCheckable(True)
        self.ledButton.clicked.connect(self.send_led_value)

        self.edit_position_btn = QPushButton("Edit position")
        self.edit_position_btn.clicked.connect(self.show_pos_dialog)

        self.edit_color_btn = QPushButton("Edit color")
        self.edit_color_btn.clicked.connect(self.show_col_dialog)

        self.poslabel = QLabel(
            f"Your current position: {self.posrgb_array[0]}"
        )

        self.col_indicator = QPushButton()
        self.col_indicator.setEnabled(False)
        self.col_indicator.setStyleSheet(
            "background-color: rgb({},{},{})".format(*self.posrgb_array[1:])
        )
        self.col_indicator.setObjectName("colIndicator")

        layout.addWidget(self.poslabel, 0, 0, 1, 3)
        layout.addWidget(QLabel("LED color:"), 2, 0)
        layout.addWidget(self.col_indicator, 1, 1, 3, 1)

        layout.addWidget(self.ledButton, 4, 0, 3, 3)
        layout.addWidget(self.edit_position_btn, 8, 5)
        layout.addWidget(self.edit_color_btn, 9, 5)

        verticalSpacer = QSpacerItem(
            20, 0, QSizePolicy.Minimum, QSizePolicy.Minimum
        )
        layout.addItem(verticalSpacer, 7, 1)

        verticalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        layout.addItem(verticalSpacer, 10, 0)

        horSpacer = QSpacerItem(
            200, 40, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        layout.addItem(horSpacer, 0, 20)

        self.widg.setLayout(layout)

        if "last state" in self.configs:
            value = self.configs["last state"]
            if value:
                self.ledButton.setChecked(value)
                self.ledButton.setText("LED on")
                self.enable_edits(False)

    def send_led_value(self, value):
        self.enable_edits(not value)
        if value:
            self.ledButton.setText("LED on")
            returnval = self.led_client.send_poscolor(*self.posrgb_array)
            if returnval == -1:
                self.ledButton.setText("LED off")
                self.ledButton.setChecked(False)
        else:
            self.ledButton.setText("LED off")
            self.led_client.send_poscolor(self.posrgb_array[0], 0, 0, 0)

    def enable_edits(self, value):
        self.edit_color_btn.setEnabled(value)
        self.edit_position_btn.setEnabled(value)

    def show_dialog(self):
        dialog = FirstTimeDialog()
        dialog.dialogAccepted.connect(self.set_posrgb)
        dialog.exec()

    def show_pos_dialog(self):
        dialog = EditPositionDialog(self.posrgb_array[0])
        if dialog.exec():
            newpos = dialog.position.value()
            self.posrgb_array[0] = newpos
            self.set_posrgb(*self.posrgb_array)

    def show_col_dialog(self):
        dialog = QColorDialog()

        dialog.setCurrentColor(QColor(*self.posrgb_array[1:]))
        if dialog.exec():
            new_color = dialog.selectedColor().getRgb()

            for ii, col in enumerate(self.posrgb_array[1:]):
                self.posrgb_array[ii + 1] = new_color[ii]
                self.set_posrgb(*self.posrgb_array)

    def closeEvent(self, event):
        self.configs["last state"] = self.ledButton.isChecked()

        with open(self.cfg_path, "w") as file:
            yaml.dump(self.configs, file)

    def set_posrgb(self, pos, r, g, b):
        self.configs["position"] = pos
        self.configs["led color"] = [r, g, b]
        self.posrgb_array = [pos, r, g, b]

        try:
            self.poslabel.setText(
                f"Your current position: {self.posrgb_array[0]}"
            )
            self.col_indicator.setStyleSheet(
                "background-color: rgb({},{},{})".format(
                    *self.posrgb_array[1:]
                )
            )
        except:
            pass

        with open(self.cfg_path, "w") as file:
            yaml.dump(self.configs, file)


if __name__ == "__main__":
    filepath = Path(__file__).resolve().parents[1]
    qss = filepath / "artwork" / "stylesheet.qss"
    app = QApplication(sys.argv)
    with open(qss, "r") as fh:
        app.setStyleSheet(fh.read())
    wind = LedClientGUI()
    wind.show()
    sys.exit(app.exec_())
