UV Disinfection and Advanced Oxidation Process (UV + AOP)
============================================================

Unit Basics
--------------

The UV+AOP module in WaterTAP3 is used to determine costs for both UV disinfection and UV +
AOP units.

.. important:: Capital costs for UV systems in WaterTAP3 are significantly influenced by UV Dose, UVT,
    and flow. For most accurate capital cost, include these in input parameters.

Unit Parameters
-----------------

This module has one required parameter and three optional parameters for the input sheet:

* AOP (``aop``, required): Boolean; if True, include chemical costs
* UV Transmittance (``uvt_in``, optional): value between 0.5 and 0.99 in increments of 0.01; default is 0.9
* Reduction Equivalent Dose (RED) (``uv_dose``, optional): value between 10 and 1200 in increments of 10; default is 100
* Chemical name (``chemical_name``, optional): string that matches exactly chemical entry in catalysts_chemicals.csv; no default

Capital Costs
---------------

UV Capital Costs
*****************

Capital costs are a function of flow, UV dose, and UV Transmission (UVT). The WaterTAP3 model
uses data Table 3.22 in the below reference.


Oxidant Capital Costs
************************

The unit can accept any chemical name and dose, but the cost curve used was developed
specifically for Hydrogen Peroxide.

Oxidant costs :math:`\big( C_{ox} \big)` are calculated with:

    .. math::

        C_{ox} = 1228 \big( Q_{in} * D_{ox} ) ^ {0.2277}

Where :math:`D_{ox}` is the oxidant dose [kg/m3]:

    .. math::

        D_{ox} = 0.5 R c_{toc}

Electricity Intensity
-------------------------


Reference
-----------

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

UV + AOP Module
----------------------------------------

.. autoclass:: watertap3.wt_units.uv_aop.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build
