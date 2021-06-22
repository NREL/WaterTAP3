Chlorination
=================

In general, costs for chemical additions in WaterTAP3 are a function of the chemical dose and the
flow in. The chemical solution flow is calculated from these two values and assumed solution
densities to use in a cost curve. All chemical additions assume 2 chemical addition units.

Chlorination Capital Costs
---------------------------------
Chlorination capital costs are a function of the applied chlorine dose and the flow using data
in Table 3.23 of the Texas Water Board reference (below).

The chlorine dose is calculated from:

:math:`\text{Dose [mg/L]} = Cl_{demand} + r_{decay} t + \frac{Ct}{t}`

* :math:`\small{Cl_{demand}}` = Chlorine demand [mg/L]
* :math:`r_{decay}` = Chlorine decay rate [mg/Lhr]; default = 3
* :math:`t` = Contact time [hr]; default = 1.5
* :math:`Ct` = Desired Ct [mg*min/L]; default = 450

Assumptions:
****************

According to the reference, capital costs only include chemical feed equipment and assume there
is sufficient contact time downstream of the chlorine feed point.


Electricity Cost
------------------
Electricity intensity for chlorination is fixed at  :math:`5 \times 10 ^ {-5}` kWh/m3 and is taken
from the below reference.


Reference:
*************
CAPITAL

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

ELECTRICITY

| An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water Treatment Plant.
| Bukhary, S., Batista, J., Ahmad, S. (2019).
| Water, 12(1), 1-21.




Alum Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.chlorination.UnitProcess
   :members: fixed_cap, elect, get_costing
   :undoc-members: build
   :exclude-members: build