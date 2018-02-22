# -*- coding: utf-8 -*-

import logging
import random
from twisted.internet import defer
import numpy as np
from PyQt4.QtCore import QTimer

from client.cltremote import IRemote
from client.cltgui.cltguidialogs import GuiRecapitulatif

import dynamicCPRParams as pms
from dynamicCPRGui import GuiDecision
import dynamicCPRTexts as texts_DYNCPR


logger = logging.getLogger("le2m")


class RemoteDYNCPR(IRemote):
    """
    Class remote, remote_ methods can be called by the server
    """
    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        self.__extractions_indiv = dict()
        self.__extraction_group = PlotData()
        self.__resource = PlotData()
        self.__resource.xdata = 0
        self.__resource.ydata = pms.RESOURCE_INITIAL_STOCK
        # ---------------------------------------------------------------------
        # used for continuous time
        # ----------------------------------------------------------------------
        self.__start_time = None

    def remote_configure(self, params, server_part, group_members):
        """
        Set the same parameters as in the server side
        :param params:
        :return:
        """
        logger.info(u"{} configure".format(self.le2mclt))
        self.__server_part = server_part
        self.__group_members = group_members
        for k, v in params.items():
            setattr(pms, k, v)
        # we create a data plot for each group member
        for j in self.__group_members:
            self.__extractions_indiv[j] = PlotData()

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

    @defer.inlineCallbacks
    def remote_set_initial_extraction(self):
        """
        the player set his initial extraction, before to start the game
        :return:
        """
        if self.le2mclt.simulation:
            extraction = float(np.random.choice(
                np.arange(pms.DECISION_MIN, pms.DECISION_MAX,
                          pms.DECISION_STEP)))
            logger.info(u"{} Send {}".format(self._le2mclt.uid,
                                             extraction))
            yield (self.__server_part.callRemote(
                "new_extraction", extraction))
        else:
            pass  # todo: display a screen

    def remote_display_decision(self, time_start):
        """
        Display the decision screen
        :return: deferred
        """
        self.__start_time = time_start

        if self._le2mclt.simulation:

            def send_simulation():
                extraction = float(np.random.choice(
                    np.arange(pms.DECISION_MIN, pms.DECISION_MAX,
                              pms.DECISION_STEP)))
                logger.info(u"{} Send {}".format(self._le2mclt.uid,
                                                 extraction))
                self.__server_part.callRemote("new_extraction",
                                              extraction)

            # __ CONTINU __
            if pms.DYNAMIC_TYPE == pms.CONTINUOUS:

                self.__continuous_simulation_defered = defer.Deferred()
                self.__continuous_simulation_timer = QTimer()
                self.__continuous_simulation_timer.setInterval(
                    random.randint(2000, 10000))
                self.__continuous_simulation_timer.timeout.connect(
                    send_simulation)
                self.__continuous_simulation_timer.start()

                return self.__continuous_simulation_defered

            # __ DISCRET __
            elif pms.DYNAMIC_TYPE == pms.DISCRETE:
                extraction = float(np.random.choice(
                    np.arange(pms.DECISION_MIN, pms.DECISION_MAX,
                              pms.DECISION_STEP)))
                logger.info(u"{} Send {}".format(self.le2mclt, extraction))
                return extraction

        else:
            defered = defer.Deferred()
            ecran_decision = GuiDecision(
                defered, self._le2mclt.automatique,
                self._le2mclt.screen, self.currentperiod, self.histo)
            # used only in the continuous treatment
            self.new_extraction_signal.connect(ecran_decision.new_extraction)
            ecran_decision.show()
            return defered

    def remote_update_data(self, group_members_extractions, group_extraction,
                           resource_stock):
        """
        called by the players as soon as there is a new extraction in the
        group.
        Used only in the continuous treatment
        :param group_members_extractions:
        :param group_extraction:
        :return:
        """
        # we set the same time
        if self.currentperiod == 0:
            xdata = 0
        else:
            xdata = (group_extraction["time"] - self.__start_time).total_seconds()

        # group extraction
        self.__extraction_group.xdata = xdata
        self.__extraction_group.ydata = group_extraction["extraction"]
        try:
            self.__extraction_group.update_curve()
        except AttributeError:
            pass

        # resource
        self.__resource.xdata = xdata
        self.__resource.ydata = resource_stock
        try:
            self.__resource.update_curve()
        except AttributeError:
            pass

        # individual extractions
        for k, v in group_members_extractions.items():
            self.__extractions_indiv[k].xdata = xdata
            self.__extractions_indiv[k].ydata = v["extraction"]
            try:
                self.__extractions_indiv[k].update_curve()
            # if period==0 or simulation then there is no curve
            except AttributeError:
                pass

        logger.debug("{} update_data: Group: {} - Resource: {}".format(
            self.le2mclt, self.__extraction_group.ydata, self.__resource.ydata))

    def remote_end_update_data(self):
        logger.debug("{}: call of remote_end_data".format(self.le2mclt))
        self.continue_loop = False

        # __ if continuous simulation __
        try:
            self.__continuous_simulation_timer.stop()
            self.__continuous_simulation_defered.callback(None)
        except AttributeError:
            pass

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


# ==============================================================================
# PLOT DATA
# ==============================================================================


class PlotData():
    def __init__(self):
        self._xdata = []
        self._ydata = []
        self._curve = None

    # --------------------------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------------------

    def update_curve(self):
        self._curve.set_data(self._xdata, self._ydata)


