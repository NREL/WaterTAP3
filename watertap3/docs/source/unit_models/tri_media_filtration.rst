.. _tri_media_filtration_unit:


Tri-Media Filtration
============================================================

Unit Parameters
--------------------

None

Capital Costs
---------------

The capital costs are a function of flow [MGD] from the Texas Water Development Board (2016):

    .. math::

        C_{tri} = 0.72557 Q_{in} ^ {0.5862}

Electricity Intensity
------------------------

Electricity intensity is fixed at 0.00045 kWh/m3 from Bukhary et al. (2019).

References
______________

CAPITAL
*********

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

ELECTRICITY
***************

| Bukhary, S., et al. (2019).
| "An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water Treatment Plant."
| *Water* 12(1).

Tri-Media Filtration Module
----------------------------------------

.. autoclass:: watertap3.wt_units.tri_media_filtration.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak