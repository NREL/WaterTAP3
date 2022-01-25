.. _landfill_zld_unit:

Landfill ZLD
============================================================

Unit Basics
--------------

This unit is a terminal unit in WaterTAP3 and represents the cost of sending residual solids to
landfill.

Unit Parameters
--------------------

None.

Capital Costs
---------------

Landfill ZLD costs are a function of mass flow into the unit:

    .. math::

        C_{lf} = \frac{M_{in}}{302096} ^ {0.7}

|
The 0.7 exponent is a generic exponent used to make order-of-magnitude cost estimates 
for processes where only the cost and flow (or capacity) are known from a previous facility that used the same process (Towler & Sinnott, 2021).
|
The mass flow is calculated by first calculating the total concentration flowing into the unit:

    .. math::

       C_{in} = \sum_{i}^{n} c_i
|
Then, we estimate the density of the solution [kg/m3]:

    .. math::

        \rho_{in} = 0.6312 ( C_{in} ) + 997.86
|
Mass flow [kg/hr] is determined with:

    .. math::

        M_{in} = \rho_{in} Q_{in}

|
Electricity Intensity
------------------------

There are no electricity costs associated with landfill ZLD in WaterTAP3.

References
-------------

| Mickley, Michael C. (2008)
| "Survey of High-Recovery and Zero Liquid Discharge Technologies for Water Utilities"
| WateReuse Foundation
| ISBN: 978-1-934183-08-3

| Gavin Towler & Ray Sinnott (ed.) (2021)
| Chemical Engineering Design (Third Edition): Principles, Practice and Economics of Plant and Process Design
| Chapter 7 - Capital cost estimating, pg 239-278
| DOI: 10.1016/B978-0-12-821179-3.00007-8
| ISBN: 9780128211793


Landfill ZLD Module
----------------------------------------

.. autoclass:: watertap3.wt_units.landfill_zld.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak