# -*- coding: utf-8 -*-
"""=============================================================================
This modules contains the variables and the parameters.
Do not change the variables.
Parameters that can be changed without any risk of damages should be changed
by clicking on the configure sub-menu at the server screen.
If you need to change some parameters below please be sure of what you do,
which means that you should ask to the developer ;-)
============================================================================="""

import datetime

# variables --------------------------------------------------------------------
BASELINE = 0
TREATMENTS_NAMES = {BASELINE: "Baseline"}

# parameters -------------------------------------------------------------------
TREATMENT = BASELINE
TAUX_CONVERSION = 1
NOMBRE_PERIODES = 2
TAILLE_GROUPES = 2
GROUPES_CHAQUE_PERIODE = False
MONNAIE = u"ecu"
PERIODE_ESSAI = False

# DECISION
DECISION_MIN = 0
DECISION_MAX = 100
DECISION_STEP = 1


TIME_DURATION = datetime.timedelta(hours=0, minutes=2, seconds=0)  # hours, minutes, seconds
CONTINUOUS = 0
DISCRETE = 1
IMPULSORY = 2
DYNAMIC_TYPE = CONTINUOUS
CONTIUOUS_REFRESH = 1000  # 1 second
DISCRETE_DECISION_TIME = datetime.time(0, 1, 0)



