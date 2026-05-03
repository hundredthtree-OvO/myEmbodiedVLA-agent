from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Protocol

from .models import GraphEdge, GraphNode, GraphNodeRef, GraphSubgraph


class GraphStore(Protocol):
    def upsert_node(self, node: GraphNode) -> None: ...

    def upsert_edge(self, edge: GraphEdge) -> None: ...

    def get_node(self, ref: GraphNodeRef) -> GraphNode | None: ...

    def get_outgoing_edges(
        self,
        ref: GraphNodeRef,
        edge_types: set[str] | None = None,
    ) -> list[GraphEdge]: ...

    def get_incoming_edges(
        self,
        ref: GraphNodeRef,
        edge_types: set[str] | None = None,
    ) -> list[GraphEdge]: ...

    def query_local_subgraph(
        self,
        seeds: list[GraphNodeRef],
        max_hops: int = 2,
        edge_types: set[str] | None = None,
    ) -> GraphSubgraph: ...


@dataclass
class InMemoryGraphStore(GraphStore):
    _nodes: dict[tuple[str, str], GraphNode] = field(default_factory=dict)
    _outgoing: dict[tuple[str, str], list[GraphEdge]] = field(default_factory=dict)
    _incoming: dict[tuple[str, str], list[GraphEdge]] = field(default_factory=dict)

    def upsert_node(self, node: GraphNode) -> None:
        self._nodes[(node.node_type, node.node_id)] = node

    def upsert_edge(self, edge: GraphEdge) -> None:
        self._outgoing.setdefault((edge.src.node_type, edge.src.node_id), []).append(edge)
        self._incoming.setdefault((edge.dst.node_type, edge.dst.node_id), []).append(edge)

    def get_node(self, ref: GraphNodeRef) -> GraphNode | None:
        return self._nodes.get((ref.node_type, ref.node_id))

    def get_outgoing_edges(
        self,
        ref: GraphNodeRef,
        edge_types: set[str] | None = None,
    ) -> list[GraphEdge]:
        edges = self._outgoing.get((ref.node_type, ref.node_id), [])
        return _filter_edges(edges, edge_types)

    def get_incoming_edges(
        self,
        ref: GraphNodeRef,
        edge_types: set[str] | None = None,
    ) -> list[GraphEdge]:
        edges = self._incoming.get((ref.node_type, ref.node_id), [])
        return _filter_edges(edges, edge_types)

    def query_local_subgraph(
        self,
        seeds: list[GraphNodeRef],
        max_hops: int = 2,
        edge_types: set[str] | None = None,
    ) -> GraphSubgraph:
        visited_nodes: set[tuple[str, str]] = set()
        visited_edges: set[tuple[str, str, str, str, str]] = set()
        queue = deque((seed, 0) for seed in seeds)

        while queue:
            ref, hop = queue.popleft()
            key = (ref.node_type, ref.node_id)
            if key in visited_nodes:
                continue
            visited_nodes.add(key)

            if hop >= max_hops:
                continue

            for edge in self.get_outgoing_edges(ref, edge_types):
                edge_key = (edge.edge_type, edge.src.node_type, edge.src.node_id, edge.dst.node_type, edge.dst.node_id)
                visited_edges.add(edge_key)
                queue.append((edge.dst, hop + 1))
            for edge in self.get_incoming_edges(ref, edge_types):
                edge_key = (edge.edge_type, edge.src.node_type, edge.src.node_id, edge.dst.node_type, edge.dst.node_id)
                visited_edges.add(edge_key)
                queue.append((edge.src, hop + 1))

        nodes = [node for key, node in self._nodes.items() if key in visited_nodes]
        edges: list[GraphEdge] = []
        for edge_list in self._outgoing.values():
            for edge in edge_list:
                edge_key = (edge.edge_type, edge.src.node_type, edge.src.node_id, edge.dst.node_type, edge.dst.node_id)
                if edge_key in visited_edges:
                    edges.append(edge)
        return GraphSubgraph(seed_nodes=list(seeds), nodes=nodes, edges=edges)


def _filter_edges(edges: list[GraphEdge], edge_types: set[str] | None) -> list[GraphEdge]:
    if not edge_types:
        return list(edges)
    return [edge for edge in edges if edge.edge_type in edge_types]
