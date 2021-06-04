Evaporation Ponds
=====================================

.. important:: The WaterTAP3 evaporation pond module is under active development. Aspects of the
               module are likely to change in future releases.

Evaporation ponds are commonly used to further concentrate membrane brine to reduce the volume
needed for disposal.

The evaporation pond model in WaterTAP3 draws from several sources and includes several optional
parameters for user input.

The generalized approach is as follows:

1. Calculate the evaporation rate based on environmental conditions.
2. Determine area required for evaporation ponds using a mass balance approach.
3. Calculate capital costs based off of area and costing approach selected by user.




Evaporation Rate Calculation
----------------------------------

The evaporation rate is dependent on site specific meteorological conditions and the salinity of
the water. Salintiy has the effect of lowering the evaporation rate, and because evaporation ponds
are commonlny used to concentrate brine streams, an evaporation rate calculated for pure water
must be adjusted downward.





Capital Costs
---------------



Assumptions:
****************



Reference:
*************


Electricity Cost
------------------




Evaporation Pond Module
----------------------------------------

.. autoclass:: watertap3.wt_units.evaporation_pond.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build
