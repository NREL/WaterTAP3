WaterTAP3 Framework
========================

WaterTAP3 simulates a steady-state water treatment facility for given source water conditions,
process flows, and system-level technoeconomic assumptions. Capital costs, operating costs, and
unit performance are estimated for both individual treatment processes and the system as a whole.
Users can perform new analysis either by selecting a premade train from the treatment train
library or connecting any number of unit processes together in a custom configuration.

The model contains various technical and cost parameter options for several treatment technology
models and a library of influent water quality characteristics for a variety of source waters.
Users can customize water quality parameters to evaluat technology performance for their unique
conditions. The model can be used for different assessment needs, including process simulation,
optimization, uncertainty analysis, and sensitivity analysis.

Model Structure
----------------------

WaterTAP3 is implemented in Python using the `Institute for the Design of Advanced Energy Systems
(IDAES) <idaes.org>`_ which is itself based on the Python optimization and modeling package
package `Pyomo <https://pyomo.readthedocs.io/en/stable/index.html>`_. Though initially developed
for the research of innovative energy processes, at its core the IDAES framework is used to
track material and energy flows through complex systems, making it useful for tracking
water flows, chemical concentrations, and other parameters (e.g. pressure, temperature) through a
treatment train.

Every WaterTAP3 model ``m`` is instantiated as a Pyomo ``ConcreteModel()`` object upon which an
IDAES ``FlowsheetBlock()`` is placed to facilitate water and material transfers through each unit
process in the WaterTAP3 model. Each unit model in WaterTAP3 is an instance of the
``WT3UnitProcess()`` class, which has properties inherited from the IDAES ``UnitModelBlockData()``
class. Connections between unit models are represented by the IDAES ``Arc()`` class.

Much like actual treatment technologies, material and energy exchanges in WaterTAP3 are facilitated
by "ports" assigned to each unit process. Each water source and unit process is added as an
attribute to the flowsheet and by default are given one inlet port, one outlet port, and one
waste port. Additional inlet and outlet ports are added dynamically based on the input file
(``treatment_train_setup.xlsx`` - discussed in a later section). Flow and mass balance is
achieved across each unit process based on water recovery values and constituent removal factors.

..  raw:: pdf

    PageBreak