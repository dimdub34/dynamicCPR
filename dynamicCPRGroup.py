# -*- coding: utf-8 -*-

# built-in
from server.servbase import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Boolean
import logging
from PyQt4.QtCore import QTimer
from datetime import datetime

# dynamicCPR
import dynamicCPRParams as pms

logger = logging.getLogger("le2m")


class GroupDYNCPR(Base):
    __tablename__ = "group_dynamicCPR"
    uid = Column(String(30), primary_key=True)
    session_id = Column(Integer)
    DYNCPR_dynamic_type = Column(Integer)
    DYNCPR_trial = Column(Boolean)
    DYNCPR_sequence = Column(Integer)
    DYNCPR_treatment = Column(Integer)
    extractions = relationship("GroupExtractionDYNCPR")

    def __init__(self, le2mserv, group_id, player_list, sequence):
        self.le2mserv = le2mserv

        # ----------------------------------------------------------------------
        # fields of the table
        # ----------------------------------------------------------------------
        self.uid = group_id
        self.session_id = self.le2mserv.gestionnaire_base.session.id
        self.DYNCPR_dynamic_type = pms.DYNAMIC_TYPE
        self.DYNCPR_sequence = sequence
        self.DYNCPR_treatment = pms.TREATMENT
        self.DYNCRP_trial = pms.PARTIE_ESSAI
        self.__players = player_list

        # ----------------------------------------------------------------------
        # instantiations
        # ----------------------------------------------------------------------
        for p in self.players_part:
            p.DYNCPR_group = self.uid
        self.current_players_extractions = dict()
        self.current_extraction = None
        self.current_resource = pms.RESOURCE_INITIAL_STOCK
        self.time_start = None
        self.timer_update = QTimer()
        self.timer_update.setInterval(
            int(pms.TIMER_UPDATE.total_seconds())*1000)
        self.timer_update.timeout.connect(self.update_data)

    # --------------------------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------------------------

    @property
    def players(self):
        """
        return a copy of the players' list
        :return:
        """
        return self.__players[:]

    @property
    def players_part(self):
        """
        return the dynamicCPR part of players
        :return:
        """
        return [j.get_part("dynamicCPR") for j in self.players]

    @property
    def players_uid(self):
        """
        return only the uid
        :return:
        """
        return [p.uid for p in self.players]

    @property
    def uid_short(self):
        return self.uid.split("_")[2]

    def __repr__(self):
        return "G{}".format(self.uid_short)

    # --------------------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------------------

    def update_data(self):
        # after the initial extraction but before the game starts
        # self.time_start is None
        try:
            the_time = (datetime.now() - self.time_start).total_seconds()
        except TypeError:
            the_time = 0

        # ----------------------------------------------------------------------
        # compute and save the group extraction
        # ----------------------------------------------------------------------
        group_extrac = sum(
            [e["extraction"] for e in self.current_players_extractions.values()])
        self.current_extraction = GroupExtractionDYNCPR(
            0, the_time, group_extrac, self.current_resource)
        self.le2mserv.gestionnaire_base.ajouter(self.current_extraction)
        self.extractions.append(self.current_extraction)
        logger.debug(
            "{} update_data extraction {:.2f} - resource {:.2f}".format(
                self, self.current_extraction.DYNCPR_group_extraction,
                self.current_resource))

        # ----------------------------------------------------------------------
        # compute the resource
        # ----------------------------------------------------------------------
        self.current_resource += pms.RESOURCE_GROWTH
        self.current_resource -= self.current_extraction.DYNCPR_group_extraction
        if self.current_resource < 0:
            self.current_resource = 0

        # ----------------------------------------------------------------------
        # compute individual payoffs
        # ----------------------------------------------------------------------
        for j in self.players:
            try:
                j_extrac = self.current_players_extractions[j.uid]["extraction"]
                j_payoff = pms.param_a * j_extrac - (pms.param_b / 2) * \
                           pow(j_extrac, 2) - \
                           (pms.param_c0 - pms.param_c1 * self.current_resource) * j_extrac
                self.current_players_extractions[j.uid]["payoff"] = j_payoff
            except KeyError:
                pass  # only for the initial extraction

        # ----------------------------------------------------------------------
        # update the remote
        # ----------------------------------------------------------------------
        for j in self.players_part:
            j.remote.callRemote(
                "update_data", self.current_players_extractions,
                self.current_extraction.DYNCPR_group_extraction,
                self.current_resource, the_time)

    def add_extraction(self, player, extraction, period):
        """

        :param player: the player at the origin of the extraction
        :param extraction: the amount extracted (Float)
        :param period: the period number
        :return:
        """
        self.current_players_extractions[player.uid] = extraction.to_dict()
        group_extrac = sum(
            [e["extraction"] for e in self.current_players_extractions.values()])

        # ----------------------------------------------------------------------
        # if discrete save the extraction in the database, and compute
        # individual payoffs
        # if continuous it is saved in the update_data method
        # ----------------------------------------------------------------------
        if pms.DYNAMIC_TYPE == pms.DISCRETE:
            self.current_extraction = GroupExtractionDYNCPR(
                period, extraction.DYNCPR_extraction_time, group_extrac,
                self.current_resource)
            self.le2mserv.gestionnaire_base.ajouter(self.current_extraction)
            self.extractions.append(self.current_extraction)

        self.le2mserv.gestionnaire_graphique.infoserv("G{}: {}".format(
            self.uid_short, group_extrac))


# ==============================================================================
# EXTRACTIONS
# ==============================================================================


class GroupExtractionDYNCPR(Base):
    __tablename__ = "group_dynamicCPR_extractions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_uid = Column(String, ForeignKey("group_dynamicCPR.uid"))

    DYNCPR_period = Column(Integer, default=None)
    DYNCPR_time = Column(Integer)
    DYNCPR_group_extraction = Column(Float, default=0)
    DYNCPR_resource_stock = Column(Float)

    def __init__(self, period, time, value, resource):
        self.DYNCPR_period = period
        self.DYNCPR_time = time
        self.DYNCPR_group_extraction = value
        self.DYNCPR_resource_stock = resource

    def to_dict(self):
        return {
            "period": self.DYNCPR_period,
            "time": self.DYNCPR_time,
            "extraction": self.DYNCPR_group_extraction,
        }

    def __repr__(self):
        return "{}".format(self.DYNCPR_group_extraction)