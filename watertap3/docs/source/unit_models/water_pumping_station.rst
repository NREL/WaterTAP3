Water Pumping Station
============================================================

Unit Basics
--------------

This is a pump unit in WaterTAP3.

Unit Parameters
--------------------

There are two unit parameters:

* ``"pump_type"`` - the type of water pumping station:

    * Required parameter

    * Options are "raw" or "treated"

    * Different costing values are used for each option

* ``"pump_power"`` - pump power if available [hp]:

    * Optional parameter

Capital Costs
---------------

Depending on the value for ``"pump_type"``, different cost curves are used for the general form
with flow in [MGD]:

    .. math::

        C_{wps} = a Q_{in} ^ b

For ``"pump_type"`` = "raw":

    * `a` = 19370.36
    * `b` = 0.9149

For ``"pump_type"`` = "treated":

    * `a` = 40073.43
    * `b` = 0.8667

Electricity Intensity
------------------------

If there is no input for ``"pump_power"``, electricity intensity is a function of flow [gpm]:

    .. math::

        E_{wps} = 0.1024 \frac{Q_{in}}{440.3]

Otherwise, the input for ``"pump_power"`` is converted from horsepower to kW and electricity
intensity is:

    .. math::

        E_{wps} = \frac{p_{pump}}{Q_{in}}


References
----------------

??????????????????

Water Pumping Station Module
----------------------------------------

.. autoclass:: watertap3.wt_units.water_pumping_station.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak