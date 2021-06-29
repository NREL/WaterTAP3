Storage Tanks
=====================================

Unit Parameters
--------------------

* ``"avg_storage_time"`` - storage time for volume calculation [hr]

    * Required parameter

* ``"surge_cap"`` - desired surge capacity for volume calculation

    * Required parameter
    * Can be zero if no surge capacity is desired

Capital Costs
---------------

Storage tank capital costs are calculated as a function of the volume of storage
[m3] required, flow in [m3/hr], storage duration [hr], and surge capacity needed:

    .. math::

        V = Q_{in} t (1 + x)
|
The storage volume is used to calculate capital costs ($MM):

    .. math::

        C_{tank} = 1.48 \times 10 ^ {-4} V ^ {1.014}
|
The data to make the regression is from Loh et al. (2002).

Electricity Intensity
------------------------

There are no electricity costs associated with storage tanks in WaterTAP3.

Reference
-----------

| Loh, H. P., Lyons, J., White, C.W. (2002)
| DOE/NETL-2002/1169 - Process Equipment Cost Estimation Final Report.
| United States: N. p., 2002. Web. doi:10.2172/797810.
| https://www.osti.gov/servlets/purl/797810

Storage Tank Module
----------------------------------------

.. autoclass:: watertap3.wt_units.holding_tank.UnitProcess
   :members: fixed_cap, elect, get_costing
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak