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
from dynamicCPRPart import ExtractionsDYNCPR

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
        self.DYNCPR_trial = pms.PARTIE_ESSAI
        self.__players = player_list

        # ----------------------------------------------------------------------
        # instantiations
        # ----------------------------------------------------------------------
        for p in self.players_part:
            p.DYNCPR_group = self.uid
        self.current_period = 0
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
            the_time = int((datetime.now() - self.time_start).total_seconds())
        except TypeError:
            the_time = 0

        # ----------------------------------------------------------------------
        # compute the group extraction
        # ----------------------------------------------------------------------
        group_extrac = sum(
            [e.DYNCPR_extraction for e in self.current_players_extractions.values()])

        # ----------------------------------------------------------------------
        # check extractions
        # ----------------------------------------------------------------------
        if group_extrac > self.current_resource:
            for j in self.players_part:
                j.current_extraction = ExtractionsDYNCPR(0, the_time)
                self.le2mserv.gestionnaire_base.ajouter(j.current_extraction)
                j.currentperiod.extractions.append(j.current_extraction)
                self.current_players_extractions[j.joueur.uid] = \
                    j.current_extraction
            group_extrac = sum([e.DYNCPR_extraction for e in
                                self.current_players_extractions.values()])

        # ----------------------------------------------------------------------
        # compute individual payoffs (at instant t)
        # ----------------------------------------------------------------------
        for j in self.players_part:
            j_extrac = j.current_extraction.DYNCPR_extraction
            j.current_extraction.DYNCPR_benefice = \
                pms.param_a * j_extrac - (pms.param_b / 2) * \
                pow(j_extrac, 2)
            cost = j_extrac * (pms.param_c0 - pms.param_c1 * self.current_resource)
            if cost < 0 :
                cost = 0
            j.current_extraction.DYNCPR_cost = cost
            j.current_extraction.DYNCPR_payoff = \
                j.current_extraction.DYNCPR_benefice - \
                j.current_extraction.DYNCPR_cost

        # ----------------------------------------------------------------------
        # compute the new available resource
        # ----------------------------------------------------------------------
        self.current_resource += pms.RESOURCE_GROWTH
        self.current_resource -= group_extrac
        for j in self.players_part:
            j.current_extraction.DYNCPR_resource = self.current_resource

        # ----------------------------------------------------------------------
        # save the group extraction with the resource stock
        # ----------------------------------------------------------------------
        self.current_extraction = GroupExtractionDYNCPR(
            self.current_period, the_time, group_extrac, self.current_resource)
        self.le2mserv.gestionnaire_base.ajouter(self.current_extraction)
        self.extractions.append(self.current_extraction)
        logger.debug(
            "{} update_data extraction {:.2f} - resource {:.2f}".format(
                self, self.current_extraction.DYNCPR_group_extraction,
                self.current_resource))

        # ----------------------------------------------------------------------
        # update the remote
        # ----------------------------------------------------------------------
        cur_player_extrac_dict = {k: v.to_dict() for k, v in
                                  self.current_players_extractions.items()}

        for j in self.players_part:
            j.remote.callRemote(
                "update_data", cur_player_extrac_dict,
                self.current_extraction.to_dict(), the_time)

    def add_extraction(self, player, extraction):
        """

        :param player: the player at the origin of the extraction
        :param extraction: the amount extracted (Float)
        :param period: the period number
        :return:
        """
        self.current_players_extractions[player.uid] = extraction
        group_extrac = sum(
            [e.DYNCPR_extraction for e in self.current_players_extractions.values()])

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
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return "{}".format(self.DYNCPR_group_extraction)