Source Water
=============================

``data/case_study_water_sources.csv``

Source water information is required to run the model. It can be selected from a list of
pre-existing case studies or entered manually using Jupyter Notebook or the input data tables in
the data folder. There is no limit on the number of source water nodes for the model and the
treatment train design section details how to connect source waters to the treatment train.
Water flow rates (volumetric) and any constituent information required to calculate a unit
process performance or cost must exist in the source water information.

The source water input dataset is arranged into the following columns:

* **units**: The units used for the constituent, such as kg/m3 (constituent concentration)

* **value**: The number of the variable of interest

* **water_type**: The type/source of the water. This is where the intake unit water_type names must match the train input water_type process parameter in the treatment train design.

* **case_study**: The treatment facility name.

* **reference**: The name of the project.

* **variable**: The name of the constituent or property of interest, such as ‘flow’ (required) or
  ‘tds’.

* **scenario**: The name of the scenario that the values correspond with, otherwise the default value will be used.


..  raw:: pdf

    PageBreak