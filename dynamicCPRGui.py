# -*- coding: utf-8 -*-
"""
This module contains the GUI
"""
import logging
from PyQt4 import QtGui, QtCore
from util.utili18n import le2mtrans
import dynamicCPRParams as pms
from dynamicCPRTexts import trans_DYNCPR
import dynamicCPRTexts as texts_DYNCPR
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguiwidgets import WPeriod, WExplication, WSpinbox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


logger = logging.getLogger("le2m")


class PlotWidget(QtGui.QWidget):
    def __init__(self, time_duration):
        super(PlotWidget).__init__()

        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)

        self.plot_extraction = PlotExtraction(time_duration=time_duration)
        layout.addWidget(self.plot_extraction)

        self.plot_resource = PlotRessource(time_duration=time_duration)
        layout.addWidget(self.plot_resource)


class PlotExtraction(FigureCanvas):
    def __init__(self, remote, time_duration):
        """

        :param remote:
        :param time_duration: in order to set the abscissa of the graph
        """
        self.remote = remote

        self.fig = plt.figure(figsize=(10, 7))
        FigureCanvas.__init__(self, self.fig)

        self.graph = self.fig.add_subplot(111)
        self.graph.set_xlim(-5, time_duration + 5)
        self.graph.set_xlabel(trans_DYNCPR("Time (seconds)"))
        self.graph.set_ylim(-1, 22)
        self.graph.set_yticks(range(0, 21, 5))
        self.graph.set_ylabel(trans_DYNCPR("Extraction"))
        self.graph.legend(loc="upper left", ncol=pms.TAILLE_GROUPES,
                          fontsize=10)
        self.graph.set_title(trans_DYNCPR("Individual extraction"))
        self.graph.grid()

        # init the curve
        for k, v in self.remote.extractions.items():
            v.curve = self.graph.plot(v.xdata, v.ydata, label=k)

    def update_extractions(self):
        """
        ydata has to be set in the remote class
        :param time:
        :return:
        """
        for k, v in self.remote.extractions.items():
            v.curve.set_data(v.xdata, v.ydata)
        self.fig.canvas.draw()


class PlotRessource(FigureCanvas):
    """
    Display the curves with the total extraction of the group and the curve of
    the stock of resource
    """
    def __init__(self, time_duration, extraction_group, resource):
        """
        :param remote
        :param time_duration: needed to set the abscissa axis
        """
        self.extraction_group = extraction_group
        self.resource = resource

        self.fig = plt.figure(figsize=(10, 7))
        FigureCanvas.__init__(self, self.fig)

        self.graph = self.fig.add_subplot(111)
        self.graph.set_xlim(-5, time_duration + 5)
        self.graph.set_xlabel(trans_DYNCPR("Time (seconds)"))
        self.graph.set_ylim(-5, 125)
        self.graph.set_ylabel(trans_DYNCPR("Stock of resource"))
        self.graph.legend(loc=9, ncol=2, fontsize=10)
        self.graph.set_title(trans_DYNCPR("Group extraction and stock of resource"))
        self.graph.grid()

        # group extraction
        self.extraction_group.curve = self.graph.plot(
            self.extraction_group.xdata, self.extraction_group.ydata,
            "-k", label=trans_DYNCPR("Group extraction"))

        # stock of resource
        self.resource.curve = self.graph.plot(
            self.resource.xdata, self.resource.ydata,
            "-g", label=trans_DYNCPR("Stock of resource"))

    def update_resource(self):
        self.resource.curve.set_data(
            self.resource.xdata, self.resource.ydata)
        self.fig.canvas.draw()

    def update_extraction_group(self):
        self.extraction_group.curve.set_data(
            self.extraction_group.xdata,
            self.extraction_group.ydata)
        self.fig.canvas.draw()


class GuiDecision(QtGui.QDialog):
    def __init__(self, defered, automatique, parent, period, historique):
        super(GuiDecision, self).__init__(parent)

        # variables
        self._defered = defered
        self._automatique = automatique
        self._historique = GuiHistorique(self, historique)

        layout = QtGui.QVBoxLayout(self)

        # should be removed if one-shot game
        wperiod = WPeriod(
            period=period, ecran_historique=self._historique)
        layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_DYNCPR.get_text_explanation(),
            size=(450, 80), parent=self)
        layout.addWidget(wexplanation)

        self.graphical_zone = PlotWidget()
        layout.addWidget(self.graphical_zone)

        self._wdecision = WSpinbox(
            label=texts_DYNCPR.get_text_label_decision(),
            minimum=pms.DECISION_MIN, maximum=pms.DECISION_MAX,
            interval=pms.DECISION_STEP, automatique=self._automatique,
            parent=self)
        layout.addWidget(self._wdecision)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

        self.setWindowTitle(trans_DYNCPR(u"Décision"))
        self.adjustSize()
        self.setFixedSize(self.size())

        if self._automatique:
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
        decision = self._wdecision.get_value()
        if not self._automatique:
            confirmation = QtGui.QMessageBox.question(
                self, le2mtrans(u"Confirmation"),
                le2mtrans(u"Do you confirm your choice?"),
                QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            if confirmation != QtGui.QMessageBox.Yes: 
                return
        logger.info(u"Send back {}".format(decision))
        self.accept()
        self._defered.callback(decision)


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

        # nombre de périodes
        self._spin_periods = QtGui.QSpinBox()
        self._spin_periods.setMinimum(0)
        self._spin_periods.setMaximum(100)
        self._spin_periods.setSingleStep(1)
        self._spin_periods.setValue(pms.NOMBRE_PERIODES)
        self._spin_periods.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_periods.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Nombre de périodes"), self._spin_periods)

        # periode essai
        self._checkbox_essai = QtGui.QCheckBox()
        self._checkbox_essai.setChecked(pms.PERIODE_ESSAI)
        form.addRow(QtGui.QLabel(u"Période d'essai"), self._checkbox_essai)

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
