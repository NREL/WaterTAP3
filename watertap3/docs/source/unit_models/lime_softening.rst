Lime Softening
=====================================

Unit Parameters
--------------------

There is one unit parameter:

*``"lime"`` - lime dose for unit [mg/L]:

    * Required parameter

Capital Costs
---------------

The capital costs are a function of flow [m3/hr]:

    .. math::

        C_{lime} = 0.0704 Q_{in} ^ {0.7306}

Assumptions
--------------

Several aspects of the unit are assumed:

The lift height is 300 ft:

    .. math::

        h = 100

The pump and motor efficiency are 90%:

    .. math::

        \eta_{pump} = \eta_{motor} = 0.9

The lime solution density is 1250 kg/m3.

Electricity Intensity
------------------------

Electricity intensity for chemical additions in WaterTAP3 is based off the pump used to inject
the lime solution.

References
------------

| Minnesota Rural Water Association, Chapter 16 Lime Softening
| https://www.mrwa.com/WaterWorksMnl/Chapter%2016%20Lime%20Softening.pdf


Lime Softening Module
----------------------------------------

.. autoclass:: watertap3.wt_units.lime_softening.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak