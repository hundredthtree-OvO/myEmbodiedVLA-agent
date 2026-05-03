from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


GraphAttributes = dict[str, Any]


@dataclass(frozen=True)
class GraphNodeRef:
    node_type: str
    node_id: str


@dataclass(frozen=True)
class GraphNode:
    node_type: str
    node_id: str
    attributes: GraphAttributes = field(default_factory=dict)

    @property
    def ref(self) -> GraphNodeRef:
        return GraphNodeRef(self.node_type, self.node_id)


@dataclass(frozen=True)
class GraphEdge:
    edge_type: str
    src: GraphNodeRef
    dst: GraphNodeRef
    attributes: GraphAttributes = field(default_factory=dict)


@dataclass(frozen=True)
class GraphSubgraph:
    seed_nodes: list[GraphNodeRef]
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@dataclass(frozen=True)
class GraphQueryResult:
    summary: str
    subgraph: GraphSubgraph
    evidence_node_refs: list[GraphNodeRef] = field(default_factory=list)
