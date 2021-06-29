Anion Exchange
============================================================

Unit Basics
--------------

The anion exchange model in WaterTAP3 is based off of a regression of several runs using EPA's
Work Breakdown Structure-Based (WBS EPA) model (see reference). These models incorporate
several aspects of cost of the treatment process, including treatment, monitoring, and
administrative costs. Both capital cost and electricity intensity are based entirely on
volumetric flow, but are assumed to incorporate these costing aspects of the EPA model.

The WBS EPA models each have some "standard designs" that make default assumptions (see EPA
documentation) and span a range of flows 0.03 MGD to 75 MGD. Influent sulfate (called ``tds_in``
for WT3) also affects cost. The EPA model outputs several costing parameters, including total
capital cost.

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for  each ofthe EPA model standard designs using influent sulfate of 50, 100, and 150 mg/L.
The different capital costs for each of these model runs is determined from the user input
``tds_in``. i.e. the cost curve is different if the influent sulfate is 100 mg/L vs. 900 mg/L. A
similar approach is taken to determine electricity intensity.

Both sets of data are fit to a power curve:

    .. math::

        Y = a Q ^ b

Where `Q` is the flows for the standard design EPA models. Then `a` and `b` are used with the
flow in for the particular case study.

Unit Parameters
--------------------

Anion exchange has one parameter:

* ``"tds_in"`` - the influent sulfate to the unit [mg/L]:

    * Required parameter

    * There are different costing data for 0-50, 50-100, and >150 mg/L

Capital Costs
---------------

The ``cap_total`` column is read in from the ``cost_curves.csv`` based on influent TDS and is
fit to the power curve described above. Then `a` and `b` from that regression is used with the
unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{ax} = a Q_{in} ^ b


Electricity Intensity
------------------------

The ``electricity_flow`` column is read in from the ``cost_curves.csv`` based on influent TDS
and is fit to the power curve described above. Then `a` and `b` from that regression is used with
the unit flow [m3/hr] to determine capital costs:

    .. math::

        E_{ax} = a Q_{in} ^ b


Chemical Use
--------------

The WBS EPA model includes costs for sodium chloride and ion exchange resins. Rather than fit
this data to a cost curve vs. standard design flows, the average is taken for the range of flows
and assumed to be the "dose" for the particular chemical/material.


References
--------------

| US Environmental Protection Agency (2017)
| "Work Breakdown Structure-Based Cost Model for Anion Exchange Drinking Water Treatment"
| https://www.epa.gov/sites/production/files/2019-03/documents/wbs-anion-documentation-dec-2017_v3.pdf

Unit Template
----------------------------------------

.. autoclass:: watertap3.wt_units.anion_exchange.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build
