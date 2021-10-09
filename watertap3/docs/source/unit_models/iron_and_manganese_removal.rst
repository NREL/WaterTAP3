.. _fe_mn_removal_unit:

Iron & Manganese Removal
============================================================

The Fe/Mn removal unit in WaterTAP3 is based off of the dual media filtration schematic in the
Lenntech reference using costing data in McGivney & Kawamura (2008).

Unit Parameters
--------------------

None

Capital Costs
---------------

The coagulation/flocculation unit in WaterTAP3 includes costing for filtration media, backwash
system, and air blower.

    .. math::

        C_{Fe/Mn} = (C_{filt} + C_{bw} + nC_{blow}) \frac{Q_{in}}{4732} ^ {0.7}

|
Filtration capital is a function of media surface area and calculated with:

    .. math::

        C_{filt} = 21377 + 38.319 A
|
Backwash capital is also a function of media surface area:

    .. math::

        C_{bw} = 92947 + 292.44 A
|

The blower capital is assumed.


Assumptions
--------------

There are six units:

    .. math::

        n = 6
|
The filter surface area is 6243 ft2:

    .. math::

        A = 6243
|
The air/water ratio in the blower is 0.001 [v/v]:

    .. math::

        r = 0.001
|
The capital for the air blower is $100,000:

    .. math::

        C_{blow} = 100000
|
Electricity Intensity
------------------------

The total electricity intensity for Fe/Mn removal is from the blower [kWh/m3]:

    .. math::

        E_{Fe/Mn} = \frac{p_{blow} }{Q_{in}}
|
Where blower power is calculated with [hp]:

    .. math::

        p_{rm} = 147.8 q_{air}
|
And the air flow rate is [m3/hr]:

    .. math::

        q_{air} = Q_{in} r
|

References
-------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

| Schema of an iron removal system
| https://www.lenntech.com/schema-of-an-iron-removal-system.htm

Iron & Manganese Removal Module
----------------------------------------

.. autoclass:: watertap3.wt_units.iron_and_manganese_removal.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak