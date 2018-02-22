# -*- coding: utf-8 -*-

from server.servbase import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from twisted.internet import defer
import time
import logging
from util.utiltools import RepeatedTimer

import dynamicCPRParams as pms
from dynamicCPRUtil import ThreadForRepeatedAction

logger = logging.getLogger("le2m")


class GroupDYNCPR(Base):
    __tablename__ = "group_dynamicCPR"
    uid = Column(String(30), primary_key=True)
    session_id = Column(Integer)
    DYNCPR_sequence = Column(Integer)
    DYNCPR_treatment = Column(Integer)
    extractions = relationship("GroupExtractionDYNCPR")

    def __init__(self, le2mserv, group_id, player_list, sequence):
        self.le2mserv = le2mserv
        self.uid = group_id
        self.session_id = self.le2mserv.gestionnaire_base.session.id
        self.DYNCPR_sequence = sequence
        self.DYNCPR_treatment = pms.TREATMENT
        self._players = player_list
        self._current_players_extractions = dict()
        self._current_extraction = None
        self._current_resource = pms.RESOURCE_INITIAL_STOCK
        self._thread_update = ThreadForRepeatedAction(5, self.update_data)

    @property
    def players(self):
        """
        return a copy of the players' list
        :return:
        """
        return self._players[:]

    @property
    def players_uid(self):
        """
        return only the uid
        :return:
        """
        return [p.uid for p in self.players]

    @property
    def players_part(self):
        """
        return the dynamicCPR part of players
        :return:
        """
        return [j.get_part("dynamicCPR") for j in self.players]

    @property
    def thread_update(self):
        return  self._thread_update

    def add_extraction(self, player, extraction, period):
        """

        :param player: the player at the origin of the extraction
        :param extraction: the amount extracted (Float)
        :param period: if discret, the period number. If continuous call the
        method without this arg
        :return:
        """
        self._current_players_extractions[player] = extraction.to_dict()
        group_extrac = sum([e["extraction"] for e in
                            self._current_players_extractions.values()])
        self._current_resource -= group_extrac
        self._current_extraction = GroupExtractionDYNCPR(
            period, extraction.DYNCPR_extraction_time, group_extrac,
            self._current_resource)
        self.le2mserv.gestionnaire_base.ajouter(self._current_extraction)
        self.extractions.append(self._current_extraction)
        self.le2mserv.gestionnaire_graphique.infoserv("G{}: {}".format(
            self.uid_short, self._current_extraction.DYNCPR_group_extraction))

    @property
    def current_extraction(self):
        return self._current_extraction.to_dict()

    @property
    def current_players_extractions(self):
        return self._current_players_extractions.copy()

    @property
    def current_resource(self):
        return self._current_resource

    @property
    def uid_short(self):
        return self.uid.split("_")[2]

    @defer.inlineCallbacks
    def update_data(self):
        logger.debug("call of update_data")
        for j in self.players_part:
            yield (j.remote.callRemote(
                "update_data", self.current_players_extractions,
                self.current_extraction, self.current_resource))

    @defer.inlineCallbacks
    def end_update_data(self):
        logger.debug("call of end_update_data")
        # self.repeated_timer.stop()
        for j in self.players_part:
            j.remote.callRemote("end_update_data")


class GroupExtractionDYNCPR(Base):
    __tablename__ = "group_dynamicCPR_extractions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_uid = Column(String, ForeignKey("group_dynamicCPR.uid"))

    DYNCPR_period = Column(Integer, default=None)
    DYNCPR_time = Column(DateTime, default=None)
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