# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
from twisted.internet import defer, reactor
from blinker import signal

from util import utiltools
from util.utili18n import le2mtrans
from util.utiltools import get_module_attributes

import dynamicCPRParams as pms
from dynamicCPRGui import DConfigure
from dynamicCPRTexts import trans_DYNCPR
from dynamicCPRGroup import GroupDYNCPR
from dynamicCPRUtil import ThreadForRepeatedAction


logger = logging.getLogger("le2m.{}".format(__name__))


class Serveur():
    def __init__(self, le2mserv):
        self._le2mserv = le2mserv
        self._current_sequence = 0
        self._time_elapsed = signal("time_elapsed")
        self._time_elapsed.connect(lambda _: self._stop_the_groups_thread)

        # creation of the menu (will be placed in the "part" menu on the
        # server screen)
        actions = OrderedDict()
        actions[le2mtrans(u"Configure")] = self._configure
        actions[le2mtrans(u"Display parameters")] = \
            lambda _: self._le2mserv.gestionnaire_graphique. \
            display_information2(
                utiltools.get_module_info(pms), le2mtrans(u"Parameters"))
        actions[le2mtrans(u"Start")] = lambda _: self._demarrer()
        actions[le2mtrans(u"Display payoffs")] = \
            lambda _: self._le2mserv.gestionnaire_experience.\
            display_payoffs_onserver("dynamicCPR")
        self._le2mserv.gestionnaire_graphique.add_topartmenu(
            u"Dynamic CPR", actions)

    def _configure(self):
        screen_conf = DConfigure(self._le2mserv.gestionnaire_graphique.screen)
        if screen_conf.exec_():
            pms_list = []
            for k, v in get_module_attributes(pms).items():
                if k in ["TREATMENT", "DYNAMIC_TYPE", "NOMBRE_PERIODES",
                         "PARTIE_ESSAI"]:
                    pms_list.append("{}: {}".format(k, v))
            self._le2mserv.gestionnaire_graphique.infoserv(pms_list)

    @defer.inlineCallbacks
    def _demarrer(self):

        # ----------------------------------------------------------------------
        # check conditions
        # ----------------------------------------------------------------------

        if not self._le2mserv.gestionnaire_graphique.question(
                        le2mtrans("Start") + " dynamicCPR?"):
            return

        # ----------------------------------------------------------------------
        # init part
        # ----------------------------------------------------------------------

        self._current_sequence += 1
        self._groups = []

        # form groups
        if pms.TAILLE_GROUPES > 0:
            try:
                self._le2mserv.gestionnaire_groupes.former_groupes(
                    self._le2mserv.gestionnaire_joueurs.get_players(),
                    pms.TAILLE_GROUPES, forcer_nouveaux=True)
            except ValueError as e:
                self._le2mserv.gestionnaire_graphique.display_error(
                    e.message)
                self._current_sequence -= 1
                return
            else:
                for g, m in self._le2mserv.gestionnaire_groupes.get_groupes().items():
                    group = GroupDYNCPR(self._le2mserv, g, m, self._current_sequence)
                    self._le2mserv.gestionnaire_base.ajouter(group)
                    self._groups.append(group)
                    for j in m:
                        j.group = group

        # creates parts
        yield (self._le2mserv.gestionnaire_experience.init_part(
            "dynamicCPR", "PartieDYNCPR", "RemoteDYNCPR", pms,
            current_sequence=self._current_sequence))
        self._tous = self._le2mserv.gestionnaire_joueurs.get_players(
            'dynamicCPR')

        # set parameters on remotes (has to be after group formation)
        yield (self._le2mserv.gestionnaire_experience.run_step(
            le2mtrans(u"Configure"), self._tous, "configure"))

        # ----------------------------------------------------------------------
        # SELECT THE INITIAL EXTRACTION
        # ----------------------------------------------------------------------

        self._le2mserv.gestionnaire_graphique.infoclt(trans_DYNCPR(
            u"Initial extraction"))
        yield (self._le2mserv.gestionnaire_experience.run_func(
            self._tous, "newperiod", 0))
        yield (self._le2mserv.gestionnaire_experience.run_step(
            trans_DYNCPR(u"Initial extraction"), self._tous,
            "set_initial_extraction"))
        for g in self._groups:
            self._le2mserv.gestionnaire_graphique.infoserv("G{}: {}".format(
                g.uid_short, g.current_extraction["extraction"]))

        # ----------------------------------------------------------------------
        # DEPENDS ON TREATMENT
        # ----------------------------------------------------------------------

        if pms.DYNAMIC_TYPE == pms.CONTINUOUS:

            txt = le2mtrans(u"Period") + u" 1"
            self._le2mserv.gestionnaire_graphique.infoserv(
                txt, fg="white", bg="gray")
            self._le2mserv.gestionnaire_graphique.infoclt(
                txt, fg="white", bg="gray")
            yield (self._le2mserv.gestionnaire_experience.run_func(
                self._tous, "newperiod", 1))

            # we collect the threads that handle the update of data
            self._the_groups_thread = [g.thread_update for g in self._groups]
            # we create a thread thant handles the time
            self._thread_time = ThreadForRepeatedAction(
                pms.CONTINUOUS_TIME_DURATION.total_seconds(),
                self._time_elapsed.send)

            # start the threads
            for t in self._the_groups_thread:
                t.start()
            self._thread_time.start()
            self._thread_time.again = False

            # start the decision step
            yield(self._le2mserv.gestionnaire_experience.run_step(
                trans_DYNCPR("Decision"), self._tous, "display_decision"))

            # wait for the thread
            self._thread_time.join()

        elif pms.DYNAMIC_TYPE == pms.DISCRETE:

            for period in range(1, pms.NOMBRE_PERIODES + 1):

                if self._le2mserv.gestionnaire_experience.stop_repetitions:
                    break

                # init period
                txt = le2mtrans(u"Period") + u" {}".format(period)
                self._le2mserv.gestionnaire_graphique.infoserv(
                    [txt], fg="white", bg="gray")
                self._le2mserv.gestionnaire_graphique.infoclt(
                    [txt], fg="white", bg="gray")
                yield (self._le2mserv.gestionnaire_experience.run_func(
                    self._tous, "newperiod", period))

                # decision
                yield(self._le2mserv.gestionnaire_experience.run_step(
                    le2mtrans(u"Decision"), self._tous, "display_decision"))
                for g in self._groups:
                    self._le2mserv.gestionnaire_graphique.infoserv(
                        "G{}: {}".format(
                            g.uid_short, g.current_extraction["extraction"]))

                # period payoffs
                self._le2mserv.gestionnaire_experience.compute_periodpayoffs(
                    "dynamicCPR")
        
        # summary
        yield(self._le2mserv.gestionnaire_experience.run_step(
            le2mtrans(u"Summary"), self._tous, "display_summary"))
        
        # ----------------------------------------------------------------------
        # End of part
        # ----------------------------------------------------------------------

        yield (self._le2mserv.gestionnaire_experience.finalize_part("dynamicCPR"))

    @defer.inlineCallbacks
    def _stop_the_groups_thread(self):
        for t in self._the_groups_thread:
            t.stop()
        yield (self._le2mserv.gestionnaire_experience.run_func(
            self._groups, "end_update_data"))

