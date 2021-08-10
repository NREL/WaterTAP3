Heap Leaching
============================================================

Heap leaching is the process of leaching desirable metals off a stack of metal-bearing ores via
irrigation with a chemical solution and then collecting the leached solution for further
extraction of the desirable metals.
|
Unit Parameters
--------------------

There are two parameters:

* ``'mining_capacity'`` - mining capacity for the mine [tonnes/day]

    * Optional parameter
    * Default value is 922 tonnes/day
    * Must be provided with ``'ore_heap_soln'`` or default values for both will be used.

* ``'ore_heap_soln'`` - volume of leach solution needed per mass ore [gal/tonne]

    * Optional parameter
    * Default value is 500 gal/tonne
    * Must be provided with ``'mining_capacity'`` or default values for both will be used.

Capital Costs
---------------

Capital costs for heap leaching are a function of the mining equipment, mine development, the
crushing plant, and the leaching pads/ponds. Each of these are a function of the mining
capacity `X`. Cost curves for these components were derived from data for mining capacities of
3,000 tonnes/day and 15,000 tonnes/day.

    .. math::

        C_{equip} = 0.00124 * X ^ {0.93454}

    .. math::

        C_{devel} = 0.01908 * X ^ {0.43068}

    .. math::

        C_{crush} = 0.0058 * X ^ {0.6651}

    .. math::

        C_{leach} = 0.0005 * X ^ {0.94819}





Electricity Intensity
------------------------


Assumptions
_____________


References
______________



Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.unit_template.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak