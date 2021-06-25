WaterTAP3 Overview
========================

The Water Technoeconomic Assment Pipe-Parity Platform (WaterTAP3) was developed under the
National Alliance for Water Innovation (NAWI) to facilitate consistent technoecnomic assessments
of desalination treatment trains. It is an analytically robust modeling tool that can be used to
evaluate cost, energy, environmental, and resiliency tradeoffs of water treatment technology
across differentw ater sources, sectors, and scales.

WaterTAP3 is publicly accessible and based on open-source models and data. The model is designed
to be flexible and customizable to allow users to adapt or create new treatment trains and process
models to assess different water treatment performance criteria.

Examples of WaterTAP3 applications include:

    * Baselining the state of water treatment systems across key water-using economic sectors.
    * Road-mapping critical technology development priorities to achieve pipe parity.
    * Performing ongoing project evaluation for NAWI funded research.
    * Conducting technoeconomic and life-cycle assessments of water technologies and systems
      across the water industry (in development).


WaterTAP3 Installation
----------------------------

WaterTAP3 is still in development so is not listed in ``pip`` and must be accessed by cloning the
current GitHub repo available at https://github.com/NREL/NAWI-WaterTAP3 (**THIS URL MUST BE
CHANGED**):

#. Install the Anaconda distribution of Python

    * https://www.anaconda.com/products/individual
    * I AM NOT SURE IF THIS IS NECESSARY

#. Create new empty directory for WaterTAP3 installation

    * e.g. this might be a folder called "watertap3" on your desktop

#. Open terminal and navigate to that directory

    * e.g. ``cd ~/Desktop/watertap3``
    * You can also right-click on the folder in Finder and select "New Terminal at Folder". A
      terminal window/tab will then open with that folder as the working directory

#. Clone the repo

    * ``git clone https://github.com/NREL/NAWI-WaterTAP3``
    * All the necessary python files and data files will be downloaded into your working directory

#. Create the ``watertap3`` Python environment

    * ``conda env create --file watertap3.yml``

#. Activate the ``watertap3`` environment

    * ``conda activate watertap3``

#. Start Jupyter Notebook app or Jupyter Lab app to access tutorial notebooks and run WaterTAP3

    * For Jupyter Notebook - ``jupyer notebook``
    * For Jupyter Lab - ``jupyter lab``


WaterTAP3 Cost Estimates
----------------------------

Cost estimations are represented at the unit process level (i.e. per treatment technology in the
train) and aggregated to the system-level. Esttimated costs include:

* Capital investment
* Annual operation and maintenance

    * Fixed (labor, maintenance)
    * Variable (energy, chemical)

WaterTAP3 Outputs
----------------------------

The pipe-parity metrics from the output of a WaterTAP3 model currently include:

    * Levelized Cost of Water: cost per unit of treated water
    * Energy intensity: direct energy consumption per unit of treated water
    * Water recovery: the percentage of water recovered for a beneficial use
    * Constituent removal: the percentage of constituent mass removed from the source water

Other outputs in development inclue:

    * Extent of alternative water and energy resouces
    * Life-cycle assessment of environmental impacts (e.g. greenhouse gas emissions, total water
      intensity)
    * System resiliency and security


WaterTAP3 Impacts
-----------------------------

The objective of WaterTAP3 is to become a standard tool to evaluate water treatment system
performance across key metrics used to promote and assess pipe-parity for a range of users
including industry and academia. The results from WaterTAP3 can help identify trade-offs among
the different performance metrics and enable users to asses how particular technologies affect
pipe-parity metrics and how improvements in one metric can affect others across a range of source
water conditions and technology performance parameters.

The flexibility and comprehensive scope of WaterTAP3 make it a userful too for industry-wide
technoeconomic analyses, promoting better informed water investment decisions and technology
development. As a user-friendly, open-source platform, WaterTAP3 is not limited to only those
with scientific expertise and technical know-how. The tool can be used by policymakers, planners,
and others without extensive analytical experience through the publicly available graphical user
interface (under development).



..  raw:: pdf

    PageBreak