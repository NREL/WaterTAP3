Municipal Drinking (Distribution)
============================================================

Unit Basics
--------------

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

Assumptions
--------------

Several aspects of the unit are assumed:

The lift height is 300 ft:

    .. math::

        h = 300

The pump and motor efficiency are 90%:

    .. math::

        \eta_{pump} = \eta_{motor} = 0.9

Electricity Intensity
------------------------

Electricity intensity for municipal drinking in WaterTAP3 is based off the pump used to inject
the pump/motor efficiencies, lift height, and the influent flow rate.

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
