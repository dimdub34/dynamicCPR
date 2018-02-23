# -*- coding: utf-8 -*-
"""
This module contains the GUI
"""

from __future__ import division
import sys
import logging
from PyQt4 import QtGui, QtCore
from twisted.internet import defer
import random

from util.utili18n import le2mtrans
import dynamicCPRParams as pms
from dynamicCPRTexts import trans_DYNCPR
import dynamicCPRTexts as texts_DYNCPR
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguiwidgets import (WPeriod, WExplication, WCompterebours,
                                         WSlider)
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


logger = logging.getLogger("le2m")


# ==============================================================================
# WIDGETS
# ==============================================================================


class MySlider(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.current_value = 0

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)

        self.lcd = QtGui.QLCDNumber(5)
        self.lcd.setMode(QtGui.QLCDNumber.Dec)
        self.lcd.setSmallDecimalPoint(True)
        self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.layout.addWidget(self.lcd)

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(pms.DECISION_MIN)
        self.slider.setMaximum(pms.DECISION_MAX*int(1 / pms.DECISION_STEP))
        self.slider.setTickInterval(1)
        self.slider.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.layout.addWidget(self.slider)
        self.slider.valueChanged.connect(self.display)

        self.adjustSize()

    def display(self, value):
        self.lcd.display(value / int(1 / pms.DECISION_STEP))

    def value(self):
        return self.slider.value() / int(1 / pms.DECISION_STEP)


# ==============================================================================
# SCREEN FOR INITIAL EXTRACTION
# ==============================================================================


class GuiInitialExtraction(QtGui.QDialog):
    def __init__(self, parent, defered, automatique):
        QtGui.QDialog.__init__(self, parent)

        self.defered = defered
        self.automatique = automatique

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        explanation_area = WExplication(
            parent=self, text=texts_DYNCPR.INITIAL_EXTRACTION)
        layout.addWidget(explanation_area)

        self.slider_area = MySlider()
        layout.addWidget(self.slider_area)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

        self.setWindowTitle("Decision")
        self.adjustSize()
        self.setFixedSize(self.size())

        if self.automatique:
            self.slider_area.slider.setValue(random.randint(
                pms.DECISION_MIN, pms.DECISION_MAX*int(1 / pms.DECISION_STEP)))
            self.timer_automatique = QtCore.QTimer()
            self.timer_automatique.timeout.connect(
                buttons.button(QtGui.QDialogButtonBox.Ok).click)
            self.timer_automatique.start(7000)

    def _accept(self):
        try:
            self.timer_automatique.stop()
        except AttributeError:
            pass
        val = self.slider_area.slider.value() / int(1/pms.DECISION_STEP)
        if not self.automatique:
            confirmation = QtGui.QMessageBox.question(
                self, "Confirmation", trans_DYNCPR(u"Do you confirm your choice?"),
                QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            if confirmation != QtGui.QMessageBox.Yes:
                return
        self.accept()
        logger.info("send {}".format(val))
        self.defered.callback(val)

    def reject(self):
        pass


# ==============================================================================
# WIDGETS FOR THE GRAPHS
# ==============================================================================


class PlotExtraction(QtGui.QWidget):
    """
    This widget plot the individual extractions
    """
    def __init__(self, individual_extractions):
        QtGui.QWidget.__init__(self)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        self.fig = plt.figure(figsize=(10, 7))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.graph = self.fig.add_subplot(111)
        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            self.graph.set_xlim(0, pms.NOMBRE_PERIODES + 1)
            self.graph.set_xlabel(trans_DYNCPR(u"Periods"))
            self.graph.set_xticks(range(1, pms.NOMBRE_PERIODES + 1))
        elif pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            self.graph.set_xlim(-5, pms.CONTINUOUS_TIME_DURATION.total_seconds() + 5)
            self.graph.set_xlabel(trans_DYNCPR(u"Time (seconds)"))
        self.graph.set_ylim(-1, 22)
        self.graph.set_yticks(range(0, 21, 5))
        self.graph.set_ylabel(trans_DYNCPR(u"Extraction"))
        self.graph.legend(loc="upper left", ncol=pms.TAILLE_GROUPES,
                          fontsize=10)
        self.graph.set_title(trans_DYNCPR(u"Individual extractions"))
        self.graph.grid()

        # init the curve
        for k, v in individual_extractions.items():
            v.curve = self.graph.plot(v.xdata, v.ydata, label=k)

        self.canvas.draw()


class PlotResource(QtGui.QWidget):
    """
    Display the curves with the total extraction of the group and the curve of
    the stock of resource
    """
    def __init__(self, extraction_group, resource):
        QtGui.QWidget.__init__(self)

        self.extraction_group = extraction_group
        self.resource = resource

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        self.fig = plt.figure(figsize=(10, 7))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.graph = self.fig.add_subplot(111)
        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            self.graph.set_xlim(0, pms.NOMBRE_PERIODES + 1)
            self.graph.set_xlabel(trans_DYNCPR(u"Periods"))
            self.graph.set_xticks(range(1, pms.NOMBRE_PERIODES + 1))
        elif pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            self.graph.set_xlim(-5, pms.CONTINUOUS_TIME_DURATION.total_seconds() + 5)
            self.graph.set_xlabel(trans_DYNCPR(u"Time (seconds)"))
        self.graph.set_ylim(-5, 125)
        self.graph.set_ylabel(trans_DYNCPR(u"Stock of resource"))
        self.graph.legend(loc="lower left", ncol=2, fontsize=10)
        self.graph.set_title(
            trans_DYNCPR(u"Group extraction and stock of resource"))
        self.graph.grid()

        # group extraction
        self.extraction_group.curve = self.graph.plot(
            self.extraction_group.xdata, self.extraction_group.ydata,
            "-k", label=trans_DYNCPR(u"Group extraction"))

        # stock of resource
        self.resource.curve = self.graph.plot(
            self.resource.xdata, self.resource.ydata,
            "-g", label=trans_DYNCPR(u"Stock of resource"))

        self.canvas.draw()


# ==============================================================================
# DECISION SCREEN
# ==============================================================================


class GuiDecision(QtGui.QDialog):
    def __init__(self, defered, automatique, parent, period, historique,
                 individual_extractions, group_extraction, resource):
        super(GuiDecision, self).__init__(parent)

        # variables
        self.defered = defered
        self.automatique = automatique
        self.historique = GuiHistorique(self, historique)
        self.individual_extractions = individual_extractions
        self.group_extraction = group_extraction
        self.resource = resource

        layout = QtGui.QVBoxLayout(self)

        # ----------------------------------------------------------------------
        # HEAD AREA
        # ----------------------------------------------------------------------

        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            wperiod = WPeriod(period, self.historique)
            layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_DYNCPR.get_text_explanation(),
            size=(450, 80), parent=self)
        layout.addWidget(wexplanation)

        if pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            wtimer = WCompterebours(
                self, pms.CONTINUOUS_TIME_DURATION, self._accept)
            layout.addWidget(wtimer)

        # ----------------------------------------------------------------------
        # GRAPHICAL AREA
        # ----------------------------------------------------------------------

        layout_plot = QtGui.QHBoxLayout()
        layout.addLayout(layout_plot)
        self.plot_extraction = PlotExtraction(self.individual_extractions)
        layout_plot.addWidget(self.plot_extraction)
        self.plot_resource = PlotResource(self.group_extraction, self.resource)
        layout_plot.addWidget(self.plot_resource)

        # ----------------------------------------------------------------------
        # DECISION AREA
        # ----------------------------------------------------------------------

        self.extract_dec = MySlider()
        layout.addWidget(self.extract_dec)

        # ----------------------------------------------------------------------
        # FOOT AREA
        # ----------------------------------------------------------------------

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

        self.setWindowTitle(trans_DYNCPR(u"Décision"))
        self.adjustSize()
        self.setFixedSize(self.size())

        if pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            self._timer_continuous = QtCore.QTimer()
            self._timer_continuous.timeout.connect(self.update_graphs)
            self._timer_continuous.setSingleShot(False)
            self._timer_continuous.start(1000)

        if self.automatique:
            self._timer_automatique = QtCore.QTimer()
            self._timer_automatique.timeout.connect(
                buttons.button(QtGui.QDialogButtonBox.Ok).click)
            self._timer_automatique.start(7000)
                
    def reject(self):
        pass
    
    def _accept(self):
        try:
            self._timer_automatique.stop()
        except AttributeError:
            pass
        extraction = self.extract_dec.value()
        if not self.automatique:
            confirmation = QtGui.QMessageBox.question(
                self, le2mtrans(u"Confirmation"),
                le2mtrans(u"Do you confirm your choice?"),
                QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            if confirmation != QtGui.QMessageBox.Yes: 
                return
        logger.info(u"Send {}".format(extraction))
        self.accept()
        self.defered.callback(extraction)

    @defer.inlineCallbacks
    def send_extraction(self):
        yield (self.remote.server_part.callRemote(
            "new_extraction", self.extract_dec.value()))


# ==============================================================================
# CONFIGURATION SCREEN
# ==============================================================================


class DConfigure(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        form = QtGui.QFormLayout()
        layout.addLayout(form)

        # treatment
        self._combo_treatment = QtGui.QComboBox()
        self._combo_treatment.addItems(
            [v for k, v in sorted(pms.TREATMENTS_NAMES.items())])
        self._combo_treatment.setCurrentIndex(pms.TREATMENT)
        form.addRow(QtGui.QLabel(u"Traitement"), self._combo_treatment)

        # dynamic
        self._combo_dynamic = QtGui.QComboBox()
        self._combo_dynamic.addItems(["CONTINUOUS", "DISCRETE"])
        self._combo_dynamic.setCurrentIndex(pms.DYNAMIC_TYPE)
        form.addRow(QtGui.QLabel("Dynamic"), self._combo_dynamic)

        # partie d'essai
        self._checkbox_essai = QtGui.QCheckBox()
        self._checkbox_essai.setChecked(pms.PARTIE_ESSAI)
        form.addRow(QtGui.QLabel(u"Partie d'essai"), self._checkbox_essai)

        # nombre de périodes
        self._spin_periods = QtGui.QSpinBox()
        self._spin_periods.setMinimum(0)
        self._spin_periods.setMaximum(100)
        self._spin_periods.setSingleStep(1)
        self._spin_periods.setValue(pms.NOMBRE_PERIODES)
        self._spin_periods.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_periods.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Nombre de périodes"), self._spin_periods)

        # taille groupes
        self._spin_groups = QtGui.QSpinBox()
        self._spin_groups.setMinimum(0)
        self._spin_groups.setMaximum(100)
        self._spin_groups.setSingleStep(1)
        self._spin_groups.setValue(pms.TAILLE_GROUPES)
        self._spin_groups.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_groups.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Taille des groupes"), self._spin_groups)

        button = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        button.accepted.connect(self._accept)
        button.rejected.connect(self.reject)
        layout.addWidget(button)

        self.setWindowTitle(u"Configurer")
        self.adjustSize()
        self.setFixedSize(self.size())

    def _accept(self):
        pms.TREATMENT = self._combo_treatment.currentIndex()
        pms.PERIODE_ESSAI = self._checkbox_essai.isChecked()
        pms.NOMBRE_PERIODES = self._spin_periods.value()
        pms.TAILLE_GROUPES = self._spin_groups.value()
        self.accept()


class TestSlider(QtGui.QDialog):
    def __init__(self):
        super(TestSlider, self).__init__()
        layout = QtGui.QVBoxLayout(self)
        self.extract_dec = WSlider(
            parent=self, label=trans_DYNCPR(u"Your extraction"),
            minimum=pms.DECISION_MIN, maximum=pms.DECISION_MAX*100,
            interval=pms.DECISION_STEP
        )
        layout.addWidget(self.extract_dec)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    def display(what):
        print(what)
    # test_slider = TestSlider()
    test_slider = MySlider()
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: display(test_slider.value()))
    timer.start(1000)
    def stop():
        timer.stop()
    QtCore.QTimer.singleShot(10000, stop)
    test_slider.show()
    sys.exit(app.exec_())