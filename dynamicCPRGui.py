# -*- coding: utf-8 -*-

""" ============================================================================
#
# This module contains the GUI
#
 =========================================================================== """

# ==============================================================================
# IMPORTS
# ==============================================================================
# built-in
from __future__ import division
import sys
import logging
from PyQt4 import QtGui, QtCore
import random
from datetime import timedelta
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

# le2m
from util.utili18n import le2mtrans
from util.utiltools import timedelta_to_time
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguitablemodels import TableModelHistorique
from client.cltgui.cltguiwidgets import (WPeriod, WExplication, WCompterebours,
                                         WTableview)

# dynamicCPR
import dynamicCPRParams as pms
from dynamicCPRTexts import trans_DYNCPR
import dynamicCPRTexts as texts_DYNCPR


logger = logging.getLogger("le2m")


# ==============================================================================
# WIDGETS
# ==============================================================================


class MySlider(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.current_value = 0

        # self.layout = QtGui.QVBoxLayout()
        # self.setLayout(self.layout)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.lcd_layout = QtGui.QHBoxLayout()
        self.lcd_layout.addSpacerItem(
            QtGui.QSpacerItem(20, 5, QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Fixed))
        self.lcd = QtGui.QLCDNumber(5)
        self.lcd.setMode(QtGui.QLCDNumber.Dec)
        self.lcd.setSmallDecimalPoint(True)
        self.lcd.setSegmentStyle(QtGui.QLCDNumber.Flat)
        self.lcd.setFixedSize(100, 50)
        self.lcd_layout.addWidget(self.lcd)
        self.lcd_layout.addSpacerItem(
            QtGui.QSpacerItem(20, 5, QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Fixed))
        self.layout.addLayout(self.lcd_layout, 0, 1)

        self.label_min = QtGui.QLabel(str(pms.DECISION_MIN))
        self.layout.addWidget(self.label_min, 1, 0)
        self.label_max = QtGui.QLabel(str(pms.DECISION_MAX))
        self.layout.addWidget(self.label_max, 1, 2)

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(pms.DECISION_MIN)
        self.slider.setMaximum(pms.DECISION_MAX*int(1 / pms.DECISION_STEP))
        self.slider.setTickInterval(100)
        self.slider.setTickPosition(QtGui.QSlider.TicksAbove)
        self.slider.valueChanged.connect(self.display)
        self.layout.addWidget(self.slider, 2, 0, 1, 3)

        self.adjustSize()

    def display(self, value):
        self.lcd.display(value / int(1 / pms.DECISION_STEP))

    def value(self):
        return self.slider.value() / int(1 / pms.DECISION_STEP)


class PlotExtraction(QtGui.QWidget):
    """
    This widget plot the individual extractions
    """
    def __init__(self, cltuid, extractions_indiv):
        QtGui.QWidget.__init__(self)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        self.fig = plt.figure(figsize=(10, 7))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.graph = self.fig.add_subplot(111)

        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            self.graph.set_xlim(-1, pms.NOMBRE_PERIODES + 1)
            self.graph.set_xlabel(trans_DYNCPR(u"Periods"))
            self.graph.set_xticks(range(0, pms.NOMBRE_PERIODES + 1))
            for k, v in extractions_indiv.items():
                if k == cltuid:
                    lab = trans_DYNCPR(u"Me")
                else:
                    lab = trans_DYNCPR(u"The other")
                self.graph.plot(v.xdata, v.ydata, ls="-", label=lab, marker="*")

        elif pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            self.graph.set_xlim(
                -5, pms.CONTINUOUS_TIME_DURATION.total_seconds() + 5)
            self.graph.set_xticks(
                range(0, int(pms.CONTINUOUS_TIME_DURATION.total_seconds())+1, 10))
            self.graph.set_xlabel(trans_DYNCPR(u"Time (seconds)"))
            for k, v in extractions_indiv.items():
                if k == cltuid:
                    lab = trans_DYNCPR(u"Me")
                else:
                    lab = trans_DYNCPR(u"The other")
                if v.curve is None:
                    v.curve, = self.graph.plot(
                        v.xdata, v.ydata, ls="-", label=lab)

        self.graph.set_ylim(-5, 25)
        self.graph.set_yticks(range(0, 21, 5))
        self.graph.set_ylabel(trans_DYNCPR(u"Extraction"))
        self.graph.set_title(trans_DYNCPR(u"Individual extractions"))
        self.graph.grid()
        self.graph.legend(loc="lower left", ncol=pms.TAILLE_GROUPES,
                          fontsize=10)
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
            self.graph.set_xlim(-1, pms.NOMBRE_PERIODES + 1)
            self.graph.set_xlabel(trans_DYNCPR(u"Periods"))
            self.graph.set_xticks(range(0, pms.NOMBRE_PERIODES + 1))
            self.graph.plot(
                self.extraction_group.xdata, self.extraction_group.ydata,
                "-*k", label=trans_DYNCPR(u"Group extraction"))
            self.graph.plot(
                self.resource.xdata, self.resource.ydata,
                "-*g", label=trans_DYNCPR(u"Stock of resource"))

        elif pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            self.graph.set_xlim(
                -5, pms.CONTINUOUS_TIME_DURATION.total_seconds() + 5)
            self.graph.set_xticks(
                range(0, int(pms.CONTINUOUS_TIME_DURATION.total_seconds())+1, 10))
            self.graph.set_xlabel(trans_DYNCPR(u"Time (seconds)"))
            if self.extraction_group.curve is None:
                self.extraction_group.curve, = self.graph.plot(
                    self.extraction_group.xdata, self.extraction_group.ydata,
                    "-k", label=trans_DYNCPR(u"Group extraction"))
            if self.resource.curve is None:
                self.resource.curve, = self.graph.plot(
                    self.resource.xdata, self.resource.ydata,
                    "-g", label=trans_DYNCPR(u"Stock of resource"))

        self.graph.set_ylim(-15, 130)
        self.graph.set_yticks(range(0, 121, 10))
        self.graph.set_ylabel(trans_DYNCPR(u"Stock of resource"))
        self.graph.set_title(
            trans_DYNCPR(u"Group extraction and stock of resource"))
        self.graph.grid()
        self.graph.legend(loc="lower left", ncol=2, fontsize=10)
        self.canvas.draw()


# ==============================================================================
# SCREEN FOR INITIAL EXTRACTION
# ==============================================================================


class GuiInitialExtraction(QtGui.QDialog):
    def __init__(self, remote, defered):
        QtGui.QDialog.__init__(self, remote.le2mclt.screen)

        self.remote = remote
        self.defered = defered

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

        if self.remote.le2mclt.automatique:
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
        if not self.remote.le2mclt.automatique:
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
# DECISION SCREEN
# ==============================================================================


class GuiDecision(QtGui.QDialog):
    def __init__(self, remote, defered):
        super(GuiDecision, self).__init__(remote.le2mclt.screen)

        # ----------------------------------------------------------------------
        # main attributes
        # ----------------------------------------------------------------------
        self.remote = remote
        self.defered = defered
        self.historique = GuiHistorique(self, self.remote.histo)

        layout = QtGui.QVBoxLayout(self)

        # ----------------------------------------------------------------------
        # HEAD AREA
        # ----------------------------------------------------------------------

        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            wperiod = WPeriod(self.remote.currentperiod, self.historique)
            layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_DYNCPR.EXTRACTION, size=(450, 80), parent=self)
        layout.addWidget(wexplanation)

        if pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            wtimer = WCompterebours(
                self, pms.CONTINUOUS_TIME_DURATION, lambda: None)
            layout.addWidget(wtimer)

        # ----------------------------------------------------------------------
        # GRAPHICAL AREA
        # ----------------------------------------------------------------------

        layout_plot = QtGui.QHBoxLayout()
        layout.addLayout(layout_plot)
        self.plot_extraction = PlotExtraction(
            self.remote.le2mclt.uid, self.remote.extractions_indiv)
        layout_plot.addWidget(self.plot_extraction)
        self.plot_resource = PlotResource(
            self.remote.extraction_group, self.remote.resource)
        layout_plot.addWidget(self.plot_resource)

        # ----------------------------------------------------------------------
        # DECISION AREA
        # ----------------------------------------------------------------------

        self.extract_dec = MySlider()
        player_extrac = self.remote.extractions_indiv[self.remote.le2mclt.uid].ydata[-1]
        self.extract_dec.slider.setValue(player_extrac * 100)
        self.extract_dec.lcd.display(player_extrac)
        layout.addWidget(self.extract_dec)

        # ----------------------------------------------------------------------
        # FOOT AREA
        # ----------------------------------------------------------------------

        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        self.buttons.accepted.connect(self._accept)
        layout.addWidget(self.buttons)

        self.setWindowTitle(trans_DYNCPR(u"Decision"))
        self.adjustSize()
        self.setFixedSize(self.size())

        if pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            self.buttons.setEnabled(False)
            self.extract_dec.slider.sliderReleased.connect(self.send_extrac)
            if self.remote.le2mclt.automatique:
                self.extract_dec.slider.valueChanged.connect(self.send_extrac)
            self.timer_continuous = QtCore.QTimer()
            self.timer_continuous.timeout.connect(
                self.update_data_and_graphs)
            self.timer_continuous.start(
                int(pms.TIMER_UPDATE.total_seconds())*1000)
            self.remote.end_of_time.connect(self.end_of_time)

        if pms.DYNAMIC_TYPE == pms.DISCRETE and self.remote.le2mclt.automatique:
            self.timer_automatique = QtCore.QTimer()
            self.extract_dec.slider.setValue(random.randint(
                pms.DECISION_MIN,
                pms.DECISION_MAX*int(1 / pms.DECISION_STEP)))
            self.timer_automatique.setSingleShot(True)
            self.timer_automatique.timeout.connect(
                self.buttons.button(QtGui.QDialogButtonBox.Ok).click)
            self.timer_automatique.start(7000)

    def reject(self):
        pass
    
    def _accept(self):
        try:
            self.timer_automatique.stop()
        except AttributeError:
            pass

        extraction = None

        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            extraction = self.extract_dec.value()
            if not self.remote.le2mclt.automatique:
                confirmation = QtGui.QMessageBox.question(
                    self, le2mtrans(u"Confirmation"),
                    le2mtrans(u"Do you confirm your choice?"),
                    QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
                if confirmation != QtGui.QMessageBox.Yes:
                    return

        logger.info(u"{} send {}".format(self.remote.le2mclt, extraction))
        super(GuiDecision, self).accept()
        self.defered.callback(extraction)

    def send_extrac(self):
        dec = self.extract_dec.value()
        logger.info("{} send {}".format(self.remote.le2mclt, dec))
        self.remote.server_part.callRemote("new_extraction", dec)

    def update_data_and_graphs(self):
        if self.remote.le2mclt.automatique:
            if random.random() < 0.33:
                self.extract_dec.slider.setValue(random.randint(
                    pms.DECISION_MIN,
                    pms.DECISION_MAX * int(1 / pms.DECISION_STEP)))
        self.plot_extraction.canvas.draw()
        self.plot_resource.canvas.draw()

    def end_of_time(self):
        self.timer_continuous.stop()
        self.extract_dec.setEnabled(False)
        self.buttons.setEnabled(True)
        if self.remote.le2mclt.automatique:
            self.timer_automatique = QtCore.QTimer()
            self.timer_automatique.setSingleShot(True)
            self.timer_automatique.timeout.connect(
                self.buttons.button(QtGui.QDialogButtonBox.Ok).click)
            self.timer_automatique.start(7000)


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

        # ----------------------------------------------------------------------
        # treatment
        # ----------------------------------------------------------------------
        # self.combo_treatment = QtGui.QComboBox()
        # self.combo_treatment.addItems(
        #     [v for k, v in sorted(pms.TREATMENTS_NAMES.items())])
        # self.combo_treatment.setCurrentIndex(pms.TREATMENT)
        # form.addRow(QtGui.QLabel(u"Traitement"), self.combo_treatment)

        # ----------------------------------------------------------------------
        # dynamic
        # ----------------------------------------------------------------------
        self.combo_dynamic = QtGui.QComboBox()
        self.combo_dynamic.addItems(["CONTINUOUS", "DISCRETE"])
        self.combo_dynamic.setCurrentIndex(pms.DYNAMIC_TYPE)
        form.addRow(QtGui.QLabel("Dynamic"), self.combo_dynamic)

        # ----------------------------------------------------------------------
        # trial part
        # ----------------------------------------------------------------------
        self.checkbox_essai = QtGui.QCheckBox()
        self.checkbox_essai.setChecked(pms.PARTIE_ESSAI)
        form.addRow(QtGui.QLabel(u"Trial part"), self.checkbox_essai)

        # ----------------------------------------------------------------------
        # periods
        # ----------------------------------------------------------------------
        self.spin_periods = QtGui.QSpinBox()
        self.spin_periods.setMinimum(0)
        self.spin_periods.setMaximum(100)
        self.spin_periods.setSingleStep(1)
        self.spin_periods.setValue(pms.NOMBRE_PERIODES)
        self.spin_periods.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self.spin_periods.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Number of periods"), self.spin_periods)

        # ----------------------------------------------------------------------
        # continuous time duration
        # ----------------------------------------------------------------------
        self.timeEdit_continuous_duration = QtGui.QTimeEdit()
        self.timeEdit_continuous_duration.setDisplayFormat("hh:mm:ss")
        time_duration = timedelta_to_time(pms.CONTINUOUS_TIME_DURATION)
        self.timeEdit_continuous_duration.setTime(
            QtCore.QTime(time_duration.hour, time_duration.minute,
                         time_duration.second))
        self.timeEdit_continuous_duration.setMaximumWidth(100)
        form.addRow(QtGui.QLabel(u"Continuous time duration"),
                    self.timeEdit_continuous_duration)

        # ----------------------------------------------------------------------
        # buttons
        # ----------------------------------------------------------------------
        button = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        button.accepted.connect(self._accept)
        button.rejected.connect(self.reject)
        layout.addWidget(button)

        self.setWindowTitle(u"Configure")
        self.adjustSize()
        self.setFixedSize(self.size())

    def _accept(self):
        # pms.TREATMENT = self.combo_treatment.currentIndex()
        pms.PARTIE_ESSAI = self.checkbox_essai.isChecked()
        pms.DYNAMIC_TYPE = self.combo_dynamic.currentIndex()
        pms.NOMBRE_PERIODES = self.spin_periods.value()
        time_continuous = self.timeEdit_continuous_duration.time().toPyTime()
        pms.CONTINUOUS_TIME_DURATION = timedelta(
            hours=time_continuous.hour, minutes=time_continuous.minute,
            seconds=time_continuous.second)
        self.accept()


# ==============================================================================
# SUMMARY SCREEN
# ==============================================================================


class GuiSummary(QtGui.QDialog):
    def __init__(self, remote, defered, the_text=""):
        super(GuiSummary, self).__init__(remote.le2mclt.screen)

        self.remote = remote
        self.defered = defered
        self.historique = GuiHistorique(self, self.remote.histo)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            wperiod = WPeriod(self.remote.currentperiod, self.historique)
            layout.addWidget(wperiod)

        wexplanation = WExplication(text=the_text, size=(450, 80), parent=self)
        layout.addWidget(wexplanation)

        # ----------------------------------------------------------------------
        # GRAPHICAL AREA
        # ----------------------------------------------------------------------
        for v in self.remote.extractions_indiv.values():
            v.curve = None
        self.remote.extraction_group.curve = None
        self.remote.resource.curve = None

        layout_plot = QtGui.QHBoxLayout()
        layout.addLayout(layout_plot)
        self.plot_extraction = PlotExtraction(
            self.remote.le2mclt.uid, self.remote.extractions_indiv)
        layout_plot.addWidget(self.plot_extraction)
        self.plot_resource = PlotResource(
            self.remote.extraction_group, self.remote.resource)
        layout_plot.addWidget(self.plot_resource)

        # ----------------------------------------------------------------------
        # TABLE AREA
        # ----------------------------------------------------------------------
        # ligne historique (entêtes et dernière ligne de l'historique)
        histo_recap = [self.remote.histo[0], self.remote.histo[-1]]
        self.tablemodel = TableModelHistorique(histo_recap)
        self.widtableview = WTableview(parent=self, tablemodel=self.tablemodel,
                                       size=(500, 90))
        self.widtableview.ui.tableView.verticalHeader().setResizeMode(
            QtGui.QHeaderView.Stretch)
        layout.addWidget(self.widtableview)

        # ----------------------------------------------------------------------
        # FINALIZE THE DIALOG
        # ----------------------------------------------------------------------

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

        # auto
        if self.remote.le2mclt.automatique:
            self.timer_automatique = QtCore.QTimer()
            self.timer_automatique.timeout.connect(
                buttons.button(QtGui.QDialogButtonBox.Ok).click)
            self.timer_automatique.start(7000)

        # title and size
        self.setWindowTitle(le2mtrans(u"Summary"))
        self.adjustSize()
        self.setFixedSize(self.size())

    def _accept(self):
        try:
            self.timer_automatique.stop()
        except AttributeError:
            pass
        logger.info(u"{} send Ok summary".format(self.remote.le2mclt))
        self.defered.callback(1)
        self.accept()

    def reject(self):
        pass


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    slider = MySlider()
    slider.setGeometry(300, 300, 300, 200)
    slider.show()
    sys.exit(app.exec_())