Storage Tanks
=====================================

Tank costs are calculated as a function of the volume of storage required. The storage required is calculated as:

  .. math::

    \small\text{Storage Capacity = Flow In * Storage Duration * (1 + Surge Capacity)}

  .. math::

    \small\text{flow in = inlet flow to the tank}

    \small\text{storage duration = hours of storage required}

    \small\text{surge capacity = percentage of additional capacity required}

Once the capacity is calculated, the cost data below is used to calculate the FCI. The cost data is
based on figure X from DOE/NETL-2002/1169 - Process Equipment Cost Estimation. The assumed data points
from the curve are provided below and an adapted cost curve is generated using the scipy curve fit
function.

.. csv-table::
    :header: Cost ($MM), Storage Capacity (m :superscript:`3`)
    :file: csvs/storage_tanks.csv

Import table from a CSV file

.. csv-table:: Tank Example
   :file: files/tank.csv

Cost curve equation in WaterTAP3:

  .. math::

    \text{Cost(\$MM)} = 1.48\times10^{-4} \big(\text{Storage Capacity ^ {1.014}}\big)

The tank unit model does not include any electricity costs or other unit-specific O&M costs.

Storage Tank Module
----------------------------------------

.. autoclass:: watertap3.wt_units.holding_tank.UnitProcess
   :members: get_costing, fixed_cap, electricity
   :undoc-members: build
   :exclude-members: build

