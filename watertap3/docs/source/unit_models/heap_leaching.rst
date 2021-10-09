.. _heap_leaching_unit:

Heap Leaching
============================================================

Heap leaching is the process of collecting the leached solution irrigated over a stack of
metal-bearing ores.
|

Unit Parameters
--------------------

There are two parameters:

* ``"mining_capacity"`` - mining capacity for the mine [tonnes/day]

    * Optional parameter
    * Default value is 922 tonnes/day
    * Must be provided with ``"ore_heap_soln"`` or default values for both will be used.
|
* ``"ore_heap_soln"`` - volume of leach solution needed per mass ore [gal/tonne]

    * Optional parameter
    * Default value is 500 gal/tonne
    * Must be provided with ``"mining_capacity"`` or default values for both will be used.
|
Capital Costs
-------------------------

Capital costs for heap leaching and other associated mine units (i.e.
:ref:`solution_distribution_and_recovery_plant_unit`,
:ref:`agglom_stacking_unit`) are derived from Table 3 in Kappes (2002). The costing
components explicitly calculated for these units via regressed data from this table are
(associated WaterTAP3 unit in parentheses):

* Mining equipment (Heap Leaching)
* Mine development (Heap Leaching)
* Crushing plant (Heap Leaching)
* Leaching pads/ponds (Heap Leaching)
* Agglomeration/stacking system (Agglomeration and Stacking)
* Solution distribution and recovery plant (Solution Distribution and Recovery Plant)

The costs from this table that are estimated via different method below are:

* Infrastructure (power, water, access roads, site office, service facilities)
* Owner's preproduction cost
* Engineering, procurement, construction management
* Import duties
* Equipment and materials transport
* Initial operating supplies

Note that laboratory costs and working capital costs from this table are accounted for elsewhere
in WaterTAP3 and so are excluded from the unit process calculations.

Capital costs for heap leaching are a function of the mining equipment, mine development, the
crushing plant, and the leaching pads/ponds. Each of these are a function of the mining
capacity `X` [tonnes/day]. Cost curves for these components were derived from data for mining
capacities of 3,000 tonnes/day and 15,000 tonnes/day from Table 3 in Kappes (2002):

    .. math::

        C_{equip} = 0.00124 X ^ {0.93454}
|
    .. math::

        C_{devel} = 0.01908 X ^ {0.43068}
|
    .. math::

        C_{crush} = 0.0058 X ^ {0.6651}
|
    .. math::

        C_{leach} = 0.0005 X ^ {0.94819}
|
To account for the other tabulated costing components in Table 3, WaterTAP3 calculates the
fraction `f` that the other costs are of the component costs (i.e. other costs / component
costs). The other costs fraction `f` are determined from a regression of the total cost in Table
3 minus the sum of the heap leaching costs (calculated above) vs. the mining capacities in that
table (3,000 and 15,000 tonnes/day):

    .. math::

        f = 0.3012 X ^ {0.1119}

This fraction is multiplied by the sum of the component costs (calculated above) and added to
that sum. This is the costing basis for Heap Leaching:

    .. math::

        C_{basis} = (C_{equip} + C_{devel} + C_{crush} + C_{leach}) (1 + f)


To create a cost curve based on unit flow, WaterTAP3 scales the unit flow to 73 m3/hr (derived
from the initial heap leaching case study used to develop WaterTAP3) and creates an exponent
`b` from:

    .. math::

        b = \frac{0.935 C_{equip} + 0.431 C_{devel} + 0.665 C_{crush} + 0.948 C_{leach}}{C_{equip} + C_{devel} + C_{crush} + C_{leach}}

Note that the coefficients in the numerator of the above equation are the exponents for the cost
curves for each costing component.

And then the final capital costing curve for heap leaching unit is:

    .. math::

        C_{heap} = \frac{Q_{in}}{73} C_{basis} ^ b

|

Operating Costs
--------------------

The operating costs `P` [$/year] for heap leaching are derived with cost curves regressed from
data in Table 5 of Kappes (2002). Included for heap leaching in WaterTAP3 are operational costs
relating to:

* Mining equipment
* Crushing plant
* Leaching pads/ponds

These cost curves are:

    .. math::

        P_{mining} = 22.54816 X ^ {0.74807}

    .. math::

        P_{crush} = 4.466 X ^ {0.8794}

    .. math::

        P_{leach} = 6.34727 X ^ {0.68261}

The total operating cost is the sum of these components:

    .. math::

        C_{op} = P_{mining} + P_{crush} + P_{leach}




Electricity Intensity
------------------------

There is no electricity intensity associated with heap leaching.


References
______________

| Kappes, D.W. "Precious Metal Heap Leach Design and Practice" (2002)
| in: *Mineral processing plant design, practice, and control*
| pg. 1606-1630, ISBN: 0873352238
| http://ore-max.com/pdfs/resources/precious_metal_heap_leach_design_and_practice.pdf

Heap Leaching Module
----------------------------------------

.. autoclass:: watertap3.wt_units.heap_leaching.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak