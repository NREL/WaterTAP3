.. _filter_press_unit:

Filter Press
============================================================

The Filter Press module in WaterTAP3 can represent capital and electricity costs for both a belt filter press and pressure filter press.

Unit Parameters
--------------------

There are three optional unit parameters for the filter press module:

* ``"type"`` - the type of filter press to be modeled:

    * Optional parameter
    * Options are ``"belt"`` or ``"pressure"``
    * Default type is ``"belt"`` if no input provided
|
* ``"hours_per_day_operation"`` - hours per day the filter press is in operation [hr]:

    * Optional parameter
    * Default is 24 hours if no input provided
|
* ``"cycle_time"`` - cycle time duration [hours]:

    * Optional parameter
    * Default is 3 hours if no input provided
|

Capital Costs
---------------

The capital costs are a function of the flow into the filter press [gal/hr] (McGivney & Kawamura (2008)).

For belt filter press:

    .. math::

        C_{belt} = 146.29 * Q + 433972

For pressure filter press:

    .. math::

        C_{pressure} = 102794 Q ^ {0.4216}


Electricity Intensity
------------------------

The annual energy use data provided in Wang, Shammas, and Hung (2007) is a function of the filter press capacity (or volume) and is fit to a power curve:

    .. math::

        E = a V ^ b

Filter press capacity (or volume) [ft3] is the volume of solids the filter press must handle per cycle:

    .. math::

        V_{fp} = Q / n

Where 'n' is the number of cycles per day and is the hours per day of operation [hr/day] divided by the cycle time [hr]:

    .. math::

        n = \frac{t_{op}}{t_{cycle}}


Then, the electricity intensity [kWh/m3] is calculated as the annual energy use [kWh/yr] divided by the annual sludge flow [m3/yr] into the filter press.

For a belt filter press:

    .. math::

        E_{fp} = \frac{16.285 V_{fp} ^ {1.2434}}{Q} 

For a pressure filter press:

    .. math::

        E_{fp} = \frac{16.612 V_{fp} ^ {1.2195}}{Q} 

Assumptions
_____________

* Percent influent solids = 6%  

References
______________

CAPITAL
****************

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

ELECTRICITY
***********************

| Lawrence K. Wang, Nazih K. Shammas, Yung-Tse Hung (Ed.) (2007)
| Biosolids Treatment Processes
| Chap. 17 "Belt Filter Press" & Chap. 18 "Pressure Filtration"
| DOI: 10.1007/978-1-59259-996-7
| eBook ISBN: 978-1-59259-996-7


Filter Press Module
----------------------------------------

.. autoclass:: watertap3.wt_units.filter_press.UnitProcess
    :members: fixed_cap, elect, fp_setup
    :exclude-members: build


..  raw:: pdf

    PageBreak