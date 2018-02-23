# -*- coding: utf-8 -*-
"""
This module contains the texts of the part (server and remote)
"""

from util.utiltools import get_pluriel
import dynamicCPRParams as pms
from util.utili18n import le2mtrans
import os
import configuration.configparam as params
import gettext
import logging

logger = logging.getLogger("le2m")
try:
    localedir = os.path.join(params.getp("PARTSDIR"), "dynamicCPR",
                             "locale")
    trans_DYNCPR = gettext.translation(
      "dynamicCPR", localedir, languages=[params.getp("LANG")]).ugettext
except (AttributeError, IOError):
    logger.critical(u"Translation file not found")
    trans_DYNCPR = lambda x: x  # if there is an error, no translation


INITIAL_EXTRACTION = trans_DYNCPR(
    u"Please choose an initial extraction value"
)



def get_histo_vars():
    return ["DYNCPR_period", "DYNCPR_decision",
            "DYNCPR_periodpayoff",
            "DYNCPR_cumulativepayoff"]


def get_histo_head():
    return [le2mtrans(u"Period"), le2mtrans(u"Decision"),
             le2mtrans(u"Period\npayoff"), le2mtrans(u"Cumulative\npayoff")]


def get_text_explanation():
    return trans_DYNCPR(u"Explanation text")


def get_text_label_decision():
    return trans_DYNCPR(u"Decision label")


def get_text_summary(period_content):
    txt = trans_DYNCPR(u"Summary text")
    return txt


