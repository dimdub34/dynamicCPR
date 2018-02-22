# -*- coding: utf-8 -*-
"""=============================================================================
This modules contains the variables and the parameters.
Do not change the variables.
Parameters that can be changed without any risk of damages should be changed
by clicking on the configure sub-menu at the server screen.
If you need to change some parameters below please be sure of what you do,
which means that you should ask to the developer ;-)
============================================================================="""

from datetime import timedelta

# ------------------------------------------------------------------------------
# VARIABLES - do not change any value below
# ------------------------------------------------------------------------------

BASELINE = 0
TREATMENTS_NAMES = {BASELINE: "Baseline"}
CONTINUOUS = 0
DISCRETE = 1
IMPULSORY = 2

# ------------------------------------------------------------------------------
# PARAMETERS
# ------------------------------------------------------------------------------

TREATMENT = BASELINE
TAUX_CONVERSION = 1
NOMBRE_PERIODES = 2
TAILLE_GROUPES = 2
MONNAIE = u"ecu"

# DECISION
DECISION_MIN = 0
DECISION_MAX = 20
DECISION_STEP = 0.01

PARTIE_ESSAI = False

DYNAMIC_TYPE = CONTINUOUS
# continuous game
CONTINUOUS_TIME_DURATION = timedelta(seconds=30)
# refresh of the extractions and resource stock variations
CONTINUOUS_REFRESH = timedelta(seconds=5)
# time for the player to take a decision
DISCRETE_DECISION_TIME = timedelta(minutes=1)

# ------------------------------------------------------------------------------
# RESOURCE
# ------------------------------------------------------------------------------
RESOURCE_INITIAL_STOCK = 100
RESOURCE_GROWTH_RATE = 0.2



