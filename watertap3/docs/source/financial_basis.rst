Financial Basis Inputs
-----------------------------------------------

The case study basis input data table contains the foundational technoeconomic assumptions for the entire treatment train.

The input dataset is arranged into the following columns:

* **case_study**:  The treatment facility name.

* **scenario**: The name of the scenario that the TEA values correspond with

* **value**:  The number or name of the variable of interest

* **reference**:  The name of the project that is using the model

* **variable**: The name of the variable of interest

    * *analysis_year*:  The first year of the plant is/was in operation

    * *location_basis*: The country or U.S. state where the plant is located. Used for assigning the
      electricity cost ($/kwh). Electricity costs are provided in the data folder.

    * *plant_life_yrs*: The initial design basis for plant-life and used for life cycle analysis
      calculations. The default plant-life is 20 years.

    * *land_cost_percent*: The assumed cost of land as a percentage of total fixed capital
      investment. This is a part of the total capital investment.

    * *working_capital_percent*: The assumed cost of working capital as a percentage of total fixed
      capital investment. This is a part of the total capital investment.

    * *salaries_percent*: The assumed cost of salaries as a percentage of total fixed capital
      investment. This is a part of the fixed operating costs.

    * *employee_benefits_percent*: The assumed cost of employee benefits as a percentage of total
      salary cost. This is a part of the fixed operating costs.

    * *maintenance_cost_percent*: The assumed cost of maintenance as a percentage of total fixed
      capital investment. This is a part of the fixed operating costs.

    * *laboratory_fees_percent*: The assumed cost of laboratory fees as a percentage of total fixed
      capital investment. This is a part of the fixed operating costs.

    * *insurance_and_taxes_percent*: The assumed cost of insurance and taxes as a percentage of
      total fixed capital investment. This is a part of the fixed operating costs.

    * *default_cap_scaling_exp*: The typical value for economy-of-scale for capital equipment.
      This is a part of the total and fixed capital investment.

    * *default_opex_scaling_exp*:  The typical value for economy-of-scale for fixed plant costs.
      This is a part of the fixed operating costs.

    * *cap_by_equity*: The percent of the capital that is financed by equity rather than debt.
      This is a part of the capital recovery factor and LCOW calculations.

    * *debt_interest_rate*: The rate for loan financing of capital. This is a part of the capital
      recovery factor and LCOW calculations.

    * *exp_return_on_equity*: The expected return, interest rate, or cost of capital associated
      with the portion of capital financed with equity.

    * *default_tpec_multiplier*: The Total Purchased Equipment Cost (TPEC) to fixed capital
      investment. This is is a part of the total and fixed capital investment calculations.

    * *default_tic_multiplier*: The Total Installed Cost (TIC) to fixed capital investment. This
      is a part of the total and fixed capital investment calculations.


..  raw:: pdf

    PageBreak