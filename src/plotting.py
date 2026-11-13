"""Reusable geographic plots for the UNINETT topology.

The functions in this module only draw figures.  Loading a graph, assigning
operator domains, finding border nodes, and calculating paths belong in the
calling module.  This keeps imports free of side effects.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import matplotlib

# These functions are primarily used to write PNG files.  Selecting a
# non-interactive backend also makes them work when no graphical display exists.
matplotlib.use("Agg")
from adjustText import adjust_text
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import networkx as nx


OPERATOR_COLORS = {"A": "#dc2626", "B": "#2563eb"}
PRIMARY_PATH_COLOR = "#facc15"
BACKUP_PATH_COLOR = "#86efac"


def _is_mainland(graph: nx.Graph, node: object) -> bool:
    """Return whether *node* is included in the mainland-Norway view."""
    data = graph.nodes[node]
    return float(data["lon"]) >= 0 and data["label"] != "Stockholm"


def _mainland_positions(graph: nx.Graph) -> dict[object, tuple[float, float]]:
    return {
        node: (float(data["lon"]), float(data["lat"]))
        for node, data in graph.nodes(data=True)
        if _is_mainland(graph, node)
    }


def _edge_segments(
    graph: nx.Graph,
    positions: Mapping[object, tuple[float, float]],
    edges: Iterable[tuple[object, object]] | None = None,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """Convert graph edges to drawable geographic line segments."""
    edge_list = graph.edges() if edges is None else edges
    segments = []
    for source, target in edge_list:
        if source not in positions or target not in positions:
            continue
        start, end = positions[source], positions[target]
        if start != end:
            segments.append((start, end))
    return segments


def _draw_background(axis: plt.Axes, graph: nx.Graph) -> None:
    """Draw a subdued full network to preserve Norway's geographic shape."""
    positions = _mainland_positions(graph)
    segments = _edge_segments(graph, positions)
    axis.add_collection(
        LineCollection(
            segments,
            colors="#cbd5e1",
            linewidths=0.8,
            alpha=0.5,
            zorder=0,
        )
    )


def _draw_labels(
    axis: plt.Axes,
    graph: nx.Graph,
    nodes: Iterable[object],
    positions: Mapping[object, tuple[float, float]],
    font_size: float = 7.5,
) -> None:
    """Draw non-overlapping labels with guide lines where needed."""
    texts = []
    for node in nodes:
        x, y = positions[node]
        texts.append(
            axis.text(
                x,
                y,
                graph.nodes[node]["label"],
                fontsize=font_size,
                ha="center",
                va="center",
                color="#263238",
                zorder=5,
            )
        )

    if texts:
        adjust_text(
            texts,
            ax=axis,
            expand=(1.4, 1.7),
            force_text=(1.2, 1.6),
            force_static=(1.0, 1.4),
            force_explode=(1.0, 1.2),
            max_move=(100, 100),
            ensure_inside_axes=True,
            iter_lim=1000,
            arrowprops={"arrowstyle": "-", "color": "#64748b", "lw": 0.5},
        )


def _finish_figure(
    figure: plt.Figure,
    axis: plt.Axes,
    title: str,
    legend_handles: list[Line2D],
    output_file: str | Path | None,
) -> plt.Figure:
    axis.set_title(title, fontsize=16, weight="bold", pad=12)
    axis.set_aspect(1 / math.cos(math.radians(62)), adjustable="box")
    axis.margins(x=0.08, y=0.045)
    axis.set_axis_off()

    if legend_handles:
        axis.legend(
            handles=legend_handles,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=True,
            facecolor="white",
            edgecolor="none",
            fontsize=12,
        )

    if output_file is not None:
        target = Path(output_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(target, dpi=240, bbox_inches="tight")

    return figure


def _border_node_set(border_nodes: Mapping[object, Any] | Iterable[object]) -> set[object]:
    """Accept either find_border_nodes()'s dictionary or a node iterable."""
    if isinstance(border_nodes, Mapping):
        return set(border_nodes.keys())
    return set(border_nodes)


def _path_segments(
    path: Sequence[object] | None,
    positions: Mapping[object, tuple[float, float]],
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    if not path:
        return []
    return [
        (positions[source], positions[target])
        for source, target in zip(path, path[1:])
        if source in positions and target in positions
    ]


def plot_topology(
    graph: nx.Graph,
    domains: Mapping[object, str],
    *,
    primary_path: Sequence[object] | None = None,
    backup_path: Sequence[object] | None = None,
    show_labels: bool = False,
    output_file: str | Path | None = None,
) -> plt.Figure:
    """Plot the complete mainland topology, optionally highlighting two paths."""
    positions = _mainland_positions(graph)
    degrees = dict(graph.degree())
    hubs = [node for node in positions if degrees[node] >= 4]
    sites = [node for node in positions if node not in hubs]

    figure, axis = plt.subplots(figsize=(8, 12), constrained_layout=True)
    figure.patch.set_facecolor("#FFFFFF")
    axis.set_facecolor("#FFFFFF")
    axis.add_collection(
        LineCollection(
            _edge_segments(graph, positions),
            colors="#78909c",
            linewidths=1.15,
            alpha=0.65,
            zorder=0,
        )
    )

    # Draw backup first, so primary remains visible on shared portions.
    backup_segments = _path_segments(backup_path, positions)
    if backup_segments:
        axis.add_collection(
            LineCollection(backup_segments, colors=BACKUP_PATH_COLOR, linewidths=4, alpha=0.9, zorder=1)
        )
    primary_segments = _path_segments(primary_path, positions)
    if primary_segments:
        axis.add_collection(
            LineCollection(primary_segments, colors=PRIMARY_PATH_COLOR, linewidths=4, alpha=0.95, zorder=2)
        )

    for nodes, size, marker in ((sites, 30, "o"), (hubs, 82, "h")):
        for domain, color in OPERATOR_COLORS.items():
            domain_nodes = [node for node in nodes if domains[node] == domain]
            axis.scatter(
                [positions[node][0] for node in domain_nodes],
                [positions[node][1] for node in domain_nodes],
                s=size,
                color=color,
                marker=marker,
                edgecolors="white",
                linewidths=0.7,
                zorder=3,
            )

    if show_labels:
        # On path comparison plots, label only nodes that occur in one of the
        # highlighted paths.  This keeps unrelated site names out of the
        # figure while preserving the full topology in the background.
        path_nodes = set(primary_path or ()) | set(backup_path or ())
        label_nodes = [node for node in positions if node in path_nodes]
        _draw_labels(axis, graph, label_nodes, positions, font_size=7.5)

    handles = [
        Line2D([], [], marker="o", color="none", markerfacecolor=OPERATOR_COLORS["A"], markeredgecolor="white", markersize=8, label="Operator A"),
        Line2D([], [], marker="o", color="none", markerfacecolor=OPERATOR_COLORS["B"], markeredgecolor="white", markersize=8, label="Operator B"),
        Line2D([], [], marker="h", color="none", markerfacecolor="#6b7280", markeredgecolor="white", markersize=8, label="Network hub (4+ links)"),
    ]
    if primary_segments:
        handles.append(Line2D([], [], color=PRIMARY_PATH_COLOR, linewidth=4, label="Primary path"))
    if backup_segments:
        handles.append(Line2D([], [], color=BACKUP_PATH_COLOR, linewidth=4, label="Backup path"))

    return _finish_figure(
        figure,
        axis,
        "UNINETT topology · mainland Norway",
        handles,
        output_file,
    )


def plot_border_nodes(
    graph: nx.Graph,
    domains: Mapping[object, str],
    border_nodes: Mapping[object, Any] | Iterable[object],
    *,
    additional_nodes: Iterable[object] = (),
    show_labels: bool = True,
    show_background: bool = True,
    output_file: str | Path | None = None,
) -> plt.Figure:
    """Plot mainland border nodes and direct links between visible nodes."""
    visible = _border_node_set(border_nodes) | set(additional_nodes)
    nodes = sorted((node for node in visible if _is_mainland(graph, node)), key=str)
    positions = {node: (float(graph.nodes[node]["lon"]), float(graph.nodes[node]["lat"])) for node in nodes}
    visible_set = set(nodes)
    direct_edges = [
        (source, target)
        for source, target in graph.edges()
        if source in visible_set and target in visible_set
    ]

    figure, axis = plt.subplots(figsize=(8, 12), constrained_layout=True)
    figure.patch.set_facecolor("#FFFFFF")
    axis.set_facecolor("#FFFFFF")
    if show_background:
        _draw_background(axis, graph)

    axis.add_collection(
        LineCollection(_edge_segments(graph, positions, direct_edges), colors="#475569", linewidths=2.5, zorder=1)
    )
    axis.scatter(
        [positions[node][0] for node in nodes],
        [positions[node][1] for node in nodes],
        s=130,
        c=[OPERATOR_COLORS[domains[node]] for node in nodes],
        edgecolors="white",
        linewidths=1,
        zorder=3,
    )

    if show_labels:
        _draw_labels(axis, graph, nodes, positions)

    handles = [
        Line2D([], [], marker="o", color="none", markerfacecolor=OPERATOR_COLORS["A"], markersize=8, label="Operator A"),
        Line2D([], [], marker="o", color="none", markerfacecolor=OPERATOR_COLORS["B"], markersize=8, label="Operator B"),
        Line2D([], [], color="#475569", linewidth=2.5, label="Direct visible link"),
    ]
    return _finish_figure(figure, axis, "Border nodes between operator A and B", handles, output_file)


def plot_border_paths(
    graph: nx.Graph,
    domains: Mapping[object, str],
    border_nodes: Mapping[object, Any] | Iterable[object],
    primary_path: Sequence[object],
    backup_path: Sequence[object] | None = None,
    *,
    show_labels: bool = True,
    show_background: bool = True,
    output_file: str | Path | None = None,
) -> plt.Figure:
    """Plot primary/backup paths using only their endpoints and border nodes.

    Internal nodes are intentionally hidden.  A coloured segment therefore
    represents the part of the physical route between two visible nodes.
    """
    border_set = _border_node_set(border_nodes)

    def reduce_path(path: Sequence[object] | None) -> list[object]:
        if not path:
            return []
        return [
            node
            for index, node in enumerate(path)
            if _is_mainland(graph, node)
            and (index == 0 or index == len(path) - 1 or node in border_set)
        ]

    primary_nodes = reduce_path(primary_path)
    backup_nodes = reduce_path(backup_path)
    if len(primary_nodes) < 2:
        raise ValueError("The primary path needs two mainland endpoints to be plotted.")

    nodes = sorted(set(primary_nodes) | set(backup_nodes), key=str)
    positions = {node: (float(graph.nodes[node]["lon"]), float(graph.nodes[node]["lat"])) for node in nodes}

    figure, axis = plt.subplots(figsize=(8, 12), constrained_layout=True)
    figure.patch.set_facecolor("#FFFFFF")
    axis.set_facecolor("#FFFFFF")
    if show_background:
        _draw_background(axis, graph)

    backup_segments = _path_segments(backup_nodes, positions)
    if backup_segments:
        axis.add_collection(
            LineCollection(backup_segments, colors=BACKUP_PATH_COLOR, linewidths=4, alpha=0.9, zorder=1)
        )
    primary_segments = _path_segments(primary_nodes, positions)
    axis.add_collection(
        LineCollection(primary_segments, colors=PRIMARY_PATH_COLOR, linewidths=4, alpha=0.95, zorder=2)
    )

    axis.scatter(
        [positions[node][0] for node in nodes],
        [positions[node][1] for node in nodes],
        s=130,
        c=[OPERATOR_COLORS[domains[node]] for node in nodes],
        edgecolors="white",
        linewidths=1,
        zorder=3,
    )
    if show_labels:
        _draw_labels(axis, graph, nodes, positions)

    handles = [
        Line2D([], [], color=PRIMARY_PATH_COLOR, linewidth=4, label="Primary path"),
        Line2D([], [], marker="o", color="none", markerfacecolor=OPERATOR_COLORS["A"], markersize=8, label="Operator A"),
        Line2D([], [], marker="o", color="none", markerfacecolor=OPERATOR_COLORS["B"], markersize=8, label="Operator B"),
    ]
    if backup_segments:
        handles.insert(1, Line2D([], [], color=BACKUP_PATH_COLOR, linewidth=4, label="Backup path"))

    return _finish_figure(
        figure,
        axis,
        "Primary and backup path through border nodes",
        handles,
        output_file,
    )
