Caustic Soda Addition
=====================================

In general, costs for chemical additions in WaterTAP3 are a function of the chemical dose and the
flow in. The chemical solution flow is calculated from these two values and assumed solution
densities to use in a cost curve. All chemical additions assume 2 chemical addition units.

Capital Costs:
---------------

The caustic soda flow `S` is used in a cost curve of the general form:

    .. math::

        C = S a ^ b

For a single caustic soda addition unit, `a` = 2262.8 and `b` = 0.6195. The full cost equation in
WaterTAP3 is:

    .. math::

        C_{NaOH} = N_{units}( 2262.8 S ) ^ {0.6195}

These parameters were determined by fitting data from FIGURE 5.5.12b - SODIUM HYDROXIDE FEED in
the below reference to the general form.


Assumptions:
****************

* Number of units = 2
* Chemical solution density [kg/m3] = 1540
* Ratio in solution = 50%


Electricity Intensity
------------------------

Electricity intensity for chemical additions in WaterTAP3 is based off the pump used to inject
the chemical solution, the chemical solution flow rate, and the influent flow rate. The model
assumes:

* Lift height = 100 ft
* Pump efficiency = 90%
* Motor efficiency = 90%

Reference
------------------------

| William McGivney & Susumu Kawamura (2008)
| Cost Estimating Manual for Water Treatment Facilities
| DOI:10.1002/9780470260036

Caustic Soda Module
----------------------------------------

.. autoclass:: watertap3.wt_units.caustic_soda_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak