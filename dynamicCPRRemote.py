# -*- coding: utf-8 -*-

# built-in
import logging
import random
from twisted.internet import defer
import numpy as np
from PyQt4.QtCore import QTimer, pyqtSignal, QObject

# le2m
from client.cltremote import IRemote

# dynamicCPR
import dynamicCPRParams as pms
from dynamicCPRGui import GuiDecision, GuiInitialExtraction, GuiSummary
import dynamicCPRTexts as texts_DYNCPR


logger = logging.getLogger("le2m")


class RemoteDYNCPR(IRemote, QObject):

    end_of_time = pyqtSignal()

    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        QObject.__init__(self)

    def __init_vars(self):
        self.start_time = None
        self.extractions_indiv = dict()  # the players + the other group members
        self.extraction_group = PlotData()
        self.cost = PlotData()
        self.resource = PlotData()
        self.payoff_instant = PlotData()
        self.payoff_part = PlotData()
        self.text_infos = u""
        for j in self.group_members:
            self.extractions_indiv[j] = PlotData()
        self.decision_screen = None

    def remote_configure(self, params, server_part, group_members):
        """
        Set the same parameters as in the server side
        :param params:
        :return:
        """
        logger.info(u"{} configure".format(self.le2mclt))
        self.server_part = server_part
        self.group_members = group_members
        for k, v in params.items():
            setattr(pms, k, v)
        self.__init_vars()

    def remote_newperiod(self, period):
        """
        Set the current period and delete the history
        :param period: the current period
        :return:
        """
        logger.info(u"{} Period {}".format(self.le2mclt, period))
        self.currentperiod = period
        # if self.currentperiod <= 1:
        #     del self.histo[:]
        #     self.histo_vars = texts_DYNCPR.get_histo_vars()
        #     self.histo.append(texts_DYNCPR.get_histo_head())

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
            screen = GuiInitialExtraction(self, defered)
            screen.show()
            return defered

    def remote_display_decision(self, time_start):
        """
        Display the decision screen
        :param time_start: the time is given by the server
        :return: deferred
        """

        self.start_time = time_start

        # ----------------------------------------------------------------------
        # simulation
        # ----------------------------------------------------------------------

        if self._le2mclt.simulation:

            # ------------------------------------------------------------------
            # continuous
            # ------------------------------------------------------------------

            if pms.DYNAMIC_TYPE == pms.CONTINUOUS:

                def send_simulation():
                    extraction = float(np.random.choice(
                        np.arange(pms.DECISION_MIN, pms.DECISION_MAX,
                                  pms.DECISION_STEP)))
                    logger.info(u"{} Send {}".format(self._le2mclt.uid,
                                                     extraction))
                    self.server_part.callRemote("new_extraction",
                                                extraction)

                self.continuous_simulation_defered = defer.Deferred()
                self.continuous_simulation_timer = QTimer()
                self.continuous_simulation_timer.setInterval(
                    random.randint(2000, 10000))
                self.continuous_simulation_timer.timeout.connect(
                    send_simulation)
                self.continuous_simulation_timer.start()

                return self.continuous_simulation_defered

            # ------------------------------------------------------------------
            # discrete
            # ------------------------------------------------------------------

            elif pms.DYNAMIC_TYPE == pms.DISCRETE:
                extraction = float(np.random.choice(
                    np.arange(pms.DECISION_MIN, pms.DECISION_MAX,
                              pms.DECISION_STEP)))
                logger.info(u"{} Send {}".format(self.le2mclt, extraction))
                return extraction

        # ----------------------------------------------------------------------
        # manual or automatic
        # ----------------------------------------------------------------------

        else:
            defered = defer.Deferred()
            if self.decision_screen is None:
                self.decision_screen = GuiDecision(self, defered)
                self.decision_screen.showFullScreen()
            else:
                self.decision_screen.defered = defered
                self.decision_screen.update_data_and_graphs()
            return defered

    def remote_update_data(self, group_members_extractions, group_extraction,
                           the_time):
        """
        called by the server:
        - every second if dynamic == continuous
        - every period if dynamic == discrete
        :param group_members_extractions:
        :param group_extraction: the total extraction of the group
        :param resource_stock: the stock of resource
        :param the_time: the time of the update
        :return:
        """

        # ----------------------------------------------------------------------
        # we set the same time for every player in the group
        # ----------------------------------------------------------------------
        if self.currentperiod == 0:
            xdata = 0
        else:
            if pms.DYNAMIC_TYPE == pms.DISCRETE:
                xdata = self.currentperiod
            elif pms.DYNAMIC_TYPE == pms.CONTINUOUS:
                xdata = the_time

        # ----------------------------------------------------------------------
        # group extraction
        # ----------------------------------------------------------------------
        self.extraction_group.add_x(xdata)
        self.extraction_group.add_y(group_extraction["DYNCPR_group_extraction"])
        try:
            self.extraction_group.update_curve()
        except AttributeError:
            pass

        # ----------------------------------------------------------------------
        # resource
        # ----------------------------------------------------------------------
        self.resource.add_x(xdata)
        self.resource.add_y(group_extraction["DYNCPR_resource_stock"])
        try:
            self.resource.update_curve()
        except AttributeError:
            pass

        # ----------------------------------------------------------------------
        # group members' extractions
        # ----------------------------------------------------------------------
        for k, v in group_members_extractions.items():
            self.extractions_indiv[k].add_x(xdata)
            self.extractions_indiv[k].add_y(v["DYNCPR_extraction"])
            try:
                self.extractions_indiv[k].update_curve()
            except AttributeError:  # if period==0
                pass

        # ----------------------------------------------------------------------
        # player's cost
        # ----------------------------------------------------------------------
        self.cost.add_x(xdata)
        self.cost.add_y(group_members_extractions[self.le2mclt.uid]
                        ["DYNCPR_cost"])

        # ----------------------------------------------------------------------
        # player's payoff
        # ----------------------------------------------------------------------
        self.payoff_instant.add_x(xdata)
        self.payoff_instant.add_y(group_members_extractions[self.le2mclt.uid]
                                  ["DYNCPR_payoff"])
        cumulative_payoff = pms.get_cumulative_payoff(
            xdata, self.payoff_instant.ydata)
        infinite_payoff = pms.get_infinite_payoff(
            xdata,
            group_members_extractions[self.le2mclt.uid]["DYNCPR_extraction"],
            group_extraction["DYNCPR_group_extraction"],
            group_extraction["DYNCPR_resource_stock"])
        self.payoff_part.add_x(xdata)
        self.payoff_part.add_y(cumulative_payoff + infinite_payoff)
        try:
            self.payoff_part.update_curve()
        except AttributeError:  # if period or instant == 0
            pass

        # ----------------------------------------------------------------------
        # text information
        # ----------------------------------------------------------------------
        old = self.text_infos
        the_time_str = texts_DYNCPR.trans_DYNCPR(u"Instant") if \
            pms.DYNAMIC_TYPE == pms.CONTINUOUS else \
            texts_DYNCPR.trans_DYNCPR(u"Period")
        self.text_infos = the_time_str + u": {}".format(int(xdata)) + \
            u"<br>" + texts_DYNCPR.trans_DYNCPR(u"Your extraction") + \
            u": {:.2f}".format(self.extractions_indiv[self.le2mclt.uid].ydata[-1]) + \
            u"<br>" + texts_DYNCPR.trans_DYNCPR(u"Pair extraction") + \
            u": {:.2f}".format(self.extraction_group.ydata[-1]) + \
            u"<br>" + texts_DYNCPR.trans_DYNCPR(u"Available resource") + \
            u": {:.2f}".format(self.resource.ydata[-1]) + \
            u"<br>" + texts_DYNCPR.trans_DYNCPR(u"Instant payoff") + \
            u": {:.2f}".format(self.payoff_instant.ydata[-1]) + \
            u"<br>" + texts_DYNCPR.trans_DYNCPR(u"Cumulative payoff") + \
            u": {:.2f}".format(cumulative_payoff) + \
            u"<br>" + texts_DYNCPR.trans_DYNCPR(u"Part payoff") + \
            u": {:.2f}".format(self.payoff_part.ydata[-1])
        self.text_infos += u"<br>{}<br>{}".format(20*"-", old)

        # ----------------------------------------------------------------------
        # log
        # ----------------------------------------------------------------------
        logger.info("{} update group {:.2f} resource {:.2f} payoff: {:.2f}".format(
            self.le2mclt, self.extraction_group.ydata[-1],
            self.resource.ydata[-1], self.payoff_part.ydata[-1]))

    def remote_end_update_data(self):
        logger.debug("{}: call of remote_end_update_data".format(self.le2mclt))

        # __ if continuous simulation __
        if self.le2mclt.simulation and pms.DYNAMIC_TYPE == pms.CONTINUOUS:
            self.continuous_simulation_timer.stop()
            self.continuous_simulation_defered.callback(None)

        self.end_of_time.emit()

    def remote_display_summary(self, period_content):
        """
        Display the summary screen
        :param period_content: dictionary with the content of the current period
        :return: deferred
        """
        logger.info(u"{} Summary".format(self._le2mclt.uid))
        # self.histo.append([period_content.get(k) for k in self.histo_vars])
        if self._le2mclt.simulation:
            logger.info("{} send curves".format(self.le2mclt))
            extrac_indiv = self.extractions_indiv[self.le2mclt.uid]
            return {
                "extractions": zip(extrac_indiv.xdata, extrac_indiv.ydata),
                "payoffs": zip(self.payoff_part.xdata, self.payoff_part.ydata),
                "cost": zip(self.remote.cost.xdata, self.remote.cost.ydata)
            }
        else:
            defered = defer.Deferred()
            part_payoff = float(self.payoff_part.ydata[-1]) * pms.TAUX_CONVERSION
            summary_screen = GuiSummary(
                self, defered, texts_DYNCPR.get_text_summary(part_payoff))
            summary_screen.showFullScreen()
            return defered


# ==============================================================================
# PLOT DATA
# ==============================================================================


class PlotData():
    def __init__(self):
        self.xdata = []
        self.ydata = []
        self.curve = None

    def add_x(self, val):
        self.xdata.append(val)

    def add_y(self, val):
        self.ydata.append(val)

    def update_curve(self):
        self.curve.set_data(self.xdata, self.ydata)


