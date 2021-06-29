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


The storage volume is used to calculate capital costs ($MM):

    .. math::

        C_{tank} = V a ^ b`


Electricity Intensity
------------------------

There are no electricity costs associated with storage tanks in WaterTAP3.

Reference
-----------

Data Used
*************

.. csv-table:: Cost ($MM) vs. Volume
    :file: csvs/storage_tanks.csv
    :align: center

This data comes from "cone roof tanks" on page 7.
The `full reference <https://www.osti.gov/servlets/purl/797810>`_ is:

| DOE/NETL-2002/1169 - Process Equipment Cost Estimation Final Report.
| Loh, H. P., Lyons, Jennifer, and White, Charles W.
| United States: N. p., 2002. Web. doi:10.2172/797810.


Storage Tank Module
----------------------------------------

.. autoclass:: watertap3.wt_units.holding_tank.UnitProcess
   :members: fixed_cap, elect, get_costing
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak