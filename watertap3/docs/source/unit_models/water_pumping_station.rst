.. _water_pumping_station_unit:

Water Pumping Station
============================================================

Unit Basics
--------------

This is a pump unit in WaterTAP3.

Unit Parameters
--------------------

There are three unit parameters:

* ``"pump_type"`` - the type of water pumping station:

    * Required parameter
    * Options are "raw" or "treated"
    * Different costing values are used for each option
|
* ``"pump_power"`` - pump power if available [hp]:

    * Optional parameter
|
* ``"lift_height"`` - amount of dynamic head [ft]:

    * Optional parameter
    * Default value is 100 ft
|
Capital Costs
---------------

Depending on the value for ``"pump_type"``, different cost curves are used for the general form
with flow in [MGD] from McGivney & Kawamura (2008):

    .. math::

        C_{wps} = a Q_{in} ^ b
|
For ``"pump_type"`` = "raw":

    * `a` = 19370.36
    * `b` = 0.9149
|
For ``"pump_type"`` = "treated":

    * `a` = 40073.43
    * `b` = 0.8667
|
Electricity Intensity
------------------------

If there is no input for ``"pump_power"``, electricity intensity is a function of flow [gpm] and
the unit parameter ``"lift_height"`` `h`:

    .. math::

        E_{wps} = \frac{0.746 Q_{gpm} h}{3960 \eta_{pump} \eta_{motor} Q_{in}}
|
With assumed pump and motor efficiencies of 90%.

Otherwise, the input for ``"pump_power"`` is converted from horsepower to kW and electricity
intensity is:

    .. math::

        E_{wps} = \frac{p_{pump}}{Q_{in}}
|
References
----------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Water Pumping Station Module
----------------------------------------

.. autoclass:: watertap3.wt_units.water_pumping_station.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak