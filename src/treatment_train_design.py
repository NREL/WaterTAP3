import numpy as np
import pandas as pd
import datetime
import time
import matplotlib.pyplot as plt
from multiprocessing import Pool
import multiprocessing
import os, sys
import networkx as nx

#### TREATMENT TRAIN DESIGN #### SOME OF THESE FUNCTIONS SHOULD BE MOVED TO ANOTHER MODULE
import watertap as wt
from src import get_graph_chars

unit_process_library_list = unit_process_library_list = [
    "chlorination_twb",
    "media_filtration_twb",
    "microfiltration_twb",
    "ultrafiltration_twb",
    "nanofiltration_twb",
    "ro_twb",
    "uv_twb",
    "ro_bor",
    "uvozone_twb",
    "mbr",
]

### DESCRIBE todo
# MOVE THE BELOW SO THAT IT CAN BE CALLED FROM NOTEBOOK
def create_train(
    unit_process_name_list,
    # unit_process = False,
    from_process_lib=True,
    unit_process_case_study=False,
    source_water_reference=None,
    source_water_type=None,
    source_water_case_study=None,
    enduse_water_reference=None,
    enduse_water_type=None,
    enduse_water_case_study=None,
    flow=0,
    mem_manu=None,
    mem_model_type=None,
):

    G = nx.DiGraph(directed=True)
    # G = nx.MultiDiGraph()

    G = add_multiple_unit_processes(
        G,
        unit_process_name_list=unit_process_name_list,
        # unit_process,
        from_process_lib=from_process_lib,
        source_water_reference=source_water_reference,
        source_water_type=source_water_type,
        source_water_case_study=source_water_case_study,
        enduse_water_reference=enduse_water_reference,
        enduse_water_type=enduse_water_type,
        enduse_water_case_study=enduse_water_case_study,
        mem_manu=mem_manu,
        mem_model_type=mem_model_type,
    )

    G = add_flows(G, flow)

    return G


def add_flows(G, flow, source_nodes=None):

    if source_nodes is None:
        source_nodes = get_graph_chars.get_source_nodes(G)

    for node in source_nodes:
        G.nodes[node]["Flow"] = flow

    return G


def add_recycle_stream(
    G,
    unit_process_name=None,
    unit_process=None,
    recyle_fraction_of_waste=None,
    number_of_affected_streams=1,
    affected_stream=None,
):

    if unit_process is None:
        print("potential input error: unit_process not defined")
        unit_process = unit_process_name

    if recyle_fraction_of_waste is not None:

        recycle_node_name = unit_process_name + "_source_and_recycle"

        G.remove_edge(("%s_start" % unit_process_name), ("%s_end" % unit_process_name))
        mapping = {("%s_start" % unit_process_name): recycle_node_name}
        G = nx.relabel_nodes(G, mapping, copy=False)

        recycle_to_start_edge = (
            recycle_node_name,
            ("%s_start" % unit_process_name),
            {
                "name": ("%s_source_and_recycle_stream" % unit_process_name),
                "type": "source_and_recycle_stream",
            },
        )

        treatment_edge = (
            ("%s_start" % unit_process_name),
            ("%s_end" % unit_process_name),
            {
                "name": unit_process_name,
                "type": "treatment_process",
                "treatment_name": unit_process,
            },
        )

        end_to_recycle_edge = (
            ("%s_end" % unit_process_name),
            recycle_node_name,
            {
                "name": ("%s_recycle_stream" % unit_process_name),
                "type": "recycle_stream",
            },
        )

        G.add_edges_from([recycle_to_start_edge, treatment_edge, end_to_recycle_edge])

        G = name_nodes(G)

        G = update_unit_process_recycle(
            G, unit_process, unit_process_name, recyle_fraction_of_waste
        )

    return G


def add_multiple_unit_processes(
    G,
    unit_process_name_list=None,  # change this to None?
    unit_process_list=None,
    from_process_lib=True,  # redundant with below
    unit_process_case_study=False,  # this gives you a specific microfiltration case study
    source_water_reference=None,
    source_water_type=None,
    source_water_case_study=None,
    enduse_water_reference=None,
    enduse_water_type=None,
    enduse_water_case_study=None,
    source_node_name="source",
    end_node_name="use",
    mem_manu=None,
    mem_model_type=None,
):

    if unit_process_list == None:
        unit_process_list = unit_process_name_list

    # ADD THE UNIT PROCESSES AND LINKS
    for unit_process, unit_process_name in zip(
        unit_process_list, unit_process_name_list
    ):

        print(
            "adding unit process to network:", unit_process_name
        )  # turn this to if statement

        if unit_process == unit_process_name:
            n = 1
            while ("%s_start" % unit_process_name) in G.nodes():
                unit_process_name = "%s%s" % (unit_process_name, n)
                n = n + 1

        end_node_name = "use"
        source_node_name = "source"

        # ADD THE UNIT PROCESSES AND LINKS
        source_edge = (
            source_node_name,
            ("%s_start" % unit_process_name),
            {"name": ("%s_feedwater" % unit_process_name), "type": "feedwater_stream"},
        )

        treatment_edge = (
            ("%s_start" % unit_process_name),
            ("%s_end" % unit_process_name),
            {
                "name": unit_process_name,
                "type": "treatment_process",
                "treatment_name": unit_process,
                "mem_manu": mem_manu,
                "mem_model_type": mem_model_type,
            },
        )

        waste_edge = (
            ("%s_end" % unit_process_name),
            ("%s_waste" % unit_process_name),
            {"name": ("%s_waste_stream" % unit_process_name), "type": "waste_stream"},
        )

        product_edge = (
            ("%s_end" % unit_process_name),
            end_node_name,
            {"name": ("%s_use_stream" % unit_process_name), "type": "use_stream"},
        )

        G.add_edges_from([source_edge, treatment_edge, waste_edge, product_edge])

    # NAME THE NODES
    G = name_nodes(G)

    # GET INFORMATION ON UNIT PROCESSES FROM UP MODELS
    # if from_process_lib is not None:
    #    G = set_up_unit_process(G)

    # add option to import for existing list if from_process_lib is true -> NOT SURE THIS IS NEEDED. ALREADY DOES IT?
    # should the below also be 'from_process_lib'?
    if source_water_reference is not None:
        G = get_source_data(
            G,
            source_water_reference,
            source_water_type,
            source_water_case_study,
            source_node_name,
        )

    if enduse_water_reference is not None:
        G = get_enduse_data(
            G,
            enduse_water_reference,
            enduse_water_type,
            enduse_water_case_study,
            end_node_name,
        )

    return G


def get_source_data(
    G,
    source_water_reference,
    source_water_type,
    source_water_case_study,
    source_node_name=None,
):  # need to do this to allow multiple at a time.

    #### READ IN SOURCE DATA
    df_source = pd.read_csv("data/case_study_water_sources_and_uses.csv")

    if source_water_reference is not None:
        df_source = df_source[df_source.Reference == source_water_reference]

    if source_water_type is not None:
        df_source = df_source[df_source.WaterType == source_water_type]

    if source_water_case_study is not None:
        df_source = df_source[df_source.CaseStudy == source_water_case_study]

    # ADD INFORMATION TO NODES
    for variable in df_source.Variable:
        G.nodes[source_node_name][variable] = (
            df_source[df_source.Variable == variable].mean().max()
        )

    return G


def get_enduse_data(
    G,
    enduse_water_reference,
    enduse_water_type,
    enduse_water_case_study,
    enduse_node_name=None,
):

    #### READ IN END USE DATA
    df_enduse = pd.read_csv("data/case_study_water_sources_and_uses.csv")

    if enduse_water_reference is not None:
        df_enduse = df_enduse[df_enduse.Reference == enduse_water_reference]

    if enduse_water_type is not None:
        df_enduse = df_enduse[df_enduse.WaterType == enduse_water_type]

    if enduse_water_case_study is not None:
        df_enduse = df_enduse[df_enduse.CaseStudy == enduse_water_case_study]

    # ADD INFORMATION TO NODES
    # right now it's mean of potential range, but the user should be able to select
    # TO DO: END NODE TO BE REPLACED WITH SOMETHING ELSE?!
    for variable in df_enduse.Variable:
        G.nodes[enduse_node_name][variable] = (
            df_enduse[df_enduse.Variable == variable].mean().max()
        )

    return G


def name_nodes(G):

    for node in G.nodes():
        G.nodes[node]["name"] = node
        G.nodes[node]["type"] = "TODO"

        node_label = node

        if (len(G.in_edges(node)) >= 1) & (len(G.out_edges(node)) == 0):  # end node
            node_label = node.split("_")[-1]
            G.nodes[node]["type"] = node_label

            for edge in G.in_edges(node):
                if "use" in G.edges[edge]["type"]:
                    G.nodes[node]["type"] = "use"

        if (len(G.in_edges(node)) == 0) & (len(G.out_edges(node)) >= 1):  # start node
            node_label = node.split("_")[-1]
            G.nodes[node]["type"] = "source"

        # mapping = {('%s' % node): node_label}
        # G = nx.relabel_nodes(G, mapping, copy=False)

    return G


# THIS UPDATES FEEDWATER DATA WITH ANOTHER SOURCE (SINGLE)-> LIKELY A PROBLEM WHEN DOING MULTIPLE -> SHOULD BE EASY FIX
# THIS SHOULD UPDATE THE GRAPH NOT THE DATAFRAME! DELELTE?!?!?!?!?!?!!?
def update_feedwater_data(
    df,
    number_of_additional_sources=None,
    source_to_node_names=None,
    constituents="dummy_name",
    from_case_study=True,
    flows=None,
):

    for n in range(
        0, number_of_additional_sources
    ):  # need to test adding more than one at a time
        feedwater_data_new = pd.DataFrame()
        feedwater_data_new = df.copy(deep=True)
        feedwater_data_new.Value = np.array(0)
        feedwater_data_new.feedwater = np.array(0)
        feedwater_data_new.SourceNodeName = np.array(source_to_node_names[n][0])

        if from_case_study == True:
            feedwater_data_new.Value = feedwater_data_new.Variable.map(
                df.Value
            )  # CHANGE THIS FEEEDWATER WITH AN ATUAL CASE STUDY NAME OR WAY TO LOOKUP
            feedwater_data_new.feedwater = feedwater_data_new.Value
            feedwater_data_new["Value"]["Flow"] = flows[n][0]
            feedwater_data_new["feedwater"]["Flow"] = flows[n][0]
            feedwater_data_new.ExampleReference = np.array(constituents)

        df = pd.concat([df, feedwater_data_new])

    return df


def add_multiple_water_sources(
    G,
    source_water_reference=None,
    source_water_type=None,
    source_water_case_study=None,
    number_of_additional_sources=1,
    source_to_node_names=None,  # ALLOW FOR MULTIPLE?
    flow=[],
    source_node_name=None,
):

    if source_node_name is None:
        for n in range(1, 100):  # will crap out after 99.
            source_node_name = "source_node_%s" % n
            if source_node_name not in G.nodes():
                source_name = source_node_name
                source_node_name = None
                break

    for source_name, to_node in source_to_node_names:
        print("adding another water source:", source_name)  # turn this to if statement

        G.add_edges_from(
            [
                (
                    source_name,
                    to_node,
                    {
                        "name": ("%s_%s_feedwater" % (source_name, to_node)),
                        "type": "feedwater_stream",
                    },
                )
            ]
        )

    G = name_nodes(G)

    G = get_source_data(
        G,
        source_water_reference,
        source_water_type,
        source_water_case_study,
        source_node_name=source_name,
    )

    G = add_flows(G, flow, source_nodes=[source_name])

    return G


def add_multiple_water_enduses(
    G,
    enduse_water_reference=None,
    enduse_water_type=None,
    enduse_water_case_study=None,
    number_of_additional_ends=1,
    node_to_end_names=None,  # ALLOW FOR MULTIPLE?
    min_flow=[],
    end_node_name=None,
):

    if end_node_name is None:
        for n in range(1, 100):  # will crap out after 99.
            end_node_name = "source_node_%s" % n
            if end_node_name not in G.nodes():
                end_name = end_node_name
                end_node_name = None
                break

    for from_node, end_name in node_to_end_names:
        print("adding another water use:", end_name)  # turn this to if statement

        G.add_edges_from(
            [
                (
                    from_node,
                    end_name,
                    {
                        "name": ("%s_treated_%s_stream" % (from_node, end_name)),
                        "type": "use_stream",
                    },
                )
            ]
        )

    G = name_nodes(G)

    G = get_enduse_data(
        G,
        enduse_water_reference,
        enduse_water_type,
        enduse_water_case_study,
        enduse_node_name=end_name,
    )

    G.nodes[end_name]["min_flow"] = min_flow

    # G = add_flows(G, flow, source_nodes = [source_name])

    return G


def add_unit_process(
    G,
    from_node=None,
    to_node=None,
    unit_process_name_list=None,
    unit_process_list=None,
    adjust_end_use=True,
    adjust_source=True,
    order=None,
    mem_manu=None,
    mem_model_type=None,
):

    if order is None:
        print("check inputs: order not set. assuming series.")
        order = "series"

    if unit_process_list == None:
        unit_process_list == unit_process_name_list
    # ADD THE UNIT PROCESSES AND LINKS

    for unit_process, unit_process_name in zip(
        unit_process_list, unit_process_name_list
    ):

        print(
            "adding unit process to network:", unit_process_name
        )  # turn this to if statement

        if unit_process == unit_process_name:
            n = 1
            while ("%s_start" % unit_process_name) in G.nodes():
                unit_process_name = "%s%s" % (unit_process, n)
                n = n + 1

        if order == "series":
            if from_node is not None:
                end_use_node_name = from_node
                n = 1
                while end_use_node_name in G.nodes():
                    end_use_node_name = "%s%s" % (end_use_node_name, n)
                    n = n + 1

            if to_node is not None:
                from_node = to_node
                end_use_node_name = to_node
                n = 1
                while from_node in G.nodes():
                    from_node = "%s%s" % (from_node, n)
                    n = n + 1

        if order == "parallel":
            end_use_node_name = to_node
            from_node = from_node

        source_edge = (
            from_node,
            ("%s_start" % unit_process_name),
            {"name": ("%s_feedwater" % unit_process_name), "type": "feedwater_stream"},
        )

        treatment_edge = (
            ("%s_start" % unit_process_name),
            ("%s_end" % unit_process_name),
            {
                "name": unit_process_name,
                "type": "treatment_process",
                "treatment_name": unit_process,
                "mem_manu": mem_manu,
                "mem_model_type": mem_model_type,
            },
        )

        waste_edge = (
            ("%s_end" % unit_process_name),
            ("%s_waste" % unit_process_name),
            {"name": ("%s_waste_stream" % unit_process_name), "type": "waste_stream"},
        )

        product_edge = (
            ("%s_end" % unit_process_name),
            end_use_node_name,
            {"name": ("%s_use_stream" % unit_process_name), "type": "use_stream"},
        )

        G.add_edges_from([source_edge, treatment_edge, waste_edge, product_edge])

        G = name_nodes(G)

        # G = set_up_unit_process(G)

        if adjust_end_use == True:
            if from_node is not None:
                for key in list(G.nodes[from_node]):
                    if key != "name":
                        if key != "type":
                            G.nodes[end_use_node_name][key] = G.nodes[from_node][key]
                            del G.nodes[from_node][key]

        if adjust_source == True:
            if to_node is not None:
                for key in list(G.nodes[to_node]):
                    if key != "name":
                        if key != "type":
                            G.nodes[from_node][key] = G.nodes[to_node][key]
                            del G.nodes[to_node][key]

    return G


def add_stream(
    G, from_node=None, to_node=None, stream_name=None, stream_type=None,
):

    if stream_name is None:
        print("input error likely: stream_name not set")

    new_edge = (from_node, to_node, {"name": stream_name, "type": stream_type})

    G.add_edges_from([new_edge])

    return G


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
