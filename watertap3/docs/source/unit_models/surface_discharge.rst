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

* ``"pump"`` - whether or not to include pumping electricity costs:

    * Optional parameter

    * Options are "yes" and "no"

    * If "yes", includes electricity calculation.

Capital Costs
---------------

The capital costs are a function of flow [m3/hr] and can include piping costs:

    .. math::

        C_{surf} = 35 \frac{Q_{in}}{10417} ^ {0.873} + C_{pipe}

Piping cost assumes an 8 in diameter pipe, and is calculated as:

    .. math::

        C_{pipe} = 0.28 x_{pipe}

If the ``"pipe_distance"`` unit parameter is not included:

        C_{pipe} = 0


Assumptions
--------------

Several aspects of the unit are assumed:

The lift height is 300 ft:

    .. math::

        h = 100

The pump and motor efficiency are 90%:

    .. math::

        \eta_{pump} = \eta_{motor} = 0.9

Electricity Intensity
------------------------

Electricity intensity (if included) for surface discharge in WaterTAP3 is based off the pump used,
the pump/motor efficiencies, lift height, and the influent flow rate.

References
______________



Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.unit_template.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak