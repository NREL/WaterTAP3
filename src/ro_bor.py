import math
import pandas as pd

# Flow Rate Input Page (sheet b)

TDS_feed = 500  # mg/L
TSS_feed = 22  # mg/L
TDS_target = 50  # mg/L
recovery_factor = 0.85
feed_T = 20  # deg. C
blending = "Y"  # Y or N

# Operating time
op_time_factor = 0.9

# Membrane Life (sheet f)
rejection_intrinsic = 0.996  # T16
rejection_obs = 0.995592074544  # T17, from BOR Rejection sheet, last iteration in iteration table, test solution
rejection_apparent = 0.995592074544  # T18, site concentration

# Transfer Pumps (to HPP) (sheet f)
transfer_pumps = "Y"
transfer_pumps_style = "CSS"  # CSS or VST
transfer_pumps_number = 20
transfer_pumps_height_diff = 2  # m
transfer_pumps_motor_eff = 0.94
transfer_pumps_pump_eff = 0.75
transfer_pumps_coupling_eff = 1
transfer_pumps_pressure_diff = 310  # kPa

# High Pressure Feed Pumps and Energy Recovery (sheet f)
HPP_height_diff = 4  # m. From pump to top of skid
HPP_motor_eff = 0.954
HPP_pump_eff = 0.90
HPP_coupling_eff = 1
HPP_number = 21
HPP_style = "PD"  # PD, VST, or CSS
ERG_eff = 0  # efficiency of the energy recovery device - it reduces the size of the high pressure pump
ERG = "N"  # for seawater

# Product Water Pump (sheet f)
product_pumps = "Y"
product_pumps_style = "CSS"  # CSS or VST
product_pumps_number = 20
product_pumps_height_diff = 2  # m
product_pumps_motor_eff = 0.94
product_pumps_pump_eff = 0.75
product_pumps_coupling_eff = 1
product_pumps_pressure_diff = 310  # kPa

# Membrane Manufacturer Specs (sheet f)
elements_per_vessel = 7
generator_MW = 0.7
max_vessels_per_skid = 60
skids_input = 1
NaCl_diss_const = 0.99

# Building Area (sheet f)
building_area = 109.34  # m^2
admin_area = 100  # m^2
odor_control = "Y"  # Y/N

# Cost Index (sheet d)
cost_rate_steel = 1.428066  # $/CWT
cost_rate_building = 1.441803
cost_rate_construction = 1.456335
cost_rate_piping = 1.188393
cost_rate_wage = 0.912661
cost_rate_labor = 1.298942

# Direct Capital Costs (sheet g) in $
mem_cost_per_module = 500
mem_cost_per_vessel = 5000
building_cost_per_m2 = 1076.40
electrical_cost_per_L = 0.977
instrument_base_cost = 65000  # add $300,000 for top of the line DAC
odor_base_cost = 50000
process_piping_base_cost = 55000
yard_piping_base_cost = 50000
filters_base_cost = 15000
mem_cleaning_base_cost = 67000
contractor_base_cost = 100000
concentrate_cost_per_L = 0.013
sitework_cost_per_m3 = 14.53

# Indirect Capital Costs (sheet g)
interest_during_construction_percent = 0.05
contingencies_percent = 0.05976
fees_percent = 0.1195
working_capital_percent = 0.04

# Read in the csv that lists the constituent and their mg/L, molecular weight, and moles/L
df = pd.read_csv("data/bor_constituents.csv", index_col=False)

mem_char_list = [
    "mem_area_per_module",
    "mem_operating_pressure",
    "mem_diameter",
    "mem_temp",
    "mem_rejection_chloride",
    "mem_rejection_sulfate",
    "mem_recovery_rate",
    "mem_TDS",
    "mem_avg_MW_of_TDS",
    "mem_productivity",
]


def get_membrane_details(mem_manu, mem_model_type):

    df = pd.read_csv("data/membrane_options.csv")
    a_list = []
    i = 0

    df = df[((df.manufacturer == mem_manu) & (df.model == mem_model_type))]
    df = df.set_index(df.characteristic)
    for char_name in mem_char_list:

        a_list.append(df.loc[char_name].value)

        i = i + 1

    return a_list


def total_up_cost(
    m=None,
    G=None,
    flow_in=0,
    cost_method="wt",
    mem_manu=None,
    mem_model_type=None,
    up_edge=None,
):

    print("Membrane:", mem_manu, "---", mem_model_type)
    a_list = get_membrane_details(mem_manu, mem_model_type)
    # a_list = [37, 1550, 20.32, 25, 99.5, 99.8, 10, 1500, 58.40, 23]

    area_per_module = a_list[0]  # m^2 ****
    mem_operating_pressure = a_list[1]  # kPa ****
    mem_diameter = a_list[2]  # ****
    mem_temp = a_list[3]  # deg. C #****
    mem_rejection_chloride = a_list[4] / 100  # ****
    mem_rejection_sulfate = a_list[5] / 100  # ****
    mem_recovery_rate = a_list[6] / 100  # ****
    mem_TDS = a_list[7]  # mg/L ****
    mem_avg_MW_of_TDS = a_list[8]  # mg/mmole NaCl ****
    mem_productivity = a_list[9] * 1000  # L/day ****

    feed_flow_rate = (
        flow_in * 0.0115741
    )  # module calcs below need to be in liters per second. this is m3/d -> l/s

    # TDS_feed = G.nodes['source']['TDS'] #(feed_flow_rate / G.nodes['source']['Flow']) * G.nodes['source']['TDS']
    # import watertap as wt
    # tdslink_variable = wt.get_model_chars.get_link_variable(m, variable = 'TDS')
    # TDS_feed = tdslink_variable[G.edges[up_edge]['name']]
    # TDS_product = tds_treatment_equation(m, G, TDS_feed, up_edge)

    # something with membrane - concentration and pressure - TODO
    mem_conc_salt_in_feed = mem_TDS / mem_avg_MW_of_TDS  # mol/m^3
    mem_conc_salt_in_product = mem_conc_salt_in_feed * (
        1 - mem_rejection_chloride
    )  # mol/m^3
    mem_conc_salt_in_reject = (
        mem_conc_salt_in_feed - mem_conc_salt_in_product * mem_recovery_rate
    ) / (
        1 - mem_recovery_rate
    )  # mol/m^3
    mem_conc_bulk = (mem_conc_salt_in_feed + mem_conc_salt_in_reject) / 2

    mem_osmotic_pressure = (
        NaCl_diss_const
        * 2
        * 8.314
        * (273.15 + mem_temp)
        * (mem_conc_bulk - mem_conc_salt_in_product)
        * (1 - rejection_obs)
        / ((1 - rejection_intrinsic) * 1000)
    )  # kPa
    net_driving_pressure = mem_operating_pressure - mem_osmotic_pressure

    # Feedwater Analysis (sheet e) moles/L
    constit_list = df.mg_per_L
    total_constit_weight = sum((constit_list[0:30]))  # mg/L
    constit_list_moles = df.moles_per_L
    total_constit_moles = sum(constit_list_moles)  # moles/L

    avg_molecular_weight = total_constit_weight / (total_constit_moles * 1000)

    # Production values
    plant_production_flow = feed_flow_rate * recovery_factor  # L/s
    TDS_product = TDS_feed * (1 - mem_rejection_chloride) / recovery_factor  # mg/L

    # Concentrations (mole/m^3)
    conc_salt_in_feed = TDS_feed / avg_molecular_weight  # mole/m^3
    conc_salt_in_product = conc_salt_in_feed * (1 - rejection_apparent)  # mole/m^3
    conc_salt_in_reject = (
        conc_salt_in_feed - conc_salt_in_product * recovery_factor
    ) / (
        1 - recovery_factor
    )  # mole/m^3
    conc_bulk = (conc_salt_in_feed + conc_salt_in_reject) / 2  # mole/m^3

    # Operating Pressure (sheet f)
    T_coeff = 1.023 ** (feed_T - 25)
    osmotic_pressure = (
        mem_rejection_chloride
        * 8.314
        * (273.15 + feed_T)
        * (conc_bulk - conc_salt_in_product)
        * (1 - rejection_apparent)
        / ((1 - rejection_intrinsic) * 1000)
    )  # kPa
    applied_pressure = osmotic_pressure + net_driving_pressure  # kPa

    # Transfer pumps (to HPP) (sheet f)
    HPP_capacity = (
        feed_flow_rate / HPP_number
    )  # capacity per pump, also = flow rate per skid, L/s
    HPP_capacity_m3 = HPP_capacity / 1000
    pipe_x_area = (
        HPP_capacity_m3 / 2.5
    )  # cross sectional area m^2, (Ax=Q/v), be sure x-section is adequate for the flow (v ~ 8.2 ft/s)
    HPP_size = (
        (
            HPP_height_diff * 9.81
            + (((HPP_capacity_m3 / pipe_x_area) ** 2) / 2)
            + (applied_pressure - 206)
        )
        * (1 - ERG_eff)
        * HPP_capacity
        / (746 * HPP_motor_eff * HPP_pump_eff * HPP_coupling_eff ** -1)
    )  # hp

    # Transfer Water Pump (sheet f)
    transfer_pumps_capacity = feed_flow_rate / transfer_pumps_number  # L/s per pump
    transfer_pumps_area = transfer_pumps_capacity / (
        1000 * 2.5
    )  # m^2 pipe cross sectional area

    if transfer_pumps == "Y":
        transfer_pumps_size = (
            (
                transfer_pumps_height_diff * 9.81
                + (((transfer_pumps_capacity / 1000) / transfer_pumps_area) ** 2) / 2
                + transfer_pumps_pressure_diff
            )
            * transfer_pumps_capacity
            / (
                746
                * transfer_pumps_motor_eff
                * transfer_pumps_pump_eff
                * transfer_pumps_coupling_eff ** -1
            )
        )  # convert from watts to hp
    else:
        transfer_pumps_size = 0  # hp

    # Product Water Pump (sheet f)
    product_pumps_capacity = plant_production_flow / (
        product_pumps_number
    )  # L/s per pump
    product_pumps_area = product_pumps_capacity / (
        1000 * 2.5
    )  # m^2 pipe cross sectional area

    if product_pumps == "Y":
        product_pumps_size = (
            (
                product_pumps_height_diff * 9.81
                + (((product_pumps_capacity / 1000) / product_pumps_area) ** 2) / 2
                + product_pumps_pressure_diff
            )
            * product_pumps_capacity
            / (
                746
                * product_pumps_motor_eff
                * product_pumps_pump_eff
                * product_pumps_coupling_eff ** -1
            )
        )  # convert from watts to hp
    else:
        product_pumps_size = 0

    # Flow & Water Quality & Membrane & Unit Configuration (sheet f)
    if blending == "Y":
        blending_bypass_flow = (
            plant_production_flow
            * (TDS_target - TDS_product)
            / (TDS_feed - TDS_product)
        )  # L/s
        membrane_capacity = plant_production_flow - blending_bypass_flow  # L/s
    else:
        blending_bypass_flow = 0
        membrane_capacity = plant_production_flow  # L/s

    # Rejection (sheet bb)
    pure_water_perm = membrane_capacity / 1000  # m^3/s
    pure_water_perm_manu = mem_productivity / (1000 * 86400)  # m^3/s
    membrane_area = area_per_module * pure_water_perm / (pure_water_perm_manu)  # m^2
    transmembrane_pressure = net_driving_pressure * 1000  # Pa
    membrane_flux = (
        pure_water_perm / membrane_area
    )  # water flux per unit area of membrane
    water_transport_coeff = membrane_flux / transmembrane_pressure  # m/(s*Pa)

    # Membrane & Unit Configuration (sheet f)
    element_productivity = (
        water_transport_coeff * area_per_module * net_driving_pressure * 1000 * T_coeff
    ) * 1000  # L/s
    number_of_elements = (
        (membrane_capacity / element_productivity) / (3 * elements_per_vessel)
    ) * (
        3 * elements_per_vessel
    )  # TODO roundup
    number_of_pressure_vessels = number_of_elements / elements_per_vessel
    skids_calculated = number_of_pressure_vessels / max_vessels_per_skid  # TODO roundup

    # Direct Capital Costs
    # NF90 Membrane Treatment Plant Costs (sheet g)

    membrane_cost = mem_cost_per_module * number_of_elements  # $
    RO_skids_cost = mem_cost_per_vessel * number_of_pressure_vessels * cost_rate_steel
    building_cost = (
        building_cost_per_m2 * (building_area + admin_area) * cost_rate_building
    )
    electrical_cost = (
        electrical_cost_per_L
        * 1000
        * membrane_capacity ** 0.65
        * cost_rate_construction
    )
    instrument_cost = (
        instrument_base_cost * skids_calculated * cost_rate_construction + 300000
    )  # $300,000 added for top of the line DAC

    # HPP cost (sheet g)
    HPP_cost = HPP_number * cost_rate_piping
    if HPP_style == "PD":
        HPP_cost = HPP_cost * 300 * HPP_size
    elif HPP_style == "VST":
        HPP_cost = HPP_cost * 85000 * HPP_size ** 0.65
    elif HPP_style == "CSS":
        HPP_cost = HPP_cost * 35000 * HPP_size ** 0.65
    else:
        HPP_cost = 0

    # ERG cost (sheet g)
    if ERG == "Y":
        if applied_pressure > 1400:
            ERG_cost = 3463.3 * feed_flow_rate ** 0.3906 * cost_rate_construction
        else:
            ERG_cost = 0
    else:
        ERG_cost = 0

    # Transfer pumps cost (sheet g)
    # transfer_pumps_style = 'CSS'
    if transfer_pumps == "Y":
        if transfer_pumps_style == "VST":
            transfer_pumps_cost = (
                transfer_pumps_number
                * cost_rate_piping
                * (85000 * (transfer_pumps_size / 100) ** 0.65)
            )
        elif transfer_pumps_style == "CSS":
            transfer_pumps_cost = (
                transfer_pumps_number
                * cost_rate_piping
                * (
                    transfer_pumps_size
                    * (0.0387 * (transfer_pumps_capacity * 0.264 * 60) + 233.86)
                )
            )
        else:
            transfer_pumps_cost = 0
    elif transfer_pumps == "N":
        transfer_pumps_cost = 0

    # Product pumps cost (sheet g)
    if product_pumps == "Y":
        if product_pumps_style == "VST":
            product_pumps_cost = (
                product_pumps_number
                * cost_rate_piping
                * (85000 * (product_pumps_size / 100) ** 0.65)
            )
        elif transfer_pumps_style == "CSS":
            product_pumps_cost = (
                product_pumps_number
                * cost_rate_piping
                * (
                    product_pumps_size
                    * (0.0387 * (product_pumps_capacity * 0.264 * 60) + 233.86)
                )
            )
        else:
            product_pumps_cost = 0
    elif product_pumps == "N":
        product_pumps_cost = 0

    # Odor control cost (sheet g)
    if odor_control == "Y":
        odor_cost = (
            odor_base_cost
            * ((feed_flow_rate * recovery_factor * 0.0228) ** 0.75)
            * cost_rate_piping
        )
    else:
        odor_cost = 0

    # Process piping cost (sheet g)
    process_piping_cost = (
        process_piping_base_cost * feed_flow_rate * 0.0228 * cost_rate_piping
    )

    # Yard piping cost (sheet g)
    yard_piping_cost = (
        yard_piping_base_cost * (feed_flow_rate * 0.0228) ** 0.75 * cost_rate_piping
    )

    # Cartridge filters cost (sheet g)
    filters_cost = (
        filters_base_cost * (feed_flow_rate * 0.0228) ** 0.85 * cost_rate_piping
    )

    # Membrane cleaning equip. cost (sheet g)
    mem_cleaning_cost = mem_cleaning_base_cost * cost_rate_construction

    # Contractor engineering and training cost (sheet g)
    contractor_cost = contractor_base_cost * cost_rate_wage

    # Concentrate treatment and piping cost (sheet g)
    concentrate_treat_pipe_cost = (
        concentrate_cost_per_L
        * (membrane_capacity * 84600)
        * (1 - recovery_factor)
        * cost_rate_piping
    )

    # Generator cost (sheet g)
    generator_cost = (
        150000 * (generator_MW / 1000) ** 0.85 + 50000 * cost_rate_construction
    )

    # Sitework cost (sheet g)
    sitework_cost = (
        sitework_cost_per_m3 * (membrane_capacity * 84600 / 1000) * cost_rate_labor
    )

    total_direct_cap_costs = sum(
        [
            membrane_cost,
            RO_skids_cost,
            building_cost,
            electrical_cost,
            instrument_cost,
            HPP_cost,
            ERG_cost,
            transfer_pumps_cost,
            product_pumps_cost,
            odor_cost,
            process_piping_cost,
            yard_piping_cost,
            filters_cost,
            mem_cleaning_cost,
            contractor_cost,
            concentrate_treat_pipe_cost,
            generator_cost,
            sitework_cost,
        ]
    )

    # Indirect Capital Costs
    interest_during_construction = (
        interest_during_construction_percent * total_direct_cap_costs
    )
    contingencies = contingencies_percent * total_direct_cap_costs
    fees = fees_percent * total_direct_cap_costs
    working_capital = working_capital_percent * total_direct_cap_costs

    total_indirect_cap_costs = sum(
        [interest_during_construction, contingencies, fees, working_capital]
    )

    # Total Production cost ($/Lpd)
    # cost per liters per day capacity
    construction_cost = sum([total_direct_cap_costs, total_indirect_cap_costs])
    production_cost_Lpd = construction_cost / (plant_production_flow * 84600)

    # Energy required by RO/NF system, kWh
    transfer_pumps_energy = (
        transfer_pumps_number * 0.746 * 8760 * op_time_factor * transfer_pumps_size
    )  # kWh
    HPP_pumps_energy = HPP_number * 0.746 * 8760 * op_time_factor * HPP_size  # kWh
    product_pumps_energy = (
        product_pumps_number * 0.746 * 8760 * op_time_factor * product_pumps_size
    )  # kWh
    total_energy_required = sum(
        [transfer_pumps_energy, HPP_pumps_energy, product_pumps_energy]
    )

    # Average water quality of the product water, average mg/L
    TDS_product = TDS_feed * (1 - mem_rejection_chloride) / recovery_factor  # mg/L

    total_up_cost = construction_cost / 1000000  # to millions

    # if variable_out == 'TDS': return TDS_product

    return total_up_cost


# Print Results
# print('Total Direct Capital Costs: $' + str(round(total_direct_cap_costs,2)))
# print('Total Indirect Capital Costs: $' + str(round(total_indirect_cap_costs,2)))
# print('Total Production Cost: ' + str(round(production_cost_Lpd,2)) + ' $/Lpd')
# print('Total Energy Required: ' + str(round(total_energy_required,2)) + ' kWh')
# print('Average Product Quality: ' + str(round(TDS_product,2)) + ' mg/L')


#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
# Perfomance Parameter Values for Process: Constituent removals.
toc_removal = 0.0  # Asano et al (2007)
nitrate_removal = 0.0  # None but in Excel tool appears to be removed sometimes?
TOrC_removal = 0.0  # slightly lower removal than for UF. Some removal is expected due to particle association of TOrCs.
EEQ_removal = 0.0  # Linden et al., 2012 (based on limited data))


def flow_treatment_equation(m, G, link_variable):
    return link_variable * recovery_factor


def toc_treatment_equation(m, G, link_variable):
    return link_variable * (1 - toc_removal)


def nitrate_treatment_equation(m, G, link_variable):
    return link_variable * (1 - nitrate_removal)


def eeq_treatment_equation(m, G, link_variable):
    return link_variable * (1 - EEQ_removal)


def torc_treatment_equation(m, G, link_variable):
    return link_variable * (1 - TOrC_removal)


#########################################################################
#########################################################################


def tds_treatment_equation(m, G, link_variable_wname, up_edge):

    mem_model_type = G.edges[up_edge]["mem_model_type"]
    mem_manu = G.edges[up_edge]["mem_manu"]

    a_list = get_membrane_details(mem_manu, mem_model_type)
    # print('Membrane:', mem_manu, '---', mem_model_type)

    area_per_module = a_list[0]  # m^2 ****
    mem_operating_pressure = a_list[1]  # kPa ****
    mem_diameter = a_list[2]  # ****
    mem_temp = a_list[3]  # deg. C #****
    mem_rejection_chloride = a_list[4] / 100  # ****
    mem_rejection_sulfate = a_list[5] / 100  # ****
    mem_recovery_rate = a_list[6] / 100  # ****
    mem_TDS = a_list[7]  # mg/L ****
    mem_avg_MW_of_TDS = a_list[8]  # mg/mmole NaCl ****
    mem_productivity = a_list[9] * 1000  # L/day ****

    return link_variable_wname * (1 - mem_rejection_chloride) / recovery_factor  # mg/L


#########################################################################
#########################################################################
################# UP CONSTITUENT CALCULATIONS ###########################
#########################################################################
#########################################################################


#### ADDING ATTRIBUTES ---> NEEDS TO BE ONE ENTIRE FUNCTION WITH SUB FUNCTIONS #####

BOD_constraint = 250
TOC_constraint = 150


def get_edge_info(unit_process_name):
    start_node = "%s_start" % unit_process_name
    end_node = "%s_end" % unit_process_name
    edge = (start_node, end_node)
    return start_node, end_node, edge


def add_recovery_attribute(G, unit_process, unit_process_name):

    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]["recovery_factor"] = recovery_factor

    return G


def add_BOD_inlet_constraint(G, unit_process, unit_process_name):
    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]["BOD_constraint"] = BOD_constraint
    return G


def add_TOC_inlet_constraint(G, unit_process, unit_process_name):
    start_node, end_node, edge = get_edge_info(unit_process_name)
    G.edges[edge]["TOC_constraint"] = TOC_constraint
    return G


def add_recycle_and_waste_attribute(
    G, unit_process, unit_process_name, recyle_fraction_of_waste=None
):

    start_node, end_node, edge = get_edge_info(unit_process_name)
    if recovery_factor == 1:
        recyle_fraction_of_waste = 0

    if recyle_fraction_of_waste is None:
        G.edges[edge]["recycle_factor"] = 0
        G.edges[edge]["waste_factor"] = 1 - recovery_factor
    else:
        G.edges[edge]["recycle_factor"] = (1 - recovery_factor) * (
            recyle_fraction_of_waste
        )
        G.edges[edge]["waste_factor"] = (
            1 - recovery_factor - G.edges[edge]["recycle_factor"]
        )

    return G


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
