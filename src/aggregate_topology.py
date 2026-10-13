from topology import graph, domains, border_nodes, find_border_nodes
from calculate_paths import source, destination, path_labels, primary_path, backup_path
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

abstract_primary = nx.shortest_path(
    TA_graph,
    source=source,
    target=destination,
    weight="weight"
)

print("Abstract primary path:")
print(path_labels(abstract_primary))

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

TA_primary = expand_path(
    graph,
    domains,
    abstract_primary
)

print("Physical primary path:")
print(path_labels(TA_primary))

#finn en backup-path - TA-based shortest-path-first backup routing
# Copy physical graph
backup_graph = graph.copy()

# Remove primary path links
for i in range(len(TA_primary) - 1):
    u = TA_primary[i]
    v = TA_primary[i + 1]

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
    abstract_backup = nx.shortest_path(
        TA_backup_graph,
        source,
        destination,
        weight="weight"
    )

    TA_backup = expand_path(
        backup_graph,
        domains,
        abstract_backup
    )

    print("TA backup:", path_labels(TA_backup))

except (nx.NetworkXNoPath, nx.NodeNotFound):
    TA_backup = None
    print("No TA backup path found")




print("CASE 1: FULL TOPOLOGY")
print("Primary:", primary_path)
print("Backup:", backup_path)

print("\nCASE 2: TOPOLOGY AGGREGATION")
print("Primary:", TA_primary)
print("Backup:", TA_backup)

print("\nPATH LENGTHS")

print("Full primary:", len(primary_path) - 1)
print("TA primary:", len(TA_primary) - 1)

if backup_path is not None:
    print("Full backup:", len(backup_path) - 1)

if TA_backup is not None:
    print("TA backup:", len(TA_backup) - 1)


def path_edges(path):
    edges = set()

    for i in range(len(path) - 1):
        edges.add(frozenset((path[i], path[i + 1])))

    return edges


if TA_backup is not None:
    shared = path_edges(TA_primary) & path_edges(TA_backup)
    print("TA paths link-disjoint:", len(shared) == 0)

#plot primary- and backup-paths 
def plot_border_paths(
    graph,
    domains,
    primary_path,
    backup_path,
    show_labels=True,
):
    border_node_map = find_border_nodes(graph, domains)
    border_nodes = set(border_node_map.keys())

    def is_mainland(node):
        data = graph.nodes[node]
        return data["lon"] >= 0 and data["label"] != "Stockholm"

    def reduced_path(path):
        """Behold kun endepunkter og border-noder som ligger på pathen."""
        return [
            node
            for index, node in enumerate(path)
            if is_mainland(node)
            and (
                index == 0
                or index == len(path) - 1
                or node in border_nodes
            )
        ]

    primary_nodes = reduced_path(primary_path)
    backup_nodes = reduced_path(backup_path)

    # Alle noder som er relevante for minst én av rutene.
    visible_nodes = list(set(primary_nodes) | set(backup_nodes))

    positions = {
        node: (
            float(graph.nodes[node]["lon"]),
            float(graph.nodes[node]["lat"]),
        )
        for node in visible_nodes
    }

    def path_segments(path):
        return [
            (positions[source], positions[target])
            for source, target in zip(path, path[1:])
        ]

    fig, axis = plt.subplots(figsize=(8, 12), constrained_layout=True)
    axis.set_facecolor("#edf5f8")

    mainland_positions = {
        node: (
            float(data["lon"]),
            float(data["lat"]),
        )
        for node, data in graph.nodes(data=True)
        if data["lon"] >= 0 and data["label"] != "Stockholm"
    }

    background_segments = [
        (mainland_positions[source], mainland_positions[target])
        for source, target in graph.edges
        if source in mainland_positions
        and target in mainland_positions
        and mainland_positions[source] != mainland_positions[target]
    ]

    axis.add_collection(
        LineCollection(
            background_segments,
            colors="#cbd5e1",  # svak grå
            linewidths=0.8,
            alpha=0.5,
            zorder=0,
        )
    )


        # Backup tegnes først, slik at primary path vises øverst ved overlapp.
    axis.add_collection(
        LineCollection(
            path_segments(backup_nodes),
            colors="#86efac",      # lys grønn
            linewidths=4,
            alpha=0.9,
            zorder=1,
        )
    )

    axis.add_collection(
        LineCollection(
            path_segments(primary_nodes),
            colors="#facc15",      # gul
            linewidths=4,
            alpha=0.95,
            zorder=2,
        )
    )

    node_colors = [
        "#dc2626" if domains[node] == "A" else "#2563eb"
        for node in visible_nodes
    ]

    axis.scatter(
        [positions[node][0] for node in visible_nodes],
        [positions[node][1] for node in visible_nodes],
        s=130,
        c=node_colors,
        edgecolors="white",
        linewidths=1,
        zorder=3,
    )

    if show_labels:
        for node in visible_nodes:
            x, y = positions[node]
            axis.text(
                x,
                y,
                graph.nodes[node]["label"],
                fontsize=7,
                ha="center",
                va="center",
                zorder=4,
            )

    axis.legend(
        handles=[
            Line2D([], [], color="#facc15", linewidth=4, label="Primary path"),
            Line2D([], [], color="#86efac", linewidth=4, label="Backup path"),
            Line2D([], [], marker="o", color="none",
                    markerfacecolor="#dc2626", markersize=8, label="Operator A"),
            Line2D([], [], marker="o", color="none",
                    markerfacecolor="#2563eb", markersize=8, label="Operator B"),
        ],
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=True,
    )

    axis.set_title("Primary and backup path through border nodes")
    axis.set_aspect(1 / math.cos(math.radians(62)), adjustable="box")
    axis.set_axis_off()

    return fig


figure = plot_border_paths(
    graph,
    domains,
    primary_path,
    backup_path,
)

figure.savefig(
    "../topologies/border_path_comparison.png",
    dpi=240,
    bbox_inches="tight",
)