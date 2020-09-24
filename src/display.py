from pylab import *

import shutil
import sys
import os.path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import write_dot, graphviz_layout


def treatment_train_graph(G, with_recycle=False):

    if with_recycle == False:
        pos = graphviz_layout(G, prog="dot")
        return nx.draw(G, pos, with_labels=True, arrows=True, center=True)

    if with_recycle == True:
        pos = graphviz_layout(G, prog="dot")
        return nx.draw(
            G,
            pos,
            with_labels=True,
            arrows=True,
            connectionstyle="arc3, rad = 0.2",
            center=True,
        )


def show_train1(G):

    import shutil
    import sys
    import os.path
    import pandas as pd
    import numpy as np

    import matplotlib.pyplot as plt
    from scipy.optimize import fsolve
    from scipy.optimize import minimize
    import itertools
    import pyomo.environ as env
    import ast

    import networkx as nx
    from networkx.drawing.nx_agraph import write_dot, graphviz_layout
    from pyvis import network as net

    import watertap as wt

    from pyvis.network import Network
    import pyvis
    import networkx as nx

    g = net.Network("500px", "100%", notebook=True, directed=True, heading="")
    # g.show_buttons()
    g.from_nx(G)
    g.set_options(
        """
    var options = {
      "nodes": {
        "font": {
          "size": 38
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
          "levelSeparation": 400,
          "nodeSpacing": 50,
          "direction": "LR",
          "sortMethod": "directed"
        }
      },
      "interaction": {
        "navigationButtons": true
      },
      "physics": {
        "hierarchicalRepulsion": {
          "centralGravity": 0
        },
        "minVelocity": 0.75,
        "solver": "hierarchicalRepulsion"
      }
    }
        """
    )
    # g.show(str(train_to_show))
    return g.show("example.html")


def show_train(G):

    import shutil
    import sys
    import os.path
    import pandas as pd
    import numpy as np

    import matplotlib.pyplot as plt
    from scipy.optimize import fsolve
    from scipy.optimize import minimize
    import itertools
    import pyomo.environ as env
    import ast

    import networkx as nx
    from networkx.drawing.nx_agraph import write_dot, graphviz_layout
    from pyvis import network as net

    import watertap as wt

    from pyvis.network import Network
    import pyvis
    import networkx as nx

    g = net.Network("500px", "100%", notebook=True, directed=True, heading="")
    # g.show_buttons()
    g.from_nx(G)
    g.set_options(
        """
    var options = {
      "nodes": {
        "borderWidth": 2,
        "font": {
          "background": "rgba(255,255,255,1)"
        },
        "physics": false
      },
      "edges": {
        "color": {
          "inherit": true
        },
        "physics": false,
        "selfReferenceSize": 38,
        "smooth": {
          "type": "continuous",
          "forceDirection": "none"
        },
        "width": 2
      },
      "layout": {
        "hierarchical": {
          "enabled": true,
          "nodeSpacing": 150,
          "treeSpacing": 20,
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
    # g.show(str(train_to_show))
    return g.show("example.html")


def show_train2(G):

    import shutil
    import sys
    import os.path
    import pandas as pd
    import numpy as np

    import matplotlib.pyplot as plt
    from scipy.optimize import fsolve
    from scipy.optimize import minimize
    import itertools
    import pyomo.environ as env
    import ast

    import networkx as nx
    from networkx.drawing.nx_agraph import write_dot, graphviz_layout
    from pyvis import network as net

    import watertap as wt

    from pyvis.network import Network
    import pyvis
    import networkx as nx

    g = net.Network("500px", "100%", notebook=True, directed=True, heading="")
    # g.show_buttons()
    g.from_nx(G)
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
          "centralGravity": 0
        },
        "minVelocity": 0.75,
        "solver": "hierarchicalRepulsion"
      }
    }
    """
    )
    # g.show(str(train_to_show))
    return g.show("example.html")


def main():
    print("importing something")
    # need to define anything here?


if __name__ == "__main__":
    main()
