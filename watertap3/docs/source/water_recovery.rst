Water Recovery
==========================

``data/water_revovery.csv``

Water recovery is represented as the fraction (between zero and one) of water recovered (treated)
after it passes through a unit process.  Case-study based water recovery is given for certain unit processes
if the case study has a unique recovery rate, otherwise default value are used. The total system water
recovery is calculated as:


The mass balance for water flow for each unit process is:

The columns are:

* **case_study**: The treatment facility name or default

* **scenario**: The name of the scenario that the values correspond with

* **unit_process**: The name of the unit process corresponding to the recovery value.

* **recovery**: How much water is recovered by each unit process (%)

* **reference**: The source of the recovery data

..  raw:: pdf

    PageBreak