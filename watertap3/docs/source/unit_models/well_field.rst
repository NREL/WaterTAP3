Well Field
============================================================

Unit Parameters
--------------------

None.

Capital Costs
---------------

The capital costs are a function of flow [m3/hr] from Voutchkov (2018):

    .. math::

        C_{tri} = 4731.6 Q_{in} ^ {0.9196}

Electricity Intensity
------------------------

There are no electricity costs associated with well field in WaterTAP3.

References
______________

| Voutchkov, N. (2018).
| Desalination Project Cost Estimating and Management.
| https://doi.org/10.1201/9781351242738

Well Field Module
----------------------------------------

.. autoclass:: watertap3.wt_units.well_field.UnitProcess
    :members: fixed_cap, elect, get_costing
    :exclude-members: build


..  raw:: pdf

    PageBreak