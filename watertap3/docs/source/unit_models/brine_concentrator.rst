Brine Concentrator
============================================================

The brine concentrator represents a thermal (evaporative brine concentrator) based on WateReuse
Foundation (2008).

Unit Parameters
--------------------

None.

Capital Costs
---------------

Capital costs for brine concentrators are a function of influent TDS, water recovery, and flow in.
The regression is based on data found in Tables 5.1 and A2.3 found in WateReuse Foundation (2008).

    .. math::

           C_{brine} = 15.1 + 3.02 \times 10 ^ {-4} ( c_{TDS} ) -18.8 (x_{wr} ) + 8.08 \times 10 ^ {-2} ( Q_{in} )
|
Electricity Intensity
-----------------------

Electricity intensity is a function of the same variables and uses the same reference.

    .. math::

           E_{brine} = 9.73 + 1.1 \times 10 ^ {-4} ( c_{TDS} ) +10.4 (x_{wr} ) + 3.83 \times 10 ^ {-5} ( Q_{in} )
|
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


..  raw:: pdf

    PageBreak