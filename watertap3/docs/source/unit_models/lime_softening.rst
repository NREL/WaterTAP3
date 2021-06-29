Lime Softening
=====================================

Unit Parameters
--------------------

There is one unit parameter:

*``"lime"`` - lime dose for unit [mg/L]:

    * Required parameter

Capital Costs
---------------

The capital costs are a function of flow [m3/hr] with cost curve parameters from McGivney &
Kawamura (2008):

    .. math::

        C_{lime} = 0.0704 Q_{in} ^ {0.7306}
|
Electricity Intensity
------------------------

Electricity intensity for lime softening is based off the pump used to inject
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

* Solution density [kg/m3] = 1250
* Lift height [ft] = 100
* Pump efficiency = 0.9
* Motor efficiency = 0.9

References
------------

| Minnesota Rural Water Association, Chapter 16 Lime Softening
| https://www.mrwa.com/WaterWorksMnl/Chapter%2016%20Lime%20Softening.pdf

Lime Softening Module
----------------------------------------

.. autoclass:: watertap3.wt_units.lime_softening.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak