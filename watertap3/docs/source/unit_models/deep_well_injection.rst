Deep Well Injection
==========================

Unit Basics
--------------
Deep well injection is used as a ZLD technology to dispose of brine waste from desalination
treatment processes.

Unit Parameters
--------------------

The evaporation pond model in WaterTAP3 draws from several sources and includes several optional
parameters for user input. Further detail on these parameters is provided below:

* ``"lift_height"`` - lift height for injection pump [ft]:

    * Optional parameter
    * Default value is 400 ft

* ``"pipe_distance"`` - pipe distance from facility to deep well injection site [mi]

    * Required parameter


Capital Costs
---------------

Capital costs for deep well injection are based off of the costs for the Kay Baily Hutchinson
(KBH) deep well injection site. Costing calculation is split into well construction and pipe
construction. From the KBH data, well construction is $16.9 MM. Piping
cost assumes an 8 in diameter pipe, and is calculated as:

    .. math::

        C_{pipe} = 0.28 x_{pipe}

The total fixed cost is then calculated by scaling with KBH flow according to:

    .. math::

        C_{dwi} = ( C_{well} + C_{pipe} ) \frac{Q_{in}}{Q_{KBH}} ^ {0.7}

Electricity Intensity
------------------------

Electricity intensity for deep well injection in WaterTAP3 is based off the pump used for
injection. The model assumes:

    * Lift height = 400 ft

        * Can be changed by user in unit parameters (see above)
    * Pump efficiency = 90%
    * Motor efficiency = 90%


Module
----------------------------------------

.. autoclass:: watertap3.wt_units.deep_well_injection.UnitProcess
    :members: fixed_cap, elect
    :exclude-members: build


..  raw:: pdf

    PageBreak