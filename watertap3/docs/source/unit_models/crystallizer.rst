Crystallizer
============================================================

Unit Basics
--------------

Crystallizers in WaterTAP3 are modeled after thermal crystallizers routinely used in zero liquid 
discharge (ZLD) schemes.

Unit Parameters
--------------------

There are no unit parameters for the crystallizer.

Capital Costs
---------------

Capital costs for crystallizers are a function of influent TDS `c_{TDS}`, water recovery
`x_{wr}`, and flow in `Q_{in}`.

The regression is based off of data found in Tables A2.1 and A2.3 found in the below reference.

    .. math::

           C_{cryst} = 1.41 - 7.11 \times 10 ^ {-7} ( c_{TDS} ) + 1.45 (x_{wr} ) + 0.56 ( Q_{in} )

Electricity Intensity
-----------------------

Electricity intensity is a function of the same variables and uses the same reference.

    .. math::

           E_{cryst} = 56.7 + 1.83 \times 10 ^ {-5} ( c_{TDS} ) - 9.47 (x_{wr} ) - 8.63 \times 10^ {-4} ( Q_{in} )

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


..  raw:: pdf

    PageBreak