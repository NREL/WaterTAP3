Storage Tanks
=====================================

Capital Costs
---------------

Storage tank capital costs are calculated as a function of the volume of storage required:

:math:`V_{s} = Q_{in} t (1 + x)`

* :math:`\small{V_{s} [m^3]}` = Storage volume needed
* :math:`Q_{in} [m^3/hr]` = Flow in to tank
* :math:`t [hr]` = Storage duration
* :math:`x` = Surge capacity

The storage volume is used to calculate capital costs ($MM):

:math:`Cost = V_{s} a ^ b`


`a` and `b` can be determined via regression of the following data with to::

        from scipy.optimize import curve_fit

        def power(x, a, b):
            return a * x ** b

        cost_MM = [0, 0.151967998, 0.197927546, 0.366661915, 0.780071937, 1.745265206, 2.643560777, 4.656835949, 6.8784383]
        storage_m3 = [1E-8, 191.2, 375.6, 1101.1, 3030, 8806, 16908, 29610, 37854.1]
        coeffs, _ = curve_fit(power, storage_m3, cost_MM)
        a, b = coeffs[0], coeffs[1]
        print(a, b)

Electricity Intensity
------------------------

The tank unit model does not include any electricity costs or other unit-specific O&M costs.

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
