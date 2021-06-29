Media Filtration
============================================================

Unit Parameters
--------------------

None

Capital Costs
---------------

Capital costs for media filtration includes the cost of the filter and the cost of the backwash
system.

    .. math::

        C_{mf} = C_{filter} + C_{bw}

The cost of the filter is a function of the surface area and the number of units:

    .. math::

        C_{filter} = (92497 + 38.319 A) n

With the filter surface area calculated as [ft2]:

    .. math::

        A = \frac{Q_{in}}{v}

The cost of the backwash system is also a function of filter surface area:

    .. math::

        C_{bw} = 92947 + 292.44 A


Assumptions
--------------

Several aspects of the unit are assumed:

There are six units:

    .. math::

        n = 6

The filtration rate is 10 m/hr:

    .. math::

        v = 10


Electricity Intensity
------------------------

Electricity intensity is fixed at 0.00015 kWh/m3 from the below reference.

References
--------------

CAPITAL
*********

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

ELECTRICITY
***********

| Bukhary, S., et al. (2019).
| "An Analysis of Energy Consumption and the Use of Renewables for a Small Drinking Water Treatment Plant."
| *Water* 12(1).



Media Filtration Module
----------------------------------------

.. autoclass:: watertap3.wt_units.media_filtration.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
