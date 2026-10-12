"""Create a clean geographic plot of the 2011 UNINETT topology.

Run ``python3 uninett_2011.py`` to create
``topologies/uninett_2011.png``.  Add ``--labels`` to show site names.

Dependencies:
    pip install matplotlib networkx
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from adjustText import adjust_text

import matplotlib

if "--show" not in sys.argv:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import networkx as nx

DATA_FILE_modified = Path(__file__).resolve().parent.parent / "data" / "uninett_modified.gml"
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "uninett_2011.gml"
DEFAULT_OUTPUT = Path("../topologies/uninett_2011.png")


def load_topology(data_file) -> nx.Graph:
    """Load the 2011 UNINETT topology."""
    return nx.read_gml(data_file, label=None)


def assign_operator_domains(graph: nx.Graph, seed: int = 2026) -> dict[object, str]:
    """Split the topology into two balanced, connected operator domains."""
    first, second = nx.community.kernighan_lin_bisection(graph, seed=seed)

    if not nx.is_connected(graph.subgraph(first)) or not nx.is_connected(graph.subgraph(second)):
        raise ValueError("Could not create two connected operator domains")

    # Give the domain containing UiO a stable name, independent of set order.
    if 0 not in first:
        first, second = second, first
    return {node: "A" if node in first else "B" for node in graph.nodes}


def plot_topology(
    graph: nx.Graph,
    output_file: Path | None = DEFAULT_OUTPUT,
    show_labels: bool = False,
    seed: int = 2026,
    primary_path: list[int] | None = None,
    backup_path: list[int] | None = None,
) -> plt.Figure:
    """Plot mainland sites and merge visually overlapping geographic links."""
    positions = {
        node: (float(data["lon"]), float(data["lat"]))
        for node, data in graph.nodes(data=True)
        # The original data places Svalbard at -8.72° / 70.92°, and also
        # contains Stockholm as an external node.  Both are omitted from this
        # mainland-Norway overview to keep its geography readable.
        if data["lon"] >= 0 and data["label"] != "Stockholm"
    }

    # Multiple logical sites share coordinates.  One line per location pair is
    # clearer than drawing zero-length loops and overlapping parallel routes.
    segments = set()
    for source, target in graph.edges():
        if source in positions and target in positions:
            start, end = positions[source], positions[target]
            if start != end:
                segments.add(tuple(sorted((start, end))))

    degrees = dict(graph.degree())
    hubs = [node for node in positions if degrees[node] >= 4]
    sites = [node for node in positions if node not in hubs]
    domains = assign_operator_domains(graph, seed)

    colors = {"A": "#dc2626", "B": "#2563eb"}
    inter_domain_links = sum(
        1 for source, target in graph.edges() if domains[source] != domains[target]
    )

    fig, axis = plt.subplots(figsize=(8, 12), constrained_layout=True)
    fig.patch.set_facecolor("#f7fafc")
    axis.set_facecolor("#edf5f8")
    axis.add_collection(
        LineCollection(
            list(segments), colors="#78909c", linewidths=1.15, alpha=0.65, zorder=1
        )
    )

    def path_segments(path):
        if path is None:
            return []

        return [
            (positions[source], positions[target])
            for source, target in zip(path, path[1:])
            if source in positions and target in positions
        ]

    backup_segments = path_segments(backup_path)
    if backup_segments:
        axis.add_collection(
            LineCollection(
                backup_segments,
                  colors="#86efac",       
                  linewidths=4,
                  alpha=0.9,
                  zorder=1.5,
            )
        )

    primary_segments = path_segments(primary_path)
    if primary_path:
        axis.add_collection(
            LineCollection(
                primary_segments,
                  colors="#facc15",      
                  linewidths=4,
                  alpha=0.95,
                  zorder=1.6,
            )
        )    

    for nodes, size, marker in ((sites, 30, "o"), (hubs, 82, "h")):
        for domain in ("A", "B"):
            domain_nodes = [node for node in nodes if domains[node] == domain]
            axis.scatter(
                [positions[node][0] for node in domain_nodes],
                [positions[node][1] for node in domain_nodes],
                s=size,
                color=colors[domain],
                marker=marker,
                edgecolors="white",
                linewidths=0.7,
                zorder=2,
            )

    if show_labels:
        labels = {node: data["label"] for node, data in graph.nodes(data=True) if node in positions}
        nx.draw_networkx_labels(
            graph.subgraph(positions),
            positions,
            labels=labels,
            ax=axis,
            font_size=5,
            font_color="#263238",
            verticalalignment="bottom",
        )

    axis.set_title("UNINETT topology · mainland Norway", fontsize=16, weight="bold", pad=12)
    axis.text(
        0.5,
        1.005,
        f"Historic topology, 2011 · two connected domains · {inter_domain_links} inter-domain links",
        transform=axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=8,
        color="#52616b",
    )
    axis.set_aspect(1 / math.cos(math.radians(62)), adjustable="box")
    axis.margins(x=0.08, y=0.045)
    axis.set_axis_off()
    axis.legend(
        handles=[
            Line2D([], [], marker="o", color="none", markerfacecolor=colors["A"], markeredgecolor="white", markersize=8, label="Operator A"),
            Line2D([], [], marker="o", color="none", markerfacecolor=colors["B"], markeredgecolor="white", markersize=8, label="Operator B"),
            Line2D([], [], marker="h", color="none", markerfacecolor="#6b7280", markeredgecolor="white", markersize=8, label="Network hub (4+ links)"),
            Line2D([], [], color="#facc15", linewidth=4, label="Primary path"),
            Line2D([], [], color="#86efac", linewidth=4, label="Backup path"),
        ],
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=True,
        facecolor="white",
        edgecolor="none",
        fontsize=8,
    )

    if output_file is not None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_file, dpi=240, bbox_inches="tight")
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot the 2011 UNINETT GML topology.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="PNG output path")
    parser.add_argument("--labels", action="store_true", help="Show site names")
    parser.add_argument("--show", action="store_true", help="Open the completed plot")
    parser.add_argument("--seed", type=int, default=2026, help="Seed for the balanced graph partition")
    arguments = parser.parse_args()

    figure = plot_topology(load_topology(DATA_FILE), arguments.output, arguments.labels, arguments.seed)
    print(f"Saved topology plot to {arguments.output}")
    if arguments.show:
        plt.show()
    else:
        plt.close(figure)


#check if the graphs are connected
graph = load_topology(DATA_FILE)
graph_modified = load_topology(DATA_FILE_modified)
domains = assign_operator_domains(graph)

def check_graph_connectivity(graph, domains):
    a_nodes = [node for node, domain in domains.items() if domain == "A"]
    b_nodes = [node for node, domain in domains.items() if domain == "B"]

    print("A connected:", nx.is_connected(graph.subgraph(a_nodes)))
    print("B connected:", nx.is_connected(graph.subgraph(b_nodes)))


def find_border_nodes(graph, domains):
    border_nodes = {}

    for node in graph.nodes:
        other_operator_neighbors = [
            neighbor
            for neighbor in graph.neighbors(node)
            if domains[neighbor] != domains[node]
        ]

        if other_operator_neighbors:
            border_nodes[node] = other_operator_neighbors

    for node, neighbors in border_nodes.items():
        node_label = graph.nodes[node]["label"]
        operator = domains[node]
        neighbor_labels = [graph.nodes[neighbor]["label"] for neighbor in
        neighbors]

        print(f"{node_label} (operatør {operator}) -> {neighbor_labels}")

    return border_nodes


def plot_border_nodes(graph, domains, show_labels=True):
    # Finner alle border-noder med funksjonen du allerede har laget.
    border_node_map = find_border_nodes(graph, domains)
    all_border_nodes = set(border_node_map.keys())

    # Behold bare border-noder på fastlands-Norge.
    border_nodes = [
        node
        for node in all_border_nodes
        if graph.nodes[node]["lon"] >= 0
        and graph.nodes[node]["label"] != "Stockholm"
    ]

    positions = {
        node: (
            float(graph.nodes[node]["lon"]),
            float(graph.nodes[node]["lat"]),
        )
        for node in border_nodes
    }

    # Tegn alle direkte lenker der begge nodene er border-noder.
    border_edges = [
        (source, target)
        for source, target in graph.edges
        if source in border_nodes and target in border_nodes
    ]

    colors = {
        node: "#dc2626" if domains[node] == "A" else "#2563eb"
        for node in border_nodes
    }

    fig, axis = plt.subplots(figsize=(8, 12), constrained_layout=True)
    axis.set_facecolor("#edf5f8")

    # Alle fastlandsnoder brukes bare for å tegne et svakt bakgrunnsnettverk.
    mainland_positions = {
        node: (
            float(data["lon"]),
            float(data["lat"]),
        )
        for node, data in graph.nodes(data=True)
        if data["lon"] >= 0 and data["label"] != "Stockholm"
    }

    background_edges = [
        (mainland_positions[source], mainland_positions[target])
        for source, target in graph.edges
        if source in mainland_positions
        and target in mainland_positions
        and mainland_positions[source] != mainland_positions[target]
    ]

    axis.add_collection(
        LineCollection(
            background_edges,
            colors="#cbd5e1",  # svak grå bakgrunn
            linewidths=0.8,
            alpha=0.5,
            zorder=1,
        )
    )

    nx.draw_networkx_edges(
        graph.edge_subgraph(border_edges),
        positions,
        ax=axis,
        edge_color="#475569",
        width=2.5,
    )

    nx.draw_networkx_nodes(
        graph.subgraph(border_nodes),
        positions,
        ax=axis,
        node_color=[colors[node] for node in border_nodes],
        node_size=130,
        edgecolors="white",
        linewidths=1,
    )

    if show_labels:
        labels = {
            node: graph.nodes[node]["label"]
            for node in border_nodes
        }

        texts = []

        for node, label in labels.items():
            x, y = positions[node]

            text = axis.text(
                x,
                y,
                label,
                fontsize=7,
                ha="center",
                va="center",
                zorder=4,
            )

            texts.append(text)

        adjust_text(
            texts,
            ax=axis,
            arrowprops={
                "arrowstyle": "-",
                "color": "#64748b",
                "lw": 0.5,
            },
        )

    axis.set_title("Border nodes between operator A and B")
    axis.set_aspect(1 / math.cos(math.radians(62)), adjustable="box")
    axis.set_axis_off()

    return fig
    


if __name__ == "__main__":
    main()
    #check_graph_connectivity(graph, domains)
    #find_border_nodes(graph, domains)


#print(find_border_nodes(graph, domains))
figure = plot_border_nodes(graph, domains)
figure.savefig("../topologies/border_nodes.png", dpi=240, bbox_inches="tight")