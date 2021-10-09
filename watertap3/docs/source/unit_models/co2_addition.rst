.. _co2_addition_unit:

Carbon Dioxide Addition
=====================================

Unit Parameters
--------------------

None

Capital Costs
---------------

The capital costs are a function of flow [MGD] in McGivney & Kawamura
(2008):

    .. math::

        C_{co2} = 0.464 Q_{in} ^ {0.7}
|
Electricity Intensity
------------------------

Electricity intensity is fixed at 0.01 kWh/m3 from ___________.

References
------------

CAPITAL
**********

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

ELECTRICITY
************


Carbon Dioxide Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.co2_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak