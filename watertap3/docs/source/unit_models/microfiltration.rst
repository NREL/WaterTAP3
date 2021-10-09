.. _microfiltration_unit:

Microfiltration
============================================================

Unit Parameters
--------------------

None

Capital Costs
---------------

Capital costs for microfiltration is based entirely on flow [MGD] from Table 3.20 in the Texas
Water Board reference:

    .. math::

        C_{MF} = 2.5 Q_{in}
|

Electricity Intensity
------------------------

Electricity intensity is fixed at 0.18 kWh/m3 from Plappally & Lienhard (2012).

References
-------------

CAPITAL
**********

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

ELECTRICITY
**************

| Plappally, A. K. and J. H. Lienhard V (2012).
| "Energy requirements for water production, treatment, end use, reclamation, and disposal."
| *Renewable and Sustainable Energy Reviews* 16(7): 4818-4848.


Microfiltation Module
----------------------------------------

.. autoclass:: watertap3.wt_units.microfiltration.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build

..  raw:: pdf

    PageBreak