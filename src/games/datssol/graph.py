from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

Point = tuple[int, int]


@dataclass(frozen=True)
class GraphSummary:
    components: tuple[tuple[Point, ...], ...]
    articulation_points: tuple[Point, ...]
    is_main_connected: bool


def build_support_graph(nodes: list[Point], signal_range: int) -> dict[Point, set[Point]]:
    graph: dict[Point, set[Point]] = defaultdict(set)
    for i, src in enumerate(nodes):
        for dst in nodes[i + 1 :]:
            if in_square_range(src, dst, signal_range):
                graph[src].add(dst)
                graph[dst].add(src)
        graph.setdefault(src, set())
    return graph


def connected_components(graph: dict[Point, set[Point]]) -> tuple[tuple[Point, ...], ...]:
    seen: set[Point] = set()
    components: list[tuple[Point, ...]] = []
    for node in sorted(graph):
        if node in seen:
            continue
        stack = [node]
        comp: list[Point] = []
        seen.add(node)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in sorted(graph.get(cur, set())):
                if nxt in seen:
                    continue
                seen.add(nxt)
                stack.append(nxt)
        components.append(tuple(sorted(comp)))
    return tuple(components)


def articulation_points(graph: dict[Point, set[Point]]) -> tuple[Point, ...]:
    # Simple O(V*(V+E)) brute-force for small visible sets.
    nodes = sorted(graph)
    if len(nodes) <= 2:
        return tuple()
    base_components = len(connected_components(graph))
    critical: list[Point] = []
    for node in nodes:
        pruned = {k: {n for n in v if n != node} for k, v in graph.items() if k != node}
        if len(pruned) == 0:
            continue
        comps = len(connected_components(pruned))
        if comps > base_components:
            critical.append(node)
    return tuple(critical)


def in_square_range(src: Point, dst: Point, rng: int) -> bool:
    return abs(src[0] - dst[0]) <= rng and abs(src[1] - dst[1]) <= rng


def summarize_graph(
    *, plantations: list[Point], main: Point | None, signal_range: int
) -> GraphSummary:
    graph = build_support_graph(plantations, signal_range)
    comps = connected_components(graph)
    main_connected = False
    if main is not None:
        for comp in comps:
            if main not in comp:
                continue
            main_connected = len(comp) == len(graph)
            break
    return GraphSummary(
        components=comps,
        articulation_points=articulation_points(graph),
        is_main_connected=main_connected,
    )
