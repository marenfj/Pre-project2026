from topology import graph, domains, border_nodes
from plotting import plot_border_paths, plot_topology
from calculate_paths import source, destination, path_labels, case1_primary_path, case1_backup_path
import networkx as nx
import math
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from itertools import combinations
from pathlib import Path

def aggregate_domain(graph, domains, operator, border_nodes, information_level="weighted"):

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

            if information_level == "weighted":
                weight = hop_count
            elif information_level == "reachability":
                weight = 1

            aggregated.add_edge(
                u,
                v,
                weight=weight
            )

        except nx.NetworkXNoPath:
            pass

    return aggregated

TA_A = aggregate_domain(
    graph, domains, "A", border_nodes, information_level="weighted"
)
TA_B = aggregate_domain(
    graph, domains, "B", border_nodes, information_level="weighted"
)

case3_TA_A = aggregate_domain(graph, domains, "A", border_nodes, information_level="reachability")
case3_TA_B = aggregate_domain(graph, domains, "B", border_nodes, information_level="reachability")


print("Operator A:")
print("Original nodes:", len([
    n for n in graph.nodes if domains[n] == "A"
]))
print("Aggregated nodes:", TA_A.number_of_nodes())
print("Aggregated links:", TA_A.number_of_edges())
print("Case3 aggregated nodes:", case3_TA_A.number_of_nodes())
print("Case3 aggregated links:", case3_TA_A.number_of_edges())

print("Operator B:")
print("Original nodes:", len([
    n for n in graph.nodes if domains[n] == "B"
]))
print("Aggregated nodes:", TA_B.number_of_nodes())
print("Aggregated links:", TA_B.number_of_edges())
print("Case3 aggregated nodes:", case3_TA_B.number_of_nodes())
print("Case3 aggregated links:", case3_TA_B.number_of_edges())


#lag en felles graf med de aggregerte domenene:
TA_graph = nx.compose(TA_A, TA_B)

case3_TA_graph = nx.compose(case3_TA_A, case3_TA_B)

for u, v in graph.edges:
    if domains[u] != domains[v]:
        TA_graph.add_edge(
            u,
            v,
            weight=1,
            virtual=False
        )
        case3_TA_graph.add_edge(
            u,v,weight=1
        )

def add_terminal(graph, TA_graph, domains, terminal, border_nodes, information_level="weighted"):

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

            if information_level == "weighted":
                weight = len(path)-1
            elif information_level == "reachability":
                weight = 1
            else:
                raise ValueError("Unknown information level")

            TA_graph.add_edge(
                terminal,
                border,
                weight=weight,
                virtual=True
            )

#case2
add_terminal(graph, TA_graph, domains, source, border_nodes)
add_terminal(graph, TA_graph, domains, destination, border_nodes)

#case3
add_terminal(graph, case3_TA_graph, domains, source, border_nodes)
add_terminal(graph, case3_TA_graph, domains, destination, border_nodes)

case2_abstract_primary = nx.shortest_path(
    TA_graph,
    source=source,
    target=destination,
    weight="weight"
)

case3_abstract_primary = nx.shortest_path(
    case3_TA_graph,
    source=source,
    target=destination,
    weight="weight"
)

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

case3_TA_primary = expand_path(
    graph,
    domains,
    case3_abstract_primary
)

#finn en backup-path - TA-based shortest-path-first backup routing
# Copy physical graph
backup_graph = graph.copy()
case3_backup_graph = graph.copy()

# Remove primary path links
for i in range(len(case2_TA_primary) - 1):
    u = case2_TA_primary[i]
    v = case2_TA_primary[i + 1]

    backup_graph.remove_edge(u, v)

for i in range(len(case3_TA_primary) - 1):
    u = case3_TA_primary[i]
    v = case3_TA_primary[i + 1]

    case3_backup_graph.remove_edge(u, v)

# Rebuild TA based on remaining resources
#case2
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

#case3
case3_TA_A_backup = aggregate_domain(
    case3_backup_graph,
    domains,
    "A",
    border_nodes,
    information_level="reachability"
)

case3_TA_B_backup = aggregate_domain(
    case3_backup_graph,
    domains,
    "B",
    border_nodes,
    information_level="reachability"
)

case3_TA_backup_graph = nx.compose(
    case3_TA_A_backup,
    case3_TA_B_backup
)


# Add remaining inter-domain links
#case2
for u, v in backup_graph.edges:
    if domains[u] != domains[v]:
        TA_backup_graph.add_edge(
            u,
            v,
            weight=1,
            virtual=False
        )

#case3
for u, v in case3_backup_graph.edges:

    if domains[u] != domains[v]:

        case3_TA_backup_graph.add_edge(
            u,
            v,
            weight=1,
            virtual=False
        )

# Add terminals
#case2
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

#case3
add_terminal(
    case3_backup_graph,
    case3_TA_backup_graph,
    domains,
    source,
    border_nodes,
    information_level="reachability"
)

add_terminal(
    case3_backup_graph,
    case3_TA_backup_graph,
    domains,
    destination,
    border_nodes,
    information_level="reachability"
)


# Compute and expand backup
#case2
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

except (nx.NetworkXNoPath, nx.NodeNotFound):
    case2_TA_backup = None
    print("No TA backup path found")

#case3
try:
    case3_abstract_backup = nx.shortest_path(
        case3_TA_backup_graph,
        source=source,
        target=destination,
        weight="weight"
    )

    case3_TA_backup = expand_path(
        case3_backup_graph,
        domains,
        case3_abstract_backup
    )

except (nx.NetworkXNoPath, nx.NodeNotFound):

    case3_TA_backup = None
    print("No Case 3 backup path found")
    


figure_case2 = plot_border_paths(
    graph,
    domains,
    border_nodes,
    case2_abstract_primary,
    case2_abstract_backup,
    output_file="../topologies/case2_border_path_comparison.png",
)

figure_case3 = plot_border_paths(
      graph,
      domains,
      border_nodes,
      case3_abstract_primary,
      case3_abstract_backup,
      output_file="../topologies/case3_border_path_comparison.png",
  )

plot_topology(graph, domains, output_file=Path("../topologies/case2_border_path_comparison_physical.png"), show_labels=True, primary_path=case2_TA_primary, backup_path=case2_TA_backup)

plot_topology(graph, domains, output_file=Path("../topologies/case3_border_path_comparison_physical.png"), show_labels=True, primary_path=case3_TA_primary, backup_path=case3_TA_backup)



def path_edges(path):
    edges = set()

    for i in range(len(path) - 1):
        edges.add(frozenset((path[i], path[i + 1])))

    return edges

def print_path_details(name, path):
    """Print node IDs, labels, and physical hop count for one path."""
    if path is None:
        print(f"{name}: no path")
        return

    print(f"{name} node IDs: {path}")
    print(f"{name} labels: {path_labels(path)}")
    print(f"{name} hops: {len(path) - 1}")


print("CASE 1: FULL TOPOLOGY (BENCHMARK)")
print_path_details("Primary path", case1_primary_path)
print_path_details("Backup path", case1_backup_path)

print("\nCASE 2: WEIGHTED AGGREGATED TOPOLOGY")
print_path_details("Aggregated primary path", case2_abstract_primary)
print_path_details("Physical primary path", case2_TA_primary)
print_path_details("Aggregated backup path", case2_abstract_backup if case2_TA_backup is not None else None)
print_path_details("Physical backup path", case2_TA_backup)

print("\nCASE 3: REACHABILITY-ONLY AGGREGATED TOPOLOGY")
print_path_details("Aggregated primary path", case3_abstract_primary)
print_path_details("Physical primary path", case3_TA_primary)
print_path_details("Aggregated backup path", case3_abstract_backup if case3_TA_backup is not None else None)
print_path_details("Physical backup path", case3_TA_backup)

if case3_TA_backup is not None:
    shared = path_edges(case3_TA_primary) & path_edges(case3_TA_backup)
    print("Case 3 link-disjoint:", len(shared) == 0)

print("Case 3 primary equals Case 1 primary:", case3_TA_primary == case1_primary_path)
if case3_TA_backup is not None:
    print("Case 3 backup equals Case 1 backup:", case3_TA_backup == case1_backup_path)


if case2_TA_backup is not None:
    shared = path_edges(case2_TA_primary) & path_edges(case2_TA_backup)
    print("TA paths link-disjoint:", len(shared) == 0)


