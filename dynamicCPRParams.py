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
IMPULSORY = 2  # future
# used to store the curve (DYNCRP_curve_type)
EXTRACTION = 0
PAYOFF = 1

# ------------------------------------------------------------------------------
# PARAMETERS
# ------------------------------------------------------------------------------

TREATMENT = BASELINE  # for future treatments
TAUX_CONVERSION = 1
NOMBRE_PERIODES = 2  # only for dynamic == discrete
TAILLE_GROUPES = 2  # should not be changed without asking Dimitri
MONNAIE = u"ecu"

# DECISION
DECISION_MIN = 0
DECISION_MAX = 20
DECISION_STEP = 0.01

PARTIE_ESSAI = False

DYNAMIC_TYPE = CONTINUOUS
# continuous game
CONTINUOUS_TIME_DURATION = timedelta(seconds=400)  # can be changed in config screen
# time for the player to take a decision
DISCRETE_DECISION_TIME = timedelta(minutes=1)
# milliseconds
TIMER_UPDATE = timedelta(seconds=1)  # refresh the group data and the graphs

# ------------------------------------------------------------------------------
# RESOURCE
# ------------------------------------------------------------------------------
RESOURCE_INITIAL_STOCK = 500
RESOURCE_GROWTH = 15

# ------------------------------------------------------------------------------
# FONCTION DE GAIN
# ------------------------------------------------------------------------------
param_a = 1.1
param_b = 0.3
param_c0 = 0.5
param_c1 = 0.5



