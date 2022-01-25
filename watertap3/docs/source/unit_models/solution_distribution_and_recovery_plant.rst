.. _solution_distribution_and_recovery_plant_unit:

Solution Distribution and Recovery Plant
============================================================

The solution distribution and recovery plant distributes the irrigated solution to the stacked
heap of metal-bearing ores and the recovers that solution for further extraction.


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

Capital costs for the solution distribution and recovery plant and other associated mine units (i.e.
:ref:`agglom_stacking_unit`, :ref:`heap_leaching_unit`) are derived from Table 3 in Kappes (2002).
The costing components explicitly calculated for these units via regressed data from this table
are (associated WaterTAP3 unit in parentheses):

* Mining equipment (Heap Leaching)
* Mine development (Heap Leaching)
* Crushing plant (Heap Leaching)
* Leaching pads/ponds (Heap Leaching)
* Agglomeration/stacking system (Agglomeration and Stacking)
* Solution distribution and recovery plant (Solution Distribution and Recovery Plant)
|
The costs from this table that are estimated as a fraction of the component costs are:

* Infrastructure (power, water, access roads, site office, service facilities)
* Owner"s preproduction cost
* Engineering, procurement, construction management
* Import duties
* Equipment and materials transport
* Initial operating supplies
|
Note that laboratory costs and working capital costs from this table are accounted for elsewhere
in WaterTAP3 and so are excluded from the unit process calculations.

Capital costs for the solution distribution and recovery plant are a function of the process
pumps, plant, and solution distribution piping. These are lumped together in one costing
equation that is a function of the mining capacity `X` [tonnes/day]. This equation is below and
is derived from Table 3 in Kappes (2002):

    .. math::

        C_{s&d} = 0.00347 X ^ {0.71917}

To account for the other tabulated costing components in Table 3, WaterTAP3 calculates the
fraction `f` that the other costs are of the component costs (i.e. other costs / component
costs). The other costs fraction `f` are determined from a regression of the total cost in Table
3 minus the solution and distribution costs (calculated above) vs. the mining capacities in that
table (3,000 and 15,000 tonnes/day):

    .. math::

        f = 0.3012 X ^ {0.1119}


This fraction is multiplied by the cost of the process pumps, plant, and solution distribution
piping (calculated above). This is the costing basis for the solution distribution and recovery
plant:

    .. math::

        C_{basis} = C_{s&d} (1 + f)


To create a cost curve based on unit flow, WaterTAP3 scales the unit flow to the recycle water flow
for the solution distribution and recovery plant. The recycle water flow is the difference
between the heap flow and the make up flow:

    .. math::

        Q_{recycle} = Q_{heap} - Q_{make up}


The make up flow and heap flow are derived from the user input for ``"ore_heap_soln"`` `q`
(default is 500 gal/tonne if no user input provided) and ``"mining_capacity"`` `X` (default is
922 tonnes/day if no user input provided). So making the proper unit conversions, make up flow is
[m3/hr]:

    .. math::

        Q_{make up} = 0.17 q X


    .. math::

        Q_{heap} = q X

And then the final capital costing curve for the solution distribution and recovery plant is:

    .. math::

        C_{soln&dist} = \frac{Q_{in}}{Q_{recycle}} C_{basis} ^ {0.71917}


Operating Costs
--------------------

The operating costs [$/year] for the solution distribution and recovery plant are derived with
cost curves regressed from data in Table 5 of Kappes (2002). Included for the system
distribution and recovery plant in WaterTAP3 are operational costs relating to:

* Recovery plant operations
* Site maintenance
* Cement for agglomeration
* Cyanide, lime, and other reagents
* Environmental reclamation and closure

The cost curve for all these operational costs is:

    .. math::

        C_{s&d} = 7.71759 X ^ {0.91475} = C_{op}


Electricity Intensity
------------------------

Electricity intensity is a function of the mining capacity `M` and the recycle flow and is taken
from Kappes (2002) and is calculated with [kWh/m3]:

    .. math::

        E = \frac{1.8 M}{Q_{recycle}}


References
______________

| Kappes, D.W. "Precious Metal Heap Leach Design and Practice" (2002)
| in: *Mineral processing plant design, practice, and control*
| pg. 1606-1630, ISBN: 0873352238
| http://ore-max.com/pdfs/resources/precious_metal_heap_leach_design_and_practice.pdf


Solution Distribution and Recovery Plant Module
-----------------------------------------------------------------

.. autoclass:: watertap3.wt_units.solution_distribution_and_recovery_plant.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak