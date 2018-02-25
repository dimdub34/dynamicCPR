# -*- coding: utf-8 -*-

import logging
import random
from twisted.internet import defer
import numpy as np
from PyQt4.QtCore import QTimer

from client.cltremote import IRemote
from client.cltgui.cltguidialogs import GuiRecapitulatif

import dynamicCPRParams as pms
from dynamicCPRGui import GuiDecision, GuiInitialExtraction
import dynamicCPRTexts as texts_DYNCPR


logger = logging.getLogger("le2m")


class RemoteDYNCPR(IRemote):
    """
    Class remote, remote_ methods can be called by the server
    """
    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        self.__extractions_indiv = dict()

    def __init_vars(self):
        self.__start_time = None
        self.__extraction_group = PlotData()
        self.__resource = PlotData()
        for j in self.__group_members:
            self.__extractions_indiv[j] = PlotData()

    # --------------------------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------------------------
    @property
    def individual_extractions(self):
        return self.__extractions_indiv

    @property
    def group_extraction(self):
        return self.__extraction_group

    @property
    def resource(self):
        return self.__resource

    # --------------------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------------------

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
        self.__init_vars()

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

    def remote_set_initial_extraction(self):
        """
        the player set his initial extraction, before to start the game
        :return:
        """
        if self.le2mclt.simulation:
            extraction = float(np.random.choice(
                np.arange(pms.DECISION_MIN, pms.DECISION_MAX,
                          pms.DECISION_STEP)))
            logger.info(u"{} Send {}".format(self.le2mclt, extraction))
            return extraction
        else:
            defered = defer.Deferred()
            screen = GuiInitialExtraction(
                self.le2mclt.screen, defered, self.le2mclt.automatique)
            screen.show()
            return defered

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
                defered, self.le2mclt.automatique,
                self.le2mclt.screen, self.currentperiod, self.histo,
                self.individual_extractions, self.group_extraction, self.resource)
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
            if pms.DYNAMIC_TYPE == pms.DISCRETE:
                xdata = self.currentperiod
            elif pms.DYNAMIC_TYPE == pms.CONTINUOUS:
                xdata = (group_extraction["time"] -
                         self.__start_time).total_seconds()

        # group extraction
        self.__extraction_group.xdata.append(xdata)
        self.__extraction_group.ydata.append(group_extraction["extraction"])
        try:
            self.__extraction_group.update_curve()
        except AttributeError:
            pass
        logger.debug("extraction_group: xdata: {}, ydata: {}, curve: {}".format(
            self.__extraction_group.xdata, self.__extraction_group.ydata,
            self.__extraction_group.curve))

        # resource
        self.__resource.xdata.append(xdata)
        self.__resource.ydata.append(resource_stock)
        try:
            self.__resource.update_curve()
        except AttributeError:
            pass
        logger.debug("resource: xdata: {}, ydata: {}, curve: {}".format(
            self.__resource.xdata, self.__resource.ydata,
            self.__resource.curve))

        # individual extractions
        for k, v in group_members_extractions.items():
            self.__extractions_indiv[k].xdata.append(xdata)
            self.__extractions_indiv[k].ydata.append(v["extraction"])
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
        self.xdata = []
        self.ydata = []
        self.__curve = None

    # --------------------------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------------------------


    @property
    def curve(self):
        return self.__curve

    @curve.setter
    def curve(self, val):
        self.__curve = val

    # --------------------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------------------

    def update_curve(self):
        self.__curve.set_data(self.xdata, self.ydata)


