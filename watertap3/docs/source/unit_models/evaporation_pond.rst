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

WaterTAP3 uses one of two regressions from each of the two references below to estimate the
evaporation rate of pure water :math:`\big( E_{pure} \big)` under the given meteorological
conditions. In WaterTAP3,evaporation ponds are used as a zero liquid discharge (ZLD) technology to reduce the volume of
brine, so the water is assumed to be saline. The evaporation rate of saline water can be
estimated to be 70% that of pure water. Thus, this calculated evaporation rate is multiplied by 0.7 to arrive at the estimated evaporation rate :math:`\big( E_{saline} = 0.7E_{pure} \big)`.

For mass balance purposes in WaterTAP3, the flow of evaporated water is the considered to be the
flow out of the unit. To accomodate a given water recovery, he area of the pond :math:`\big(A_{pond} \big)`
is calculated as:

    .. math::

           A_{pond} = \frac{Q_{out}}{E_{saline}}



Capital Costs
---------------



Assumptions:
****************



References
*************

EVAPORATION RATE

| Turc, L. (1961)
| "Water requirements assessment of irrigation, potential evapotranspiration:
| Simplified and updated climatic formula."
| Annales Agronomiques, 12, 13-49.

| Jensen, M.E.Haise, H.R. 1963,
| Estimating evapotranspiration from solar radiation.
| Proceedings of the American Society of Civil Engineers
| Journal of the Irrigation and Drainage Division, vol. 89, pp. 15-41.

Electricity Cost
------------------

WaterTAP3 does not include any electricity intensity for evaporation ponds.


Evaporation Pond Module
----------------------------------------

.. autoclass:: watertap3.wt_units.evaporation_pond.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow, evaporation_rate, evaporation_rate_regress
   :undoc-members: build
   :exclude-members: build
