from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import GraphEdge, GraphNodeRef, GraphQueryResult
from .store import GraphStore


class GraphQueryService(Protocol):
    def local_subgraph_for_node(
        self,
        node_ref: GraphNodeRef,
        max_hops: int = 2,
        edge_types: set[str] | None = None,
    ) -> GraphQueryResult: ...

    def alignment_edges_for_concept(
        self,
        concept_ref: GraphNodeRef,
        statuses: set[str] | None = None,
    ) -> list[GraphEdge]: ...


@dataclass
class DefaultGraphQueryService(GraphQueryService):
    store: GraphStore

    def local_subgraph_for_node(
        self,
        node_ref: GraphNodeRef,
        max_hops: int = 2,
        edge_types: set[str] | None = None,
    ) -> GraphQueryResult:
        subgraph = self.store.query_local_subgraph([node_ref], max_hops=max_hops, edge_types=edge_types)
        return GraphQueryResult(
            summary=f"Local subgraph for {node_ref.node_type}:{node_ref.node_id}",
            subgraph=subgraph,
        )

    def alignment_edges_for_concept(
        self,
        concept_ref: GraphNodeRef,
        statuses: set[str] | None = None,
    ) -> list[GraphEdge]:
        allowed = {
            "IMPLEMENTED_BY",
            "SUPPORTED_BY",
            "STRUCTURALLY_SUPPORTED_BY",
            "MISSING_EVIDENCE_FOR",
            "CONTRADICTED_BY",
        }
        edges = self.store.get_outgoing_edges(concept_ref, allowed)
        if not statuses:
            return edges
        return [edge for edge in edges if edge.attributes.get("status") in statuses]
