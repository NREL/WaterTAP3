Crystallizer
============================================================

Unit Basics
--------------

Crystallizers in WaterTAP3 are modeled after thermal crystallizers
routinely used in zero liquid discharge (ZLD) schemes.

Capital Costs
---------------

Capital costs for crystallizers are a function of influent TDS :math:`\big(c_{TDS} \big)`,
water recovery :math:`\big( x_{wr} \big)`, and flow in :math:`\big( Q_{in} \big)`.
The regression is based off of data found in Tables A2.1 and A2.3 found in the below reference.

    .. math::

           \text{Cost } ($MM) = 1.41 - 7.11 \times 10 ^ {-7} \big( c_{TDS} \big) +
           1.45 \big(x_{wr} \big) + 0.56 \big( Q_{in} \big)

Electricity Intensity
-----------------------

Electricity intensity for crystallizers is a function of influent TDS :math:`\big(c_{TDS} \big)`,
water recovery :math:`\big( x_{wr} \big)`, and flow in :math:`\big( Q_{in} \big)`.
The regression is based off of data found in Tables A2.1 and A2.3 found in the below reference.

    .. math::

           \text{Electricity  [kWh/m3]} = 56.7 + 1.83 \times 10 ^ {-5} \big( c_{TDS} \big) -
           9.47 \big(x_{wr} \big) - 8.63 \times 10 ^ {-4} \big( Q_{in} \big)

Reference
-----------------------

| Mickley, Michael C. (2008)
| "Survey of High-Recovery and Zero Liquid Discharge Technologies for Water Utilities"
| WateReuse Foundation
| ISBN: 978-1-934183-08-3


Crystallizer Module
----------------------------------------

.. autoclass:: watertap3.wt_units.crystallizer.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
