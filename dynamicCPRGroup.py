from server.servbase import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime


class DYNCPRGroup(Base):
    __tablename__ = "group_dynamicCPR"
    uid = Column(String(30), primary_key=True)
    session_id = Column(Integer)
    DYNCPR_sequence = Column(Integer)
    extractions = relationship("DYNCPRGroupExtraction")

    def __init__(self, le2mserv, group_id, player_list, sequence=0):
        self.le2mserv = le2mserv
        self.uid = group_id
        self.session_id = self.le2mserv.gestionnaire_base.session.id
        self._players = player_list
        self.DYNCPR_sequence = sequence
        self._current_players_extractions = dict()
        self._current_extraction = None

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

    def add_extraction(self, player, extraction, period=None):
        """

        :param player: the player at the origin of the extraction
        :param extraction: the amount extracted (Float)
        :param period: if discret, the period number. If continuous call the
        method without this arg
        :return:
        """
        self._current_players_extractions[player] = extraction.to_dict()
        self._current_extraction = DYNCPRGroupExtraction(
            period, extraction.DYNCPR_extraction_time,
            sum([e["extraction"] for e in self._current_players_extractions.values()]))
        self.le2mserv.gestionnaire_base.ajouter(self._current_extraction)
        self.extractions.append(self._current_extraction)

    @property
    def current_extraction(self):
        return self._current_extraction.to_dict()

    @property
    def current_players_extractions(self):
        return self._current_players_extractions.copy()


class DYNCPRGroupExtraction(Base):
    __tablename__ = "group_dynamicCPR_extractions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_uid = Column(String, ForeignKey("group_dynamicCPR.uid"))

    DYNCPR_period = Column(Integer, default=None)
    DYNCPR_time = Column(DateTime, default=None)
    DYNCPR_group_extraction = Column(Float, default=0)

    def __init__(self, period, time, value):
        self.DYNCPR_period = period
        self.DYNCPR_time = time
        self.DYNCPR_group_extraction = value

    def to_dict(self):
        return {
            "period": self.DYNCPR_period,
            "time": self.DYNCPR_time,
            "extraction": self.DYNCPR_group_extraction
        }