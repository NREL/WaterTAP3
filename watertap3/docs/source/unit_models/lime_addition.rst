Lime Addition
=====================================

In general, costs for chemical additions in WaterTAP3 are a function of the chemical dose and the
flow in. The chemical solution flow is calculated from these two values and assumed solution
densities to use in a cost curve. All chemical additions assume 2 chemical addition units.

Unit Parameters
--------------------

* ``"lime"`` - dose of lime [mg/L]

    * Required parameter

Capital Costs
---------------

The lime solution flow `S` is used in a cost curve of the general
form:

    .. math::

        C = S a ^ b

For a single lime addition unit, `a` = 16972 and `b` = 0.5435. The full cost equation in
WaterTAP3 is:

    .. math::

        C_{lime} = N_{units}( 16972 S ) ^ {0.5435}

These parameters were determined by fitting data from FIGURE 5.5.9 - LIME FEED in the below
reference to the general form.

Assumptions:
****************

* Number of units = 2
* Chemical solution density [kg/m3] = 1250

Reference:
*************

| Cost Estimating Manual for Water Treatment Facilities (2008)
| William McGivney & Susumu Kawamura
| DOI:10.1002/9780470260036

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

| Cost Estimating Manual for Water Treatment Facilities (2008)
| William McGivney & Susumu Kawamura
| DOI:10.1002/9780470260036

Lime Addition Module
----------------------------------------

.. autoclass:: watertap3.wt_units.lime_addition.UnitProcess
   :members: fixed_cap, elect, get_costing, solution_vol_flow
   :undoc-members: build
   :exclude-members: build


..  raw:: pdf

    PageBreak