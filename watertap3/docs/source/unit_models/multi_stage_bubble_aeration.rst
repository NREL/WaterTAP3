Multi-Stage Bubble Aeration
============================================================

The multi-stage bubble aeration unit in WaterTAP3 is based off of a regression of several runs using
EPA's Work Breakdown Structure-Based (WBS EPA) model. These models each have some "standard
designs" that make default assumptions and span a range of flows 0.03 MGD to 75 MGD (USEPA (2019)).

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for each of the EPA model standard designs. A similar approach is taken to determine
electricity intensity.

Both sets of data are fit to a power curve. Then `a` and `b` are used with the
flow for the model to determine capital and electricity intensity.

Unit Parameters
--------------------

None

Capital Costs
---------------

The ``cap_total`` column is read in from the ``cost_curves.csv`` based on influent TDS and is
fit to the power curve described above. Then `a` and `b` from that regression is used with the
unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{msba} = a Q_{in} ^ b

|
Electricity Intensity
------------------------

The ``electricity_flow`` column is read in from the ``cost_curves.csv`` based on influent TDS
and is fit to the power curve described above. Then `a` and `b` from that regression is used with
the unit flow [m3/hr] to determine capital costs:

    .. math::

        E_{msba} = a Q_{in} ^ b

|
Chemical Use
--------------

The WBS EPA model does not include any chemical/material costs for multi-stage bubble aeration.


References
--------------

| US Environmental Protection Agency (2017)
| "Work Breakdown Structure-Based Cost Model for Multi-Stage Bubble Aeration Drinking Water Treatment"
| https://www.epa.gov/sites/production/files/2019-03/documents/wbs-msba-documentation-dec-2017_v2.pdf
| https://www.epa.gov/sdwa/drinking-water-treatment-technology-unit-cost-models

Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.multi_stage_bubble_aeration.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build

..  raw:: pdf

    PageBreak