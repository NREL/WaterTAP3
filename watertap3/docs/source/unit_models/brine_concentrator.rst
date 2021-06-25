Brine Concentrator
============================================================

Unit Basics
--------------

Brine concentrators in WaterTAP3 are modeled after thermal (evaporative) brine concentrators
routinely used in zero liquid discharge (ZLD) schemes.

Capital Costs
---------------

Capital costs for brine concentrators are a function of influent TDS :math:`\big(c_{TDS} \big)`,
water recovery :math:`\big( x_{wr} \big)`, and flow in :math:`\big( Q_{in} \big)`. The regression
is based off of data found in Tables 5.1 and A2.3 found in the below reference.

    .. math::

           \text{Cost } ($MM) = 15.1 + 3.02 \times 10 ^ {-4} \big( c_{TDS} \big) -
           18.8 \big(x_{wr} \big) + 8.08 \times 10 ^ {-2} \big( Q_{in} \big)

Electricity Intensity
-----------------------

Electricity for brine concentrators is a function of influent TDS :math:`\big(c_{TDS} \big)`,
water recovery :math:`\big( x_{wr} \big)`, and flow in :math:`\big( Q_{in} \big)`. The regression
is based off of data found in Tables 5.1 and A2.3 found in the below reference.

    .. math::

           \text{Electricity  [kWh/m3]} = 9.73 + 1.1 \times 10 ^ {-4} \big( c_{TDS} \big) +
           10.4 \big(x_{wr} \big) + 3.83 \times 10 ^ {-5} \big( Q_{in} \big)

Reference
-----------------------

| Mickley, Michael C. (2008)
| "Survey of High-Recovery and Zero Liquid Discharge Technologies for Water Utilities"
| WateReuse Foundation
| ISBN: 978-1-934183-08-3


Brine Concentrator Module
----------------------------------------

.. autoclass:: watertap3.wt_units.brine_concentrator.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
