Electrodialysis Reversal
============================================================

Unit Parameters
--------------------

None.

Capital Costs
---------------

Capital costs for electrodialysis reversal are based on those from the Irwin case study.

    .. math::

        C_{EDR} = 31 \frac{Q_{in}}{946}
|
Electricity Intensity
------------------------

Electricity intensity is a function of TDS [mg/L] into the unit and based off of a regression of
data from Baker (2004):

    .. math::

        E_{EDR} = 0.2534 + 5.149 \times 10 ^ {-4} c_{tds}
|
References
------------

ELECTRICITY
************

| Richard W. Baker (2004)
| "Membrane Technology and Applications, Second Edition"
| DOI:10.1002/0470020393

Electrodialysis Reversal Module
----------------------------------------

.. autoclass:: watertap3.wt_units.electrodialysis_reversal.UnitProcess
    :members: fixed_cap, elect, uv_regress, get_costing, solution_vol_flow
    :exclude-members: build


..  raw:: pdf

    PageBreak