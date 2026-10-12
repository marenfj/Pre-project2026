import networkx as nx
from topology import graph_modified, graph, domains, plot_topology
from pathlib import Path


possible_pairs = []

def link_disjoint_paths():

    A_nodes = []
    B_nodes = []

    for node in graph.nodes:
        if domains[node] == "A":
            A_nodes.append(node)
        else:
            B_nodes.append(node)

    for source in A_nodes:
        for destination in B_nodes:
            paths = list(
                nx.edge_disjoint_paths(
                    graph, source, destination,
                    cutoff=2
                )
            )
            if len(paths) >= 2:
                possible_pairs.append((source, destination))
                #print(source, destination)
                

    print("Pairs with at least two link-disjoint paths:", len(possible_pairs))

link_disjoint_paths()


def valid_nodepair(source, destination, pairs):
    i = 0
    for (src, dst) in pairs:
        i += 1
        if src == source and dst == destination:
            return i
        

source = 21 #"HSH Stord"
destination = 56 #"HiF Alta"

number = valid_nodepair(source, destination, possible_pairs)
if number is not None:
    print("Parets nummer i possible pairs er: ", number)
else:
    print("Dette paret finnes ikke i possible pairs")


primary_path = nx.shortest_path(
    graph,
    source = source,
    target = destination
)

backup_path = nx.shortest_path(
    graph_modified,
    source = source,
    target = destination
)

def path_labels(path):
    label_path = []
    for p in path:
        name = graph_modified.nodes[p]["label"]
        label_path.append(name)
    return label_path

# print("Primary path: ", path_labels(primary_path))
# print("Backup path: ", path_labels(backup_path))

# plot_topology(graph, output_file=Path("../topologies/path_comparison.png"), show_labels=True, primary_path=primary_path, backup_path=backup_path)
