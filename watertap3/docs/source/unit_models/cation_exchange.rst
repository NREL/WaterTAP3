.. _cation_exchange_unit:

Cation Exchange
============================================================

The cation exchange model in WaterTAP3 is based off of a regression of several runs using EPA's
Work Breakdown Structure-Based (WBS EPA) model (see reference). These models incorporate
several aspects of cost of the treatment process, including treatment, monitoring, and
administrative costs. Both capital cost and electricity intensity are based entirely on
volumetric flow, but are assumed to incorporate these costing aspects of the EPA model.

The WBS EPA models each have some "standard designs" that make default assumptions (see EPA
documentation) and span a range of flows 0.03 MGD to 75 MGD. Influent hardness (called ``tds_in``
for WT3) also affects cost. The EPA model outputs several costing parameters, including total
capital cost.

The approach for the WT3 model is to regress the total capital cost output from the EPA model vs.
flow for  each of vthe EPA model standard designs using influent TDS of 200, 600, and 1000 mg/L.
The different capital costs for each of these model runs is determined from the TDS into the
unit, which is determined dynamically by WaterTAP3 (e.g. the cost curve is different if the
influent TDS is 100 mg/L vs. 900 mg/L). A similar approach is taken to determine electricity
intensity.

Both sets of data are fit to a power curve:

    .. math::

        Y = a Q ^ b

Where `Q` is the flows for the standard design EPA models. Then `a` and `b` are used with the
flow in for the particular case study.

Unit Parameters
--------------------

None.


Capital Costs
---------------

The ``cap_total`` column is read in from the ``epa_cost_curves.csv`` based on influent TDS and is
fit to the power curve described above. Then `a` and `b` from that regression is used with the
unit flow [m3/hr] to determine capital costs:

    .. math::

        C_{cx} = a Q_{in} ^ b

Electricity Intensity
------------------------

The ``electricity_intensity`` column is read in from the ``epa_cost_curves.csv`` based on influent TDS
and is fit to the power curve described above. Then `a` and `b` from that regression is used with
the unit flow [m3/hr] to determine capital costs:

    .. math::

        E_{cx} = a Q_{in} ^ b


Chemical Use
--------------

The WBS EPA model includes costs for sodium chloride and ion exchange resins. Rather than fit
this data to a cost curve vs. standard design flows, the average is taken for the range of flows
and assumed to be the "dose" for the particular chemical.

References
--------------

| US Environmental Protection Agency (2017)
| "Work Breakdown Structure-Based Cost Model for Cation Exchange Drinking Water Treatment"
| https://www.epa.gov/sites/production/files/2019-03/documents/wbs-cation-documentation-dec-2017_v2.pdf

Cation Exchange Module
----------------------------------------

.. autoclass:: watertap3.wt_units.cation_exchange.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak