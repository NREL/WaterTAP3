UV + AOP
============================================================

The UV+AOP module is used to determine costs for both UV disinfection and UV +
AOP units.

Capital costs for UV systems in WaterTAP3 are significantly influenced by UV Dose, UVT, and flow.
For most accurate capital cost, include facility data with input parameters.

Unit Parameters
-----------------

This module has one required parameter and three optional parameters for the input sheet:

* ``"aop"`` - boolean indicating if unit includes AOP or not:

    * Required parameter
    * If ``True``, include chemical costs
|
* ``"uvt_in"`` - assumed ultraviolet transmittance (UVT) into unit:

    * Optional parameter
    * Default value is 0.9
    * Must be between 0.5 and 0.99 in increments of 0.01
|
* ``"uv_dose"`` - Reduction Equivalent Dose (RED) for unit:

    * Optional parameter
    * Default value is 100 mJ/cm2
    * Must be <1200 in increments of 10
|
* ``"chemical_name"`` - name of chemical used for oxidant

    * Optional parameter
    * No default value
    * Can be any chemical but must match *exactly* chemical entry in ``catalysts_chemicals.csv``,
      e.g. ``"Hydrogen_Peroxide"``
|
Capital Costs
---------------

Capital costs for UV + AOP includes cost for the UV system and for the oxidant injection system:

    .. math::

        C_{UV+AOP} = C_{UV} + C_{ox}
|

UV Capital Costs
********************

Capital costs are a function of flow, UV dose, and UV Transmission (UVT). The WaterTAP3 model
uses data Table 3.22 in Texas Water Development Board (2016) to interpolate cost values for:

* UVT between 0.5 and 0.99 in increments of 0.01.
* UV Dose between 10 and 1,200 mJ/cm2 in increments of 10.
|
For the given UVT and UV Dose, WaterTAP3 retrieves cost data for flows between 1 and 25 MGD from
``data/uv_cost_interp.csv``. Using this data, a cost curve is fit to a power curve. Once `a` and
`b` are known, capital costs for the UV system are determined:

    .. math::

        C_{UV} = a Q_{in} ^ b
|
Oxidant Capital Costs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The unit can accept any chemical name and dose, but the cost curve used was developed
specifically for Hydrogen Peroxide.

Oxidant costs are calculated with:

    .. math::

        C_{ox} = 1228 ( Q_{in} * D_{ox} ) ^ {0.2277}
|
Where the oxidant dose [kg/m3] is taken from the input parameter ``"dose"``.

If ``"aop"`` is ``False`` in the unit parameters:

    .. math::

        C_{ox} = 0
|
Electricity Intensity
-------------------------

Electricity intensity for chlorination is fixed at 0.1 kWh/m3 and is taken from USEPA (2010).

References
-----------

CAPITAL
*********

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

ELECTRICITY
*************

| US Environmental Protection Agency (2010)
| "Evaluation of Energy Conservation Measures for Wastewater Treatment Facilities"
| https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=P1008SBM.TXT

UV + AOP Module
----------------------------------------

.. autoclass:: watertap3.wt_units.uv_aop.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak