# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
from twisted.internet import defer
from datetime import datetime
from PyQt4.QtCore import QTimer, QObject, pyqtSlot
from PyQt4.QtGui import QMessageBox

from util import utiltools
from util.utili18n import le2mtrans
from util.utiltools import get_module_attributes

import dynamicCPRParams as pms
from dynamicCPRGui import DConfigure
from dynamicCPRTexts import trans_DYNCPR
from dynamicCPRGroup import GroupDYNCPR


logger = logging.getLogger("le2m.{}".format(__name__))


class Serveur(QObject):

    def __init__(self, le2mserv):
        QObject.__init__(self)
        self.__le2mserv = le2mserv
        self.__current_sequence = 0
        self.__groups = []

        # __ MENU __
        actions = OrderedDict()
        actions["Configure"] = self._configure
        actions["Parameters"] = \
            lambda _: self.le2mserv.gestionnaire_graphique. \
            display_information2(
                utiltools.get_module_info(pms), le2mtrans(u"Parameters"))
        actions["Start"] = lambda _: self._demarrer()
        actions["Payoffs"] = \
            lambda _: self.le2mserv.gestionnaire_experience.\
            display_payoffs_onserver("dynamicCPR")
        self.le2mserv.gestionnaire_graphique.add_topartmenu(
            u"Dynamic CPR", actions)

    # --------------------------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------------------------

    @property
    def le2mserv(self):
        return self.__le2mserv

    def _configure(self):
        screen_conf = DConfigure(self.le2mserv.gestionnaire_graphique.screen)
        if screen_conf.exec_():
            pms_list = []
            for k, v in get_module_attributes(pms).items():
                if k in ["TREATMENT", "DYNAMIC_TYPE", "NOMBRE_PERIODES",
                         "PARTIE_ESSAI"]:
                    pms_list.append("{}: {}".format(k, v))
            self.le2mserv.gestionnaire_graphique.infoserv(pms_list)

    @defer.inlineCallbacks
    def _demarrer(self):

        # ----------------------------------------------------------------------
        # check conditions
        # ----------------------------------------------------------------------

        if not self.le2mserv.gestionnaire_graphique.question(
                        le2mtrans("Start") + " dynamicCPR?"):
            return

        # ----------------------------------------------------------------------
        # init part
        # ----------------------------------------------------------------------

        self.__current_sequence += 1

        # __ creates parts ___
        yield (self.le2mserv.gestionnaire_experience.init_part(
            "dynamicCPR", "PartieDYNCPR", "RemoteDYNCPR", pms,
            current_sequence=self.__current_sequence))
        self._tous = self.le2mserv.gestionnaire_joueurs.get_players(
            'dynamicCPR')

        # __ form groups __
        del self.__groups[:]
        try:
            gps = utiltools.form_groups(
                self.le2mserv.gestionnaire_joueurs.get_players(),
                pms.TAILLE_GROUPES, self.le2mserv.nom_session)
        except ValueError as e:
            QMessageBox.critical(None, "Group error", e.message)
            self.__current_sequence -= 1
            return
        logger.debug(gps)
        self.le2mserv.gestionnaire_graphique.infoserv(
            "Groups", bg="gray", fg="white")
        for g, m in gps.items():
            group = GroupDYNCPR(self.le2mserv, g, m, self.__current_sequence)
            self.le2mserv.gestionnaire_base.ajouter(group)
            self.__groups.append(group)
            self.le2mserv.gestionnaire_graphique.infoserv("__ {} __".format(group))
            for j in m:
                j.group = group
                self.le2mserv.gestionnaire_graphique.infoserv("{}".format(j))

        # __ set parameters on remotes (has to be after group formation) __
        yield (self.le2mserv.gestionnaire_experience.run_step(
            le2mtrans(u"Configure"), self._tous, "configure"))

        # ----------------------------------------------------------------------
        # SELECT THE INITIAL EXTRACTION
        # ----------------------------------------------------------------------

        self.le2mserv.gestionnaire_graphique.infoclt(trans_DYNCPR(
            u"Initial extraction"))
        yield (self.le2mserv.gestionnaire_experience.run_func(
            self._tous, "newperiod", 0))
        yield (self.le2mserv.gestionnaire_experience.run_step(
            trans_DYNCPR(u"Initial extraction"), self._tous,
            "set_initial_extraction"))
        for g in self.__groups:
            self.le2mserv.gestionnaire_graphique.infoserv("G{}: {}".format(
                g.uid_short, g.current_extraction["extraction"]))

        # ----------------------------------------------------------------------
        # DEPENDS ON TREATMENT
        # ----------------------------------------------------------------------

        if pms.DYNAMIC_TYPE == pms.CONTINUOUS:

            txt = le2mtrans(u"Period") + u" 1"
            self.le2mserv.gestionnaire_graphique.infoserv(
                txt, fg="white", bg="gray")
            self.le2mserv.gestionnaire_graphique.infoclt(
                txt, fg="white", bg="gray")
            yield (self.le2mserv.gestionnaire_experience.run_func(
                self._tous, "newperiod", 1))

            # __ timer continuous part __
            QTimer.singleShot(
                pms.CONTINUOUS_TIME_DURATION.total_seconds()*1000,
                self.slot_time_elapsed)

            time_start = datetime.now()
            self.le2mserv.gestionnaire_graphique.infoserv(
                "Start time: {}".format(time_start.strftime("%H:%M:%S")))
            for g in self.__groups:
                g.timer_update.start()
            yield(self.le2mserv.gestionnaire_experience.run_step(
                trans_DYNCPR("Decision"), self._tous, "display_decision",
                time_start))

        elif pms.DYNAMIC_TYPE == pms.DISCRETE:

            for period in range(1, pms.NOMBRE_PERIODES + 1):

                if self.le2mserv.gestionnaire_experience.stop_repetitions:
                    break

                # init period
                txt = le2mtrans(u"Period") + u" {}".format(period)
                self.le2mserv.gestionnaire_graphique.infoserv(
                    [txt], fg="white", bg="gray")
                self.le2mserv.gestionnaire_graphique.infoclt(
                    [txt], fg="white", bg="gray")
                yield (self.le2mserv.gestionnaire_experience.run_func(
                    self._tous, "newperiod", period))

                # decision
                time_start = datetime.now()
                yield(self.le2mserv.gestionnaire_experience.run_step(
                    "Decision", self._tous, "display_decision", time_start))

                # period payoffs
                self.le2mserv.gestionnaire_experience.compute_periodpayoffs(
                    "dynamicCPR")
        
        # summary
        yield(self.le2mserv.gestionnaire_experience.run_step(
            le2mtrans(u"Summary"), self._tous, "display_summary"))
        
        # ----------------------------------------------------------------------
        # End of part
        # ----------------------------------------------------------------------

        yield (self.le2mserv.gestionnaire_experience.finalize_part("dynamicCPR"))

    @defer.inlineCallbacks
    @pyqtSlot()
    def slot_time_elapsed(self):
        self.le2mserv.gestionnaire_graphique.infoserv("End time: {}".format(
            datetime.now().strftime("%H:%M:%S")))
        for g in self.__groups:
            g.timer_update.stop()
        yield (self.le2mserv.gestionnaire_experience.run_func(
            self._tous, "end_update_data"))

