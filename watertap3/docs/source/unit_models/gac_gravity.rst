GAC - Gravity
============================================================

The gravity GAC unit in WaterTAP3 is based off of a regression of several runs using
EPA's Work Breakdown Structure-Based (WBS EPA) model. These models each have some "standard
designs" that make default assumptions and span a range of flows 0.03 MGD to 75 MGD (USEPA (2019)).

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for each of the EPA model standard designs with the gravity GAC option. A similar approach
is taken to determine electricity intensity.

Both sets of data are fit to a power curve. Then `a` and `b` are used with the flow for the model
to determine capital and electricity intensity.

Unit Parameters
--------------------

Anion exchange has one parameter:

* ``"ebct"`` - empty bed contact time for the unit [min]:

    * Required parameter
    * There are different costing data for 0-60 min and >60 min
|
Capital Costs
---------------

The ``cap_total`` column is read in from the ``cost_curves.csv`` based on user-defined EBCT and is
fit to a power curve. Then `a` and `b` from that regression is used with the
unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{gac} = a Q_{in} ^ b
|
Electricity Intensity
------------------------

The ``electricity_flow`` column is read in from the ``cost_curves.csv`` based on user-defined EBCT
and is fit to a power curve. Then `a` and `b` from that regression is used with the unit flow
[m3/hr] to determine electricity intensity:

    .. math::

        E_{gac} = a Q_{in} ^ b
|
Chemical Use
--------------

The WBS EPA model includes costs for activated carbon. The average is taken for the range of flows
and assumed to be the "dose" for the particular chemical/material.


References
--------------

| US Environmental Protection Agency (2017)
| "Work Breakdown Structure-Based Cost Model for Granular Activated Carbon Drinking Water Treatment"
| https://www.epa.gov/sites/production/files/2019-03/documents/wbs-gac-documentation-dec-2017_v2.pdf
| https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models

Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.gac_pressure_vessel.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak