from server.servbase import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime


class DYNCPRGroup(object):
    __tablename__ = "group_dynamicCPR"
    id = Column(Integer, primary_key=True)
    players = relationship("partie_dynamicCPR")

    def __init__(self, group_id, player_list):
        self.id = group_id
        self.players = player_list
        self.players_extractions = {p: 0 for p in self.players}
        self.current_extraction = 0

    def set_extraction(self, player, extraction):
        self.players_extractions[player] = extraction
        self.current_extraction = sum([e for e in self.players_extractions.values()])


