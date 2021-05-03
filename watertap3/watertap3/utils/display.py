import json

import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
from networkx.readwrite import json_graph
from pyomo.environ import TransformationFactory
from pyomo.network import SequentialDecomposition
from pyvis import network as net

__all__ = ['treatment_train_graph',
           'show_train2']


def treatment_train_graph(G, with_recycle=False):
    if with_recycle == False:
        pos = graphviz_layout(G, prog='dot')
        return nx.draw(G, pos, with_labels=True, arrows=True, center=True)

    if with_recycle == True:
        pos = graphviz_layout(G, prog='dot')
        return nx.draw(
                G,
                pos,
                with_labels=True,
                arrows=True,
                connectionstyle='arc3, rad = 0.2',
                center=True,
                )


def show_train2(GG=None, model_name=None):
    dummy_model = model_name

    if GG == None:
        TransformationFactory('network.expand_arcs').apply_to(dummy_model)
        seq1 = SequentialDecomposition()
        GG = seq1.create_graph(dummy_model)

    # G2 = nx.Graph()
    GG2 = nx.DiGraph(directed=True)
    for edge in GG.edges():
        GG2.add_edge(edge[0].getname(), edge[1].getname())

    if 'surface_discharge' in list(GG2.nodes()):
        GG2.remove_node('surface_discharge')
        GG2.remove_node(dummy_model.fs.water_mixer_name)

    g = net.Network('500px', '100%', notebook=True, directed=True, heading='')
    # g.show_buttons()
    g.from_nx(GG2)
    g.set_options(
            """
        var options = {
          "nodes": {
            "font": {
              "size": 16,
              "background": "rgba(255,255,255,1)"
            }
          },
          "edges": {
            "color": {
              "inherit": true
            },
            "smooth": {
              "type": "continuous",
              "forceDirection": "none"
            }
          },
          "layout": {
            "hierarchical": {
              "enabled": true,
              "levelSeparation": 220,
              "nodeSpacing": 145,
              "treeSpacing": 195,
              "direction": "LR",
              "sortMethod": "directed"
            }
          },
          "interaction": {
            "navigationButtons": true
          },
          "physics": {
            "hierarchicalRepulsion": {
              "centralGravity": 1
            },
            "minVelocity": 0.75,
            "solver": "hierarchicalRepulsion"
          }
        }
        """
            )
    d = json_graph.node_link_data(GG2)
    json.dump(d, open('tmp/example.json', 'w'))  # write json

    return g.show('tmp/example.html')


def main():
    print('importing something')


if __name__ == '__main__':
    main()