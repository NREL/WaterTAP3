.. _chlorination_unit:

Chlorination
=================

Costs for chemical additions are based on the chemical dose required to treat the water and the inlet flow to the unit.

Unit Parameters
--------------------

There are two unit parameters:

* ``"chemical_name"`` - the name of the chemical for chlorination:

    * Required parameter
    * Must be in single ``' '`` or double ``" "`` quotes
|
* ``"dose"`` - chlorination dose [mg/L]:

    * Optional parameter
    * Default value is 9.5 mg/L (calculated below)
|

The following unit parameters must be provided together or the default values are used:

* ``"contact_time"`` - chlorination contact time [hr]:

    * Optional parameter
    * Default value is 1.5 hr
|
* ``"ct"`` - CT value [mg*min/L]:

    * Optional parameter
    * Default value is 450 mg*min/L 
|
* ``"chlorine_decay_rate"`` - chlorine decay rate [mg/L*hr]:

    * Optional parameter
    * Default value is 3 mg/L*hr 
|
Capital Costs
---------------------------------

Chlorination capital costs are a function of the applied chlorine dose and the flow using data
in Table 3.23 of the Texas Water Development Board (2016).

If ``"dose"`` is not provided by the unit parameters in the input sheet, the chlorine dose is calculated from:

    .. math::

        D_{Cl} = d + r t + \frac{Ct}{t}

* `d` = Chlorine demand [mg/L]
* `r` = Chlorine decay rate [mg/Lhr]; default = 3
* `t` = Contact time [hr]; default = 1.5
* `Ct` = Desired Ct [mg*min/L]; default = 450
|
Then, using the data provided in Table 3.23 from the Texas Water Board reference, cost data is read in based on the dose and fit to
the general form based on flow [MGD]:

    .. math::

        C = a Q ^ b
|
In other words, values of `a` and `b` will depend on the dose used for the unit. Once `a` and `b`
are known, the capital costs for chlorination are:

    .. math::

        C_{Cl} = a Q_{in} ^ b
|
Electricity Intensity
------------------------

Electricity intensity for chlorination is fixed at 5E-5 kWh/m3 and is taken from Bukhary,
et al. (2019).

Assumptions
------------------------

According to the reference, capital costs only include chemical feed equipment and assume there
is sufficient contact time downstream of the chlorine feed point.


References
------------------------

CAPITAL
*********

| `User's Manual for Integrated Treatment Train Toolbox - Potable Reuse (IT3PR) Version 2.0 <https://www.twdb.texas.gov/publications/reports/contracted_reports/doc/1348321632_manual.pdf>`_
| Steinle-Darling, E., Salveson, A., Russel, C., He, Q., Chiu, C., Lesan, D.
| Texas Water Development Board
| December 2016

ELECTRICITY
****************

| Bukhary, S., Batista, J., Ahmad, S. (2019).
| An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water TreatmentPlant.
| *Water*, 12(1), 1-21.


Chlorination Module
----------------------------------------

.. autoclass:: watertap3.wt_units.chlorination.UnitProcess
   :members: fixed_cap, elect, get_costing
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak