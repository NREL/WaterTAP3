Lime Addition
=====================================

Costs for chemical additions are based on the chemical dose required to treat the water and the inlet flow to the unit.

Unit Parameters
--------------------

* ``"lime"`` - dose of lime [mg/L]

    * Required parameter
|
Capital Costs
---------------

The lime solution mass flow `M` [lb/day] is used in a cost curve of the general
form:

    .. math::

        C = a M ^ b
|
For a single lime addition unit, `a` = 16972 and `b` = 0.5435. The full cost equation in
WaterTAP3 is:

    .. math::

        C_{lime} = 16972 S ^ {0.5435}
|
This cost is then multiplied by the number of units and the TPEC factor for the final FCI for the
chemical addition. These parameters were determined by fitting data from FIGURE 5.5.9 - LIME FEED
in McGivney & Kawamura (2008).

Electricity Intensity
------------------------

Electricity intensity for chemical additions is based off the pump used to inject
the chemical solution, the chemical solution flow rate, and the influent flow rate. The
calculation includes:

* Lift height [ft]:

    .. math::

        h
|
* The mass flow rate [kg/hr] of the solution necessary to achieve the desired dose:

    .. math::

        M_{lime} = Q_{in} D_{lime}
|
* The volumetric flow `S` [m3/hr] of the chemical solution, which incorporates the solution
  density [kg/m3]:

    .. math::

        S = \frac{M_{lime}}{\rho_{lime}}
|
* The pump and motor efficiencies:

    .. math::

        \eta_{pump}, \eta_{motor}
|
Then the electricity intensity is calculated as [kWh/m3]:

    .. math::

        E_{lime} = \frac{0.746 S h}{3960 \eta_{pump} \eta_{motor} Q_{in}}
|

Assumptions
------------------------

* Number of units = 2
* Solution density [kg/m3] = 1250
* Lift height [ft] = 100
* Pump efficiency = 0.9
* Motor efficiency = 0.9

Reference
------------------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Lime Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.lime_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak