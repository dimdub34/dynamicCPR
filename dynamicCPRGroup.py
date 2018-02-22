# -*- coding: utf-8 -*-

from server.servbase import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
import logging
from PyQt4.QtCore import QTimer

import dynamicCPRParams as pms

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
        self.__players = player_list
        self.__current_players_extractions = dict()
        self.__current_extraction = None
        self.__current_resource = pms.RESOURCE_INITIAL_STOCK
        self.__timer_update = QTimer()
        self.__timer_update.setInterval(1000)
        self.__timer_update.timeout.connect(self.__update_data)

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
        return [j.get_part("dynamicCPR") for j in self.__players]

    @property
    def players_uid(self):
        """
        return only the uid
        :return:
        """
        return [p.uid for p in self.__players]

    @property
    def current_extraction(self):
        return self.__current_extraction.to_dict()

    @property
    def timer_update(self):
        return self.__timer_update

    @property
    def uid_short(self):
        return self.uid.split("_")[2]

    def __repr__(self):
        return "G{}".format(self.uid_short)

    # --------------------------------------------------------------------------
    # METHODS
    # --------------------------------------------------------------------------

    def __update_data(self):
        self.__current_resource *= pms.RESOURCE_GROWTH_RATE
        self.__current_resource -= self.__current_extraction.DYNCPR_group_extraction
        logger.debug("{} update_data extraction {} - resource {}".format(
            self, self.current_extraction, self.__current_resource))
        for j in self.players_part:
            j.remote.callRemote(
                "update_data", self.__current_players_extractions,
                self.current_extraction, self.__current_resource)

    def add_extraction(self, player, extraction, period):
        """

        :param player: the player at the origin of the extraction
        :param extraction: the amount extracted (Float)
        :param period: if discret, the period number. If continuous call the
        method without this arg
        :return:
        """
        self.__current_players_extractions[player] = extraction.to_dict()
        group_extrac = sum([e["extraction"] for e in
                            self.__current_players_extractions.values()])
        self.__current_resource -= group_extrac
        self.__current_extraction = GroupExtractionDYNCPR(
            period, extraction.DYNCPR_extraction_time, group_extrac,
            self.__current_resource)
        self.le2mserv.gestionnaire_base.ajouter(self.__current_extraction)
        self.extractions.append(self.__current_extraction)
        self.le2mserv.gestionnaire_graphique.infoserv("G{}: {}".format(
            self.uid_short, self.__current_extraction.DYNCPR_group_extraction))


# ==============================================================================
# EXTRACTIONS
# ==============================================================================


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