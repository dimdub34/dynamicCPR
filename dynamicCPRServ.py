# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict
from twisted.internet import defer
from util import utiltools
from util.utili18n import le2mtrans
import dynamicCPRParams as pms
from dynamicCPRGui import DConfigure
from dynamicCPRTexts import trans_DYNCPR
from dynamicCPRGroup import DYNCPRGroup


logger = logging.getLogger("le2m.{}".format(__name__))


class Serveur(object):
    def __init__(self, le2mserv):
        self._le2mserv = le2mserv
        self._current_sequence = 0

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
            self._le2mserv.gestionnaire_graphique.infoserv(
                u"Traitement: {}".format(pms.TREATMENTS_NAMES.get(pms.TREATMENT)))
            self._le2mserv.gestionnaire_graphique.infoserv(
                u"Période d'essai: {}".format("oui" if pms.PERIODE_ESSAI else "non"))

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

        # form groups
        if pms.TAILLE_GROUPES > 0:
            try:
                self._le2mserv.gestionnaire_groupes.former_groupes(
                    self._le2mserv.gestionnaire_joueurs.get_players(),
                    pms.TAILLE_GROUPES, forcer_nouveaux=True)
            except ValueError as e:
                self._le2mserv.gestionnaire_graphique.display_error(
                    e.message)
                return
            else:
                for g, m in self._le2mserv.gestionnaire_groupes.get_groupes().items():
                    group = DYNCPRGroup(self, g, m, self._current_sequence)
                    for j in m:
                        j.group = group

        self._current_sequence += 1

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

        yield (self._le2mserv.gestionnaire_experience.run_func(
            self._tous, "newperiod", 0))

        # ----------------------------------------------------------------------
        # DEPENDS ON TREATMENT
        # ----------------------------------------------------------------------

        if pms.TREATMENT == pms.CONTINUOUS:
            yield (self._le2mserv.gestionnaire_experience.run_func(
                self._tous, "newperiod", 1))
            yield(self._le2mserv.gestionnaire_experience.run_step(
                trans_DYNCPR("Decision"), self._tous, "display_decision"))

        elif pms.TREATMENT == pms.DISCRETE:
            period_start = 0 if pms.NOMBRE_PERIODES == 0 or pms.PERIODE_ESSAI else 1
            for period in range(period_start, pms.NOMBRE_PERIODES + 1):

                if self._le2mserv.gestionnaire_experience.stop_repetitions:
                    break

                # init period
                self._le2mserv.gestionnaire_graphique.infoserv(
                    [None, le2mtrans(u"Period") + u" {}".format(period)])
                self._le2mserv.gestionnaire_graphique.infoclt(
                    [None, le2mtrans(u"Period") + u" {}".format(period)],
                    fg="white", bg="gray")
                yield (self._le2mserv.gestionnaire_experience.run_func(
                    self._tous, "newperiod", period))

                # decision
                yield(self._le2mserv.gestionnaire_experience.run_step(
                    le2mtrans(u"Decision"), self._tous, "display_decision"))

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
