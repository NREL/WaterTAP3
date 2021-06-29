Seawater Intake
============================================================

Unit Basics
--------------

This is the intake unit process for seawater cases.

Unit Parameters
--------------------

None.

Capital Costs
---------------

The capital costs are a function of flow [MGD]:

    .. math::

        C_{sw} = 0.000215 Q_{in} ^ {0.888803}


Assumptions
--------------

Several aspects of the unit are assumed:

The lift height is 100 ft:

    .. math::

        h = 100

The pump and motor efficiency are 90%:

    .. math::

        \eta_{pump} = \eta_{motor} = 0.9

Electricity Intensity
------------------------

Electricity intensity for onshore intake in WaterTAP3 is based off the pump used,
the pump/motor efficiencies, lift height, and the influent flow rate.

References
______________

CAPITAL
*********

| Voutchkov, N. (2018).
| Desalination Project Cost Estimating and Management.
| https://doi.org/10.1201/9781351242738

ELECTRICITY
***************

| Bukhary, S., et al. (2019).
| "An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water Treatment Plant."
| *Water* 12(1).


Seawater Intake Module
----------------------------------------

.. autoclass:: watertap3.wt_units.sw_onshore_intake.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build
