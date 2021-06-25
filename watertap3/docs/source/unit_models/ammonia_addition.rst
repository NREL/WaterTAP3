Ammonia Addition
=====================================

In general, costs for chemical additions in WaterTAP3 are a function of the chemical dose and the
flow in. The chemical solution flow is calculated from these two values and assumed solution
densities to use in a cost curve. All chemical additions assume 2 chemical addition units.

Capital Costs
---------------
The ammonia solution flow :math:`\big( S \big)` is used in a cost curve of the general
form:

:math:`\text{Cost} = S a ^ b`

For a ammonia addition unit, `a` = 6699.1 and `b` = 0.4219. The full cost equation in
WaterTAP3 is:

:math:`\text{Cost } ($MM) = N_{units}\big( 6699.1 S \big) ^{0.4219}\times 10^{-6}`

These parameters were determined by fitting data from FIGURE 5.5.11 - AQUA AMMONIA FEED 29%
SOLUTION in the below reference to the general form.

Assumptions:
****************

* Number of units = 2
* Chemical solution density [kg/m3] = 900
* Ratio in solution = 30%


Electricity Intensity
------------------------

Electricity intensity for chemical additions in WaterTAP3 is based off the pump used to inject
the chemical solution, the chemical solution flow rate, and the influent flow rate. The model
assumes:

* Lift height = 100 ft
* Pump efficiency = 90%
* Motor efficiency = 90%

Reference
------------------------

| Cost Estimating Manual for Water Treatment Facilities (2008)
| William McGivney & Susumu Kawamura
| DOI:10.1002/9780470260036


Sodium Bisulfite Module
----------------------------------------

.. autoclass:: watertap3.wt_units.ammonia_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build
