.. _evaporation_pond_unit:

Evaporation Ponds
=====================================

Evaporation ponds are commonly used to further concentrate membrane brine to reduce the volume
needed for disposal.

The generalized approach is as follows:

1. Calculate the evaporation rate based on environmental conditions.
2. Determine area required for evaporation ponds using a mass balance approach.
3. Calculate capital costs based off of area and costing approach selected by user.

|
Unit Parameters
--------------------

The evaporation pond model draws from several sources and includes several optional
parameters for user input. Further detail on these parameters is provided below:

* ``"approach"`` - costing approach used for the model (more detail is provided below on each
  approach):

    * Optional parameter
    * Options are ``"wt3"``, ``"zld"``, and ``"lenntech"``
    * Default approach is ``"wt3"`` if no input given
    * Must be enclosed in double ``" "`` or single ``' '`` quotes
|
* ``"evap_method"`` - method used to calculate evaporation rate

    * Optional parameter
    * Two options are ``"turc"`` and ``"jensen"``
    * Defaults to ``"jensen"`` if no input given
    * Must be enclosed in double ``" "`` or single ``' '`` quotes
|
* ``"air_temp"`` - air temperature for evaporation rate calculation [C]

    * Optional parameter
    * Default value is 20 \deg C
    * Note: Must provide both ``"air_temp"`` and ``"solar_rad"`` together or default values for both
      will be used.
|
* ``"solar_rad"`` - incident solar radiation for evaporation rate calculation [mJ/cm2]

    * Optional parameter
    * Default value is 25 mJ/cm2
    * Note: Must provide both ``"air_temp"`` and ``"solar_rad"`` together or default values for both
      will be used.
|
* ``"humidity"`` - humidity for use in calculation of ratio to adjust pure water evaporation rate
  to saline water evaporation rate

    * Optional parameter
    * Default value is 0.5 (i.e. 50% humidity)
    * Note: Must provide both ``"humidity"`` and ``"wind_speed"`` together or default values for
      both will be used.
|
* ``"wind_speed"`` - wind speed for use in calculation of ratio to adjust pure water evaporation
  rate [m/s]

    * Optional parameter
    * Default value is 5 m/s
    * Note: Must provide both ``"humidity"`` and ``"wind_speed"`` together or default values for
      both will be used.
|
* ``"liner_thickness"`` - thickness of liner used for calculation of cost per acre [mil]

    * Optional parameter
    * Default value is 50 mil
    * Note that 1 mil = 1/1000 inches
    * Note: Must provide ``"liner_thickness"``, ``"land_cost"``, ``"land_clearing_cost"``, and
      ``"dike_height"`` together or default values for all will be used.
|
* ``"land_cost"`` - cost to purchase land for evaporation pond [$/acre]

    * Optional parameter
    * Default value is $5,000/acre
    * Note: Must provide ``"liner_thickness"``, ``"land_cost"``, ``"land_clearing_cost"``, and
      ``"dike_height"`` together or default values for all will be used.
|
* ``"land_clearing_cost"`` - cost to clear land for evaporation pond [$/acre]

    * Optional parameter
    * Default value is $1,000/acre
    * Note: Must provide ``"liner_thickness"``, ``"land_cost"``, ``"land_clearing_cost"``, and
      ``"dike_height"`` together or default values for all will be used.
    * Typical costs for different types of land cover (Bureau of Reclamation, 2006):

        * brush = $1,000/acre
        * sparsley wooded = $2,000/acre
        * medium wooded = $4,000/acre
        * heavily wooded = $7,000/acre
|
* ``"dike_height"`` - height of dikes for evaporation pond [ft]

    * Default value is 8 ft
    * Typical dike heights are 4-12 ft (from Bureau of Reclamation reference)
    * Note: Must provide ``"liner_thickness"``, ``"land_cost"``, ``"land_clearing_cost"``, and
      ``"dike_height"`` together or default values for all will be used.
|
Evaporation Rate Calculation
----------------------------------

The evaporation rate is `R` is dependent on site specific meteorological conditions and the
salinity of the water. Salintiy has the effect of lowering the evaporation rate, and because
evaporation ponds are commonlny used to concentrate brine streams, an evaporation rate calculated
for pure water must be adjusted downward.

WaterTAP3 uses one of two regressions from each of the two references below to estimate the
evaporation rate of pure water under the given meteorological conditions. Both are functions of
air temperature `T` and solar irradiance `J`. For Jensen & Haise (1963) [mm/day]:

    .. math::

        R_{pure} = R_{j&h} = 0.41 J (0.025 T + 0.078)

|
And for Turc (1961) [mm\day]:

    .. math::

        R_{pure} = R_{turc} = \frac{ 0.313 T (J + 2.1) }{T + 15}
|

In WaterTAP3, the water in the pond is assumed to be saline. The evaporation rate of
saline water can be estimated to be 70% that of pure water (WateReuse Foundation, 2008). Thus,
this calculated evaporation rate is multiplied by 0.7 to arrive at the estimated evaporation rate
for saline water:

    .. math::

        R_{saline} = 0.7R_{pure}
|
Pond Area Calculation
----------------------------------

For mass balance purposes in WaterTAP3, the flow of evaporated water is the considered to be the
flow out of the unit. To accomodate a given water recovery, the area of the pond
is calculated as:

    .. math::

           A_{pond} = \frac{Q_{out}}{R_{saline}}
|
Capital Costs
---------------

The user can choose one of three costing approaches for evaporation ponds in WaterTAP3 that can
be provided as an option in ``unit_params`` under ``"approach"``:

1. ``"wt3"`` - default approach if the user does not provide one. Incorporates an
   adjusted pond area and more indepth costing function. Based on Bureau of Reclamation reference
   below.
2. ``"zld"`` - only considers area and assumes $0.3M/acre. Based on WateReuse
   reference below.
3. ``"lenntech"`` - capital cost determined purely from flow. Based on Lenntech
   reference below.

WT3 Approach:
*********************

The WT3 approach is the default approach and uses a regression for total pond area from the
Bureau of Reclamation reference below. After calculation of the required pond area based on flow
above, if this approach is used the pond area is adjusted upwards to inorporate the additional
area needed for dikes:

    .. math::

           A_{adj} = 1.2 (A_{pond}) (1 + 0.155 \frac{h_{dike}}{\sqrt{A_{pond}}} )
|
Then, the cost per acre [$/acre] is determined that incorporates
``"liner_thickness"``, ``"land_cost"``, ``"land_clearing_cost"``, and ``"dike_height"``:

    .. math::

           C_{acre} = 5406 + 465 ( z_{liner} ) + 1.07 ( c_{land} )+ 0.931 ( c_{clear} ) + 217.5 ( h_{dike} )
|
Thus, using this approach capital costs for evaporation ponds are calculated as:

    .. math::

           C_{evap} = A_{adj} C_{acre}
|
ZLD Approach:
*********************

The ZLD approach is named from the WateReuse document it was adapted from. Using this approach,
the unadjusted pond area is used. The cost per acre is assumed to be $0.3MM. Thus, the capital
costs are calculated as:

    .. math::

           C_{evap} = A_{pond} \times 0.3
|
Lenntech Approach:
*********************

This approach is based entirely on flow in [m3/d] to the evaporation pond and does not include the
calculation for evaporation pond area. It assumes an evaporation rate of 1 m/yr:

    .. math::

           C_{evap} = 0.031 Q_{in} ^ {0.7613}
|
Note that while the reference mentions salt concentrations, land and earthwork costs, and liner
costs, it is unclear how these are incorporated into the cost curve above.

Electricity Cost
------------------

WaterTAP3 does not include any electricity intensity for evaporation ponds.

References
------------------

EVAPORATION RATE
*******************************

| Turc, L. (1961)
| "Water requirements assessment of irrigation, potential evapotranspiration:
| Simplified and updated climatic formula."
| *Annales Agronomiques*, 12, 13-49.

| Jensen, M.E., Haise, H.R. (1963)
| "Estimating evapotranspiration from solar radiation."
| Proceedings of the American Society of Civil Engineers
| *Journal of the Irrigation and Drainage Division*, vol. 89, pp. 15-41.

COSTING
*******************************

| U.S. Bureau of Reclamation (2006)
| Mickley, Michael C.
| "Membrane Concentrate Disposal: Practices and Regulation"
| Chapter 10: Evaporation Pond Disposal

| WateReuse Foundation (2008)
| Mickley, Michael C.
| "Survey of High-Recovery and Zero Liquid Discharge Technologies for Water Utilities"
| ISBN: 978-1-934183-08-3

| Lenntech.com
| https://www.lenntech.com/Data-sheets/Brine-Evaporation-Ponds.pdf

Evaporation Pond Module
----------------------------------------

.. autoclass:: watertap3.wt_units.evaporation_pond.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow, evaporation_rate, evaporation_rate_regress
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak