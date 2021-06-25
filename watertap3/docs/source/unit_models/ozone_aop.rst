Ozone and Ozone+AOP
============================================================

Unit Basics
--------------

The Ozone unit in WaterTAP3 is used to calculate costs for both Ozone and Ozone+AOP systems.

Unit Parameters
------------------

Unit parameters are read in from the ``unit_params`` dictionary given in the input sheet.

* ``"aop"`` - boolean to indicate if the unit includes AOP costs:

    * Required parameter

    * If ``True``, oxidant costs are included

    * If ``False``, oxidant costs are excluded

* ``"contact_time"`` - contact time with ozone [min]

    * Required parameter

* ``"ct"`` - Concentration * time (Ct) target [mg/(L*min)]

    * Required parameter

* ``"mass_transfer"`` - mass transfer coefficient for ozone contactor

    * Required parameter

* ``"chemical_name"`` - oxidant chemical name

    * Required parameter if ``aop = True``

    * Must match exactly the chemical name in ``chemical_name.csv``



Capital Costs
---------------

Ozone Capital Costs
*********************

Ozone capital costs in WaterTAP3 are a function of the ozone contact time :math:`\big( t \big)`,
Ct, ozone mass transfer :math:`\big( \eta \big)`, ozone dose
:math:`\big( D_{O3} \big)`, TOC concentration :math:`\big( c_{toc} \big)`, flow in
:math:`\big( Q{in} \big)`, and the ozone/TOC ratio :math:`\big( R \big)`.

TOC concentration and flow in are taken from the model. Contact time, mass transfer, and Ct are
taken from user input. Ozone demand is calculated as:

    .. math::

         D_{O3} = \large{ \frac{ \frac{  c_{toc} + Ct }{ t }}{ \normalsize{\eta} } }

Ozone dose is then used in a regression dervied from data found in Table 3.24 from the reference
below.

Oxidant Capital Costs
************************

The unit can accept any chemical name and dose, but the cost curve used was developed
specifically for Hydrogen Peroxide.

Oxidant costs :math:`\big( C_{ox} \big)` are calculated with:

    .. math::

        C_{ox} = 1228 \big( Q_{in} \times D_{ox} ) ^ {0.2277}

Where :math:`D_{ox}` is the oxidant dose [kg/m3]:

    .. math::

        D_{ox} = 0.5 \times R \times c_{toc}

Electricity Intensity
------------------------


References
-------------------

COSTING
*********

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

ELECTRICITY
*************



Ozone + AOP Module
----------------------------------------

.. autoclass:: watertap3.wt_units.ozone_aop.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build
