# -*- coding: utf-8 -*-

import logging
import random

from twisted.internet import defer
from twisted.spread import pb
from client.cltremote import IRemote
from client.cltgui.cltguidialogs import GuiRecapitulatif
import dynamicCPRParams as pms
from dynamicCPRGui import GuiDecision
import dynamicCPRTexts as texts_DYNCPR
from datetime import datetime
from blinker import signal


logger = logging.getLogger("le2m")


class PlotData():
    def __init__(self):
        self._xdata = []
        self._ydata = []
        self._curve = None

    @property
    def xdata(self):
        return self._xdata

    @xdata.setter
    def xdata(self, val):
        self._xdata.append(val)

    @property
    def ydata(self):
        return self._ydata

    @ydata.setter
    def ydata(self, val):
        self._ydata.append(val)

    @property
    def curve(self):
        return self._curve

    @curve.setter
    def curve(self, val):
        self._curve = val

    def update_curve(self):
        self._curve.set_data(self._xdata, self._ydata)


class RemoteDYNCPR(IRemote):
    """
    Class remote, remote_ methods can be called by the server
    """
    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        self.extractions_indiv = dict()
        self.extraction_group = PlotData()
        self.resource = PlotData()
        # ---------------------------------------------------------------------
        # used for continuous time
        # ----------------------------------------------------------------------
        self.start_time = None
        self.new_extraction_signal = signal("new_extraction")

    def remote_configure(self, params):
        """
        Set the same parameters as in the server side
        :param params:
        :return:
        """
        logger.info(u"{} configure".format(self._le2mclt.uid))
        for k, v in params.viewitems():
            setattr(pms, k, v)
        for i in range(pms.TAILLE_GROUPES):
            self.extractions_indiv[i] = PlotData()

    def remote_newperiod(self, period):
        """
        Set the current period and delete the history
        :param period: the current period
        :return:
        """
        logger.info(u"{} Period {}".format(self._le2mclt.uid, period))
        self.currentperiod = period
        if self.currentperiod <= 1:
            del self.histo[:]
            self.histo_vars = texts_DYNCPR.get_histo_vars()
            self.histo.append(texts_DYNCPR.get_histo_head())
        if self.currentperiod == 1 and pms.TREATMENT == pms.CONTINUOUS:
            self.start_time = datetime.now()

    @defer.inlineCallbacks
    def remote_display_decision(self):
        """
        Display the decision screen
        :return: deferred
        """
        logger.info(u"{} Decision".format(self._le2mclt.uid))
        if self._le2mclt.simulation:
            if self.currentperiod == 0:
                decision = \
                    random.randrange(
                        pms.DECISION_MIN,
                        pms.DECISION_MAX + pms.DECISION_STEP,
                        pms.DECISION_STEP)
                logger.info(u"{} Send back {}".format(self._le2mclt.uid, decision))
                defer.returnValue(decision)
            else:
                start = datetime.now()
                end = datetime.now()
                while (end - start).total_seconds() >= \
                        pms.CONTINOUS_TIME_DURATION.total_seconds():
                    if random.random() <= 0.10:
                        pass # todo

        else:
            defered = defer.Deferred()
            ecran_decision = GuiDecision(
                defered, self._le2mclt.automatique,
                self._le2mclt.screen, self.currentperiod, self.histo)
            self.new_extraction_signal.connect(ecran_decision.new_extraction)
            ecran_decision.show()
            defer.returnValue(defered)

    def remote_new_extraction(self, group_members_extractions, group_extraction):
        """
        called by the players as soon as there is a new extraction in the
        group.
        Used only in the continuous treatment
        :param group_members_extractions:
        :param group_extraction:
        :return:
        """
        # we set the same time
        xdata = (datetime.now() - self.start_time).total_seconds()

        # group extraction
        self.extraction_group.xdata = xdata
        self.extraction_group.ydata = group_extraction["extraction"]
        self.extraction_group.update_curve()

        # individual extractions
        for k, v in group_members_extractions.items():
            self.extractions_indiv[k].xdata = xdata
            self.extractions_indiv[k].ydata = v
            self.extractions_indiv[k].update_curve()


    def remote_display_summary(self, period_content):
        """
        Display the summary screen
        :param period_content: dictionary with the content of the current period
        :return: deferred
        """
        logger.info(u"{} Summary".format(self._le2mclt.uid))
        self.histo.append([period_content.get(k) for k in self.histo_vars])
        if self._le2mclt.simulation:
            return 1
        else:
            defered = defer.Deferred()
            ecran_recap = GuiRecapitulatif(
                defered, self._le2mclt.automatique, self._le2mclt.screen,
                self.currentperiod, self.histo,
                texts_DYNCPR.get_text_summary(period_content))
            ecran_recap.show()
            return defered

