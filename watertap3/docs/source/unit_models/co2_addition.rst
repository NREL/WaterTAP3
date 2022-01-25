.. _co2_addition_unit:

Carbon Dioxide Addition
=====================================

Unit Parameters
--------------------

None

Capital Costs
---------------

The capital costs are a function of flow [MGD] from McGivney & Kawamura (2008):

    .. math::

        C_{co2} = 0.464 Q_{in} ^ {0.7}
|
The 0.7 exponent is a generic exponent used to make order-of-magnitude cost estimates 
for processes where only the cost and flow (or capacity) are known from a previous facility that used the same process (Towler & Sinnott, 2021).
|
Electricity Intensity
------------------------

None.

References
------------

CAPITAL
**********

| Gavin Towler & Ray Sinnott (ed.) (2021)
| Chemical Engineering Design (Third Edition): Principles, Practice and Economics of Plant and Process Design
| Chapter 7 - Capital cost estimating, pg 239-278
| DOI: 10.1016/B978-0-12-821179-3.00007-8
| ISBN: 9780128211793

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036



Carbon Dioxide Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.co2_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak