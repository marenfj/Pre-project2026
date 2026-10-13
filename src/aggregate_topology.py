from topology import graph, domains, border_nodes
from plotting import plot_border_paths
from calculate_paths import source, destination, path_labels, case1_primary_path, case1_backup_path
import networkx as nx
import math
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from itertools import combinations

def aggregate_domain(graph, domains, operator, border_nodes):

    # Get nodes belonging to this operator
    operator_nodes = []

    for node in graph.nodes:
        if domains[node] == operator:
            operator_nodes.append(node)

    # Internal graph of the operator
    internal_graph = graph.subgraph(operator_nodes)

    # Create aggregated graph
    aggregated = nx.Graph()

    # Add border nodes
    for node in border_nodes:
        if domains[node] == operator:
            aggregated.add_node(node)

    # Add virtual links between border nodes
    for u, v in combinations(aggregated.nodes, 2):

        try:
            path = nx.shortest_path(
                internal_graph,
                source=u,
                target=v
            )

            hop_count = len(path) - 1

            aggregated.add_edge(
                u,
                v,
                weight=hop_count
            )

        except nx.NetworkXNoPath:
            pass

    return aggregated

TA_A = aggregate_domain(
    graph, domains, "A", border_nodes
)

TA_B = aggregate_domain(
    graph, domains, "B", border_nodes
)

print("Operator A:")
print("Original nodes:", len([
    n for n in graph.nodes if domains[n] == "A"
]))
print("Aggregated nodes:", TA_A.number_of_nodes())
print("Aggregated links:", TA_A.number_of_edges())

print("Operator B:")
print("Original nodes:", len([
    n for n in graph.nodes if domains[n] == "B"
]))
print("Aggregated nodes:", TA_B.number_of_nodes())
print("Aggregated links:", TA_B.number_of_edges())


#lag en felles graf med de aggregerte domenene:
TA_graph = nx.compose(TA_A, TA_B)

for u, v in graph.edges:
    if domains[u] != domains[v]:
        TA_graph.add_edge(
            u,
            v,
            weight=1,
            virtual=False
        )

def add_terminal(graph, TA_graph, domains, terminal, border_nodes):

    operator = domains[terminal]

    operator_nodes = []

    for node in graph.nodes:
        if domains[node] == operator:
            operator_nodes.append(node)

    internal_graph = graph.subgraph(operator_nodes)

    TA_graph.add_node(terminal)

    for border in border_nodes:

        if domains[border] != operator:
            continue

        if terminal == border:
            continue

        if nx.has_path(internal_graph, terminal, border):

            path = nx.shortest_path(
                internal_graph, terminal, border
            )

            TA_graph.add_edge(
                terminal,
                border,
                weight=len(path) - 1,
                virtual=True
            )

add_terminal(graph, TA_graph, domains, source, border_nodes)
add_terminal(graph, TA_graph, domains, destination, border_nodes)

case2_abstract_primary = nx.shortest_path(
    TA_graph,
    source=source,
    target=destination,
    weight="weight"
)

print("Abstract primary path (case 2):")
print(path_labels(case2_abstract_primary))

#finner den faktiske interne ruten mellom source og destination
def expand_path(graph, domains, abstract_path):

    physical_path = [abstract_path[0]]

    for i in range(len(abstract_path) - 1):

        u = abstract_path[i]
        v = abstract_path[i + 1]

        if domains[u] != domains[v]:
            # Actual inter-domain link
            segment = [u, v]

        else:
            # Internal path in one operator's network
            operator = domains[u]

            operator_nodes = []

            for node in graph.nodes:
                if domains[node] == operator:
                    operator_nodes.append(node)

            internal_graph = graph.subgraph(operator_nodes)

            segment = nx.shortest_path(
                internal_graph, u, v
            )

        physical_path.extend(segment[1:])

    return physical_path

case2_TA_primary = expand_path(
    graph,
    domains,
    case2_abstract_primary
)

print("Physical primary path:")
print(path_labels(case2_TA_primary))

#finn en backup-path - TA-based shortest-path-first backup routing
# Copy physical graph
backup_graph = graph.copy()

# Remove primary path links
for i in range(len(case2_TA_primary) - 1):
    u = case2_TA_primary[i]
    v = case2_TA_primary[i + 1]

    backup_graph.remove_edge(u, v)

# Rebuild TA based on remaining resources
TA_A_backup = aggregate_domain(
    backup_graph, domains, "A", border_nodes
)

TA_B_backup = aggregate_domain(
    backup_graph, domains, "B", border_nodes
)

TA_backup_graph = nx.compose(
    TA_A_backup,
    TA_B_backup
)

# Add remaining inter-domain links
for u, v in backup_graph.edges:
    if domains[u] != domains[v]:
        TA_backup_graph.add_edge(
            u,
            v,
            weight=1,
            virtual=False
        )

# Add terminals
add_terminal(
    backup_graph,
    TA_backup_graph,
    domains,
    source,
    border_nodes
)

add_terminal(
    backup_graph,
    TA_backup_graph,
    domains,
    destination,
    border_nodes
)

# Compute and expand backup
try:
    case2_abstract_backup = nx.shortest_path(
        TA_backup_graph,
        source,
        destination,
        weight="weight"
    )

    case2_TA_backup = expand_path(
        backup_graph,
        domains,
        case2_abstract_backup
    )

    print("TA backup:", path_labels(case2_TA_backup))

except (nx.NetworkXNoPath, nx.NodeNotFound):
    case2_TA_backup = None
    print("No TA backup path found")




print("CASE 1: FULL TOPOLOGY")
print("Primary:", case1_primary_path)
print("Backup:", case1_backup_path)

print("\nCASE 2: TOPOLOGY AGGREGATION")
print("Primary:", case2_TA_primary)
print("Backup:", case2_TA_backup)

print("\nPATH LENGTHS")

print("Full primary:", len(case1_primary_path) - 1)
print("TA primary:", len(case2_TA_primary) - 1)

if case1_backup_path is not None:
    print("Full backup:", len(case1_backup_path) - 1)

if case2_TA_backup is not None:
    print("TA backup:", len(case2_TA_backup) - 1)


def path_edges(path):
    edges = set()

    for i in range(len(path) - 1):
        edges.add(frozenset((path[i], path[i + 1])))

    return edges


if case2_TA_backup is not None:
    shared = path_edges(case2_TA_primary) & path_edges(case2_TA_backup)
    print("TA paths link-disjoint:", len(shared) == 0)



figure = plot_border_paths(
    graph,
    domains,
    border_nodes,
    case1_primary_path,
    case1_backup_path,
    output_file="../topologies/border_path_comparison.png",
)
