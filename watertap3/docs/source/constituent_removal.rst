Constituent Removal
=============================

``data/constituent_removal.csv``

Constituent removal `r` is represented as the fraction (between zero and one) of the mass of the
constituent being removed after it is passes through a unit process. Case-study based constituent
removal is given for certain unit processes if the case study has a unique recovery rate,
otherwise default value are used.

The constituent removal data table states how much each unit process in each treatment facility removes
a given water constituent. The model uses the information about the constituents in the source water
as well as the removal rates of each unit process given in this constituent removal table to calculate
constituent levels in the output water.

The overall mass balance for a single constituent `i` flowing into a single unit is based on
volumetric flow and constituent concentration `c`:

    .. math::

        Q_{in} c_{in,i} = Q_{out} c_{out,i} + Q_{waste} c_{waste,i}
|
Any mass removed by the unit is assumed to flow out the waste outlet. Then the constituent
removal is:

    .. math::

        Q_{in} c_{in,i} r_i = Q_{waste} c_{waste,i}
|
And therefore the mass flow out of the unit (i.e. to the next unit process) can be calculated with:

    .. math::

        Q_{out} c_{out,i} = Q_{in} c_{in,i} (1 - r_i)
|
The constituent removal input dataset is arranged into the following columns:

* **units**: The units used for the constituent, such as kg/m3 (constituent concentration)

* **calculation_type**: How the model will handle the values when the unit process changes the
  constituent level, ultraviolet transmittance, or pH.

    * *fractional_constituent_removal*: fractional removal
    * *absolute_value*: percent removal for ultraviolet transmittance
    * *delta_constituent_or_property*: when the pH is changed
|
* **unit_process**: Which unit process is removing the constituent.

* **case_study**: The treatment facility name.

* **value**: The fraction or percent of the constituent in the source water that will be removed.

* **data_source**: The source of the data values and how values were calculated.

* **constituent**: The constituent being removed as named in the model

* **scenario**: The name of the scenario that the values correspond with

* **reference**: The name of the project that is using the mode


..  raw:: pdf

    PageBreak