.. _cartridge_filtration_unit:

Cartridge Filtration
============================================================

Unit Parameters
--------------------

None

Capital Costs
---------------

The capital costs are a function of flow [MGD] with cost curve parameters from section 3.5.6, figure 3.3 in Texas Water Development Board (2016):

    .. math::

        C_{cart} = 0.72557 Q_{in} ^ {0.5862}
|
Electricity Intensity
------------------------

Electricity intensity for cartridge filtration is fixed at 2E-4 kWh/m3 and is taken from Bukhary,
et al. (2019).

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

| Bukhary, S., Batista, J., Ahmad, S. (2019).
| An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water Treatment Plant.
| *Water*, 12(1), 1-21.


Cartridge Filtration Module
----------------------------------------

.. autoclass:: watertap3.wt_units.cartridge_filtration.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak