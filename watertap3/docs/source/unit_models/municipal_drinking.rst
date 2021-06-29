Municipal Drinking (Distribution)
============================================================

This unit is a terminal unit in WaterTAP3 and represents the initial cost to get product water to
the distribution system.

Unit Parameters
--------------------

None

Capital Costs
---------------

The capital costs are a function of flow [MGD]:

    .. math::

        C_{md} = 0.0403 Q_{in} ^ {0.8657}
|
Electricity Intensity
------------------------

Electricity intensity for municipal drinking is based off the pump used. The
calculation includes:

* Lift height [ft]:

    .. math::

        h
|
* The pump and motor efficiencies:

    .. math::

        \eta_{pump}, \eta_{motor}
|
* And the influent flow in [gal/min] and [m3/hr]:

    .. math::

        Q_{gpm}, Q_{m3hr}
|
Then the electricity intensity is calculated as:

    .. math::

        E_{bw} = \frac{0.746 Q_{gpm} h}{3960 \eta_{pump} \eta_{motor} Q_{m3hr}}
|

Assumptions
------------------------

* Lift height [ft] = 300
* Pump efficiency = 0.9
* Motor efficiency = 0.9

References
______________

| Voutchkov, N. (2018).
| Desalination Project Cost Estimating and Management.
| https://doi.org/10.1201/9781351242738


Municipal Drinking (Distribution) Module
--------------------------------------------

.. autoclass:: watertap3.wt_units.municipal_drinking.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak