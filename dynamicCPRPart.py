# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from twisted.internet import defer
from twisted.spread import pb  # because some functions can be called remotely
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from server.servbase import Base
from server.servparties import Partie
from util.utiltools import get_module_attributes
import dynamicCPRParams as pms


logger = logging.getLogger("le2m")


class PartieDYNCPR(Partie, pb.Referenceable):
    __tablename__ = "partie_dynamicCPR"
    __mapper_args__ = {'polymorphic_identity': 'dynamicCPR'}
    partie_id = Column(Integer, ForeignKey('parties.id'), primary_key=True)
    repetitions = relationship('RepetitionsDYNCPR')

    def __init__(self, le2mserv, joueur):
        super(PartieDYNCPR, self).__init__(
            nom="dynamicCPR", nom_court="DYNCPR",
            joueur=joueur, le2mserv=le2mserv)
        self.DYNCPR_gain_ecus = 0
        self.DYNCPR_gain_euros = 0

    @defer.inlineCallbacks
    def configure(self):
        logger.debug(u"{} Configure".format(self.joueur))
        yield (self.remote.callRemote("configure", get_module_attributes(pms)))
        self.joueur.info(u"Ok")

    @defer.inlineCallbacks
    def newperiod(self, period):
        """
        Create a new period and inform the remote
        :param period:
        :return:
        """
        logger.debug(u"{} New Period".format(self.joueur))
        self.currentperiod = RepetitionsDYNCPR(period)
        self.currentperiod.DYNCPR_group = self.joueur.group
        self.le2mserv.gestionnaire_base.ajouter(self.currentperiod)
        self.repetitions.append(self.currentperiod)
        yield (self.remote.callRemote("newperiod", period))
        logger.info(u"{} Ready for period {}".format(self.joueur, period))

    @defer.inlineCallbacks
    def display_decision(self):
        """
        Display the decision screen on the remote
        Get back the decision
        :return:
        """
        logger.debug(u"{} Decision".format(self.joueur))
        debut = datetime.now()
        self.currentperiod.DYNCPR_decision = yield(self.remote.callRemote(
            "display_decision"))
        self.currentperiod.DYNCPR_decisiontime = (datetime.now() - debut).seconds
        self.joueur.info(u"{}".format(self.currentperiod.DYNCPR_decision))
        self.joueur.remove_waitmode()

    def compute_periodpayoff(self):
        """
        Compute the payoff for the period
        :return:
        """
        logger.debug(u"{} Period Payoff".format(self.joueur))
        self.currentperiod.DYNCPR_periodpayoff = 0

        # cumulative payoff since the first period
        if self.currentperiod.DYNCPR_period < 2:
            self.currentperiod.DYNCPR_cumulativepayoff = \
                self.currentperiod.DYNCPR_periodpayoff
        else: 
            previousperiod = self.periods[self.currentperiod.DYNCPR_period - 1]
            self.currentperiod.DYNCPR_cumulativepayoff = \
                previousperiod.DYNCPR_cumulativepayoff + \
                self.currentperiod.DYNCPR_periodpayoff

        # we store the period in the self.periodes dictionnary
        self.periods[self.currentperiod.DYNCPR_period] = self.currentperiod

        logger.debug(u"{} Period Payoff {}".format(
            self.joueur,
            self.currentperiod.DYNCPR_periodpayoff))

    @defer.inlineCallbacks
    def display_summary(self, *args):
        """
        Send a dictionary with the period content values to the remote.
        The remote creates the text and the history
        :param args:
        :return:
        """
        logger.debug(u"{} Summary".format(self.joueur))
        yield(self.remote.callRemote(
            "display_summary", self.currentperiod.todict()))
        self.joueur.info("Ok")
        self.joueur.remove_waitmode()

    @defer.inlineCallbacks
    def compute_partpayoff(self):
        """
        Compute the payoff for the part and set it on the remote.
        The remote stores it and creates the corresponding text for display
        (if asked)
        :return:
        """
        logger.debug(u"{} Part Payoff".format(self.joueur))

        self.DYNCPR_gain_ecus = self.currentperiod.DYNCPR_cumulativepayoff
        self.DYNCPR_gain_euros = float(self.DYNCPR_gain_ecus) * float(pms.TAUX_CONVERSION)
        yield (self.remote.callRemote(
            "set_payoffs", self.DYNCPR_gain_euros, self.DYNCPR_gain_ecus))

        logger.info(u'{} Payoff ecus {} Payoff euros {:.2f}'.format(
            self.joueur, self.DYNCPR_gain_ecus, self.DYNCPR_gain_euros))


    @defer.inlineCallbacks
    def remote_new_extraction(self, extraction):
        self.current_extraction = ExtractionsDYNCRP()
        self.current_extraction.DYNCRP_extraction = extraction
        self.le2mserv.gestionnaire_base.ajouter(self.current_extraction)
        self.currentperiod.extractions.append(self.current_extraction)



class RepetitionsDYNCPR(Base):
    __tablename__ = 'partie_dynamicCPR_repetitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    partie_partie_id = Column(Integer, ForeignKey("partie_dynamicCPR.partie_id"))
    extractions = relationship('ExtractionsDYNCPR')

    DYNCPR_period = Column(Integer)
    DYNCPR_period_start_time = Column(DateTime, default=datetime.now())
    DYNCPR_treatment = Column(Integer, default=pms.TREATMENT)
    DYNCPR_group = Column(Integer, default=None)
    DYNCPR_decision = Column(Integer, default=0)
    DYNCPR_decisiontime = Column(Integer, default=0)
    DYNCPR_periodpayoff = Column(Float, default=0)
    DYNCPR_cumulativepayoff = Column(Float, default=0)

    def __init__(self, period):
        self.DYNCPR_period = period

    def todict(self, joueur=None):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns
                if "DYNCPR" in c.name}
        if joueur:
            temp["joueur"] = joueur
        return temp


class ExtractionsDYNCRP(Base):
    """
    In each period the subject can do several extractions in the continuous time
    treatment
    """
    __tablename__ = "partie_dynamicCPR_extractions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(Integer, ForeignKey("partie_dynamicCPR_repetitions.id"))
    DYNCRP_extraction = Column(Float)
    DYNCRP_extraction_time = Column(DateTime, default=datetime.now())
