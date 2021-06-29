Ozone + AOP
============================================================

The Ozone unit in WaterTAP3 is used to calculate costs for both Ozone and Ozone+AOP systems.

Unit Parameters
------------------

Unit parameters are read in from the ``unit_params`` dictionary given in the input sheet.

* ``"aop"`` - boolean to indicate if the unit includes AOP costs:

    * Required parameter
    * If ``True``, oxidant costs are included
    * If ``False``, oxidant costs are excluded
|
* ``"contact_time"`` - contact time with ozone [min]

    * Required parameter
|
* ``"ct"`` - Concentration * time (Ct) target [mg/(L*min)]

    * Required parameter
|
* ``"mass_transfer"`` - mass transfer coefficient for ozone contactor

    * Required parameter
|
* ``"chemical_name"`` - oxidant chemical name

    * Required parameter if ``aop = True``
    * Must match exactly the chemical name in ``chemical_name.csv``
|
Capital Costs
---------------

The Ozone/AOP unit in WaterTAP3 is used for both Ozone only units and Ozone+AOP units. For this
reason costs are broken up between the ozone system and the oxidant injection system.

Ozone Capital Costs
*********************

Ozone capital costs in WaterTAP3 are a function of the ozone contact time,
Ct, ozone mass transfer, ozone dose, TOC concentration, flow in, and the ozone/TOC ratio.

TOC concentration and flow in are taken from the model. Contact time, mass transfer, and Ct are
taken from user input. Ozone demand is calculated from Texas Water Development Board (2016):

    .. math::

         D_{O3} = \frac{ t_{O3} c_{toc} Ct}{\eta_{O3}}
|
Ozone dose is then used in a regression dervied from data found in Table 3.24 from Texas
Water Development Board (2016).

Oxidant Capital Costs
************************

The unit can accept any chemical name and dose, but the cost curve used was developed
specifically for Hydrogen Peroxide in Texas Water Development Board (2016):

    .. math::

        C_{ox} = 1228 S_{ox} ^ {0.2277}
|
Oxidant costs are calculated are based off the oxidant solution flow [lb/day]:

    .. math::

        S_{ox} = Q_{in} D_{ox}
|
Where the oxidant dose is calculated with [kg/m3]:

    .. math::

        D_{ox} = 0.5 X c_{toc}
|
And the ozone/TOC ratio `X` is calculated with:

    .. math::

        X = 1 + \frac{t_{O3} Ct}{c_{toc}}

|
Electricity Intensity
------------------------

Electricity intensity is a function of the ozone flow [lb/day] and water flow into unit [m3/hr]
from Mundy et al. (2018):

    .. math::

        E_{O3} = 5 \frac{Q_{O3}}{Q_{in}}
|
References
-------------------

COSTING
*********

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

ELECTRICITY
****************

| Mundy, B., et al. (2018).
| "A Review of Ozone Systems Costs for Municipal Applications. Report by the Municipal Committee –
|   IOA Pan American Group."
| *Ozone: Science & Engineering* 40(4): 266-274.

Ozone + AOP Module
----------------------------------------

.. autoclass:: watertap3.wt_units.ozone_aop.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak