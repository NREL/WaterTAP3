.. _agglom_stacking_unit:

Agglomeration and Stacking
============================================================

Agglomeration and stacking is the process of stacking metal-bearing ores for irrigation with a
chemical solution.

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
---------------

Capital costs for agglomeration and stacking and other associated mine units (i.e.
:ref:`solution_distribution_and_recovery_plant_unit`, :ref:`heap_leaching_unit`) are derived from
Table 3 in Kappes (2002). The costing components explicitly calculated for these units via
regressed data from this table are (associated WaterTAP3 unit in parentheses):

* Mining equipment (Heap Leaching)
* Mine development (Heap Leaching)
* Crushing plant (Heap Leaching)
* Leaching pads/ponds (Heap Leaching)
* Agglomeration/stacking system (Agglomeration and Stacking)
* Solution distribution and recovery plant (Solution Distribution and Recovery Plant)
|
The costs from this table that are estimated as a fraction of the component costs are:

* Infrastructure (power, water, access roads, site office, service facilities)
* Owner's preproduction cost
* Engineering, procurement, construction management
* Import duties
* Equipment and materials transport
* Initial operating supplies

Note that laboratory costs and working capital costs from this table are accounted for elsewhere
in WaterTAP3 and so are excluded from the unit process calculations.

Capital costs for agglomeration and stacking are a function of the cost of the mining capacity `X` [tonnes/day]. This cost
curve was derived from data for mining capacities of 3,000 tonnes/day and 15,000 tonnes/day from
Table 3 in Kappes (2002):

    .. math::

        C_{stack} = 0.00197 X ^ {0.778}


To account for the other tabulated costing components in Table 3, WaterTAP3 calculates the
fraction `f` that the other costs are of the component costs (i.e. other costs / component
costs). The other costs fraction `f` are determined from a regression of the total cost in Table
3 minus the agglomeration and stacking costs (calculated above) vs. the mining capacities in that
table (3,000 and 15,000 tonnes/day):

    .. math::

        f = 0.3012 X ^ {0.1119}


This fraction is multiplied by the agglomeration and stacking costs and added to those costs to
form the costing basis:

    .. math::

        C_{basis} = (C_{stack}) (1 + f)


To create a cost curve based on unit flow, WaterTAP3 scales the unit flow to 65 m3/hr (derived
from the initial heap leaching case study used to develop WaterTAP3). The final cost curve for
agglomeration and stacking is:

    .. math::

        C_{agglom} = \frac{Q_{in}}{65} C_{basis} ^ {0.778}


Operating Costs
--------------------

The operating costs `P` [$/year] for agglomeration and stacking are derived with cost curves
regressed from data in Table 5 of Kappes (2002). Since this is the only component considered,
this is the total operating cost:

    .. math::

        P_{stack} = 6.28846 X ^ {0.56932} = C_{op}


Electricity Intensity
------------------------

There is no electricity intensity associated with agglomeration and stacking.


References
______________

| Kappes, D.W. "Precious Metal Heap Leach Design and Practice" (2002)
| in: *Mineral processing plant design, practice, and control*
| pg. 1606-1630, ISBN: 0873352238
| http://ore-max.com/pdfs/resources/precious_metal_heap_leach_design_and_practice.pdf


Agglomeration and Stacking Module
----------------------------------------

.. autoclass:: watertap3.wt_units.agglom_stacking.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak