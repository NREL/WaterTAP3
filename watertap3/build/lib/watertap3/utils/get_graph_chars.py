import pandas as pd

__all__ = ['get_unit_process_name_list',
           'get_unit_process_name_list_for_set_up',
           'get_all_none_source_end_nodes',
           'get_link_list',
           'get_link_df',
           'get_source_nodes',
           'get_outflow_links',
           'get_inflow_links',
           'get_recovered_water_nodes']

def get_unit_process_name_list(G):
    unit_process_name_list = []
    for edge in G.edges():
        if G.edges[edge]["type"] == "treatment_process":
            unit_process_name_list.append(G.edges[edge]["name"])

    if len(unit_process_name_list) == 0:
        print("error: unit_process_name_list is empty")

    return unit_process_name_list


def get_unit_process_name_list_for_set_up(G):

    unit_process_name_list = []
    for edge in G.edges():
        if G.edges[edge]["type"] == "treatment_process":
            unit_process_name_list.append(G.edges[edge]["treatment_name"])

    if len(unit_process_name_list) == 0:
        print("error: unit_process_name_list is empty")

    return unit_process_name_list


def get_all_none_source_end_nodes(G):
    node_list = []
    for node in G.nodes():
        if (len(G.in_edges(node)) >= 1) & (len(G.out_edges(node)) >= 1):
            node_list.append(node)

    return node_list


def get_link_list(G):
    link_list = []
    for edge in G.edges():
        link_list.append(G.edges[edge]["name"])

    return link_list


def get_link_df(G):
    df = pd.DataFrame.from_dict(G.edges(data=True))
    link_name = []
    link_type = []

    for row in range(0, len(df)):
        link_name.append(df[2][row]["name"])
        link_type.append(df[2][row]["type"])

    df["name"] = link_name
    df["type"] = link_type
    df = df.set_index(df.name)

    return df


def get_source_nodes(
    G,
):  # need to diffrentiate source nodes in some way if there are multiple source nodes.
    source_node_list = []
    for node in G.nodes():
        if G.nodes[node]["type"] == "source":
            if node not in source_node_list:
                source_node_list.append(node)

    return source_node_list


def get_outflow_links(G, unit_process_name_list):
    outflow_links = []
    for up in unit_process_name_list:
        for out_link in G.out_edges(up):
            outflow_links.append(G.edges[out_link]["name"])
    return outflow_links


def get_inflow_links(G, unit_process_name_list):
    inflow_links = []
    for up in unit_process_name_list:
        for in_link in G.in_edges(up):
            inflow_links.append(G.edges[in_link]["name"])
    return inflow_links


def get_recovered_water_nodes(G):
    enduse_node_list = []
    for node in G.nodes():
        if G.nodes[node]["type"] == "use":
            if node not in enduse_node_list:
                enduse_node_list.append(node)

    return enduse_node_list


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
