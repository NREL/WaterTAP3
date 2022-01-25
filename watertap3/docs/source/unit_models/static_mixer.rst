.. _static_mixer_unit:

Static Mixer
============================================================

Unit Parameters
--------------------

None.

Capital Costs
---------------

Capital costs for stati mixer are based off the costing equation in Table 7.2 of Towler & Sinnott (2012). The equation from the reference
is for flow in liters per second, and the equation in WaterTAP3 has been adapted to be used for m3/hr:

    .. math::

        C_{sm} = 14317.14 + 389.5 Q ^{-57.342}
|
This cost is then multiplied by the number of units and the EIF factor for the final FCI for the static mixer. 

Electricity Intensity
------------------------

None.


Assumptions
_____________

* Number of units = 2

References
______________

| Gavin Towler & Ray Sinnott (ed.) (2012)
| Chemical Engineering Design (Second Edition): Principles, Practice and Economics of Plant and Process Design
| Chapter 7 - Capital cost estimating
| ISBN: 9780080966601


Static Mixer Module
----------------------------------------

.. autoclass:: watertap3.wt_units.static_mixer.UnitProcess
    :members: fixed_cap, elect
    :exclude-members: build


..  raw:: pdf

    PageBreak