.. _surface_discharge_unit:

Surface Discharge
============================================================

Unit Basics
--------------

This unit is a terminal unit in WaterTAP3 and represents the cost of discharging waste streams to
surface water. This is also the assumed destination for the waste from any unit process if no
waste steram is specified in the input sheet.

Unit Parameters
--------------------

There are two parameters:

* ``"pipe_distance"`` - distance for piping to discharge to surface water body [mi]:

    * Optional parameter
    * If included in parameters, adds pipe construction cost to capital cost.
|
* ``"pump"`` - whether or not to include pumping electricity costs:

    * Optional parameter
    * Options are "yes" and "no"
    * If "yes", includes electricity calculation.
|
Capital Costs
---------------

The capital costs are a function of flow [m3/hr] and can include piping costs:

    .. math::

        C_{surf} = 35 \frac{Q_{in}}{10417} ^ {0.873} + C_{pipe}
|
Piping cost assumes an 8 in diameter pipe, and is calculated as:

    .. math::

        C_{pipe} = 0.28 x_{pipe}
|
If the ``"pipe_distance"`` unit parameter is not included:

    .. math::

        C_{pipe} = 0
|
Electricity Intensity
------------------------

Electricity intensity for surface discharge (if included) is based off the pump used. The
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

        E_{surf} = \frac{0.746 Q_{gpm} h}{3960 \eta_{pump} \eta_{motor} Q_{m3hr}}
|

Assumptions
------------------------

* Lift height [ft] = 100
* Pump efficiency = 0.9
* Motor efficiency = 0.9

References
______________

?????

Surface Discharge Module
----------------------------------------

.. autoclass:: watertap3.wt_units.surface_discharge.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak