from __future__ import annotations

import unittest
from pathlib import Path

from study_agent.graph import DefaultGraphQueryService, GraphEdge, GraphNode, GraphNodeRef, InMemoryGraphStore
from study_agent.repo import PythonAstCodeParser


class GraphInterfaceTests(unittest.TestCase):
    def test_inmemory_graph_store_and_query_service(self) -> None:
        store = InMemoryGraphStore()
        concept = GraphNode("PaperConcept", "bridge_attention", {"paper_status": "paper_explicit"})
        symbol = GraphNode("Symbol", "LearnableQueryExtractor.forward", {"kind": "method"})
        span = GraphNode("CodeSpan", "span-1", {"path": "models/policy.py"})
        store.upsert_node(concept)
        store.upsert_node(symbol)
        store.upsert_node(span)
        store.upsert_edge(
            GraphEdge(
                "STRUCTURALLY_SUPPORTED_BY",
                concept.ref,
                symbol.ref,
                {"status": "INFERRED", "confidence": "medium"},
            )
        )
        store.upsert_edge(
            GraphEdge(
                "SUPPORTED_BY",
                concept.ref,
                span.ref,
                {"status": "CONFIRMED", "confidence": "high"},
            )
        )

        service = DefaultGraphQueryService(store)
        alignments = service.alignment_edges_for_concept(
            GraphNodeRef("PaperConcept", "bridge_attention"),
            statuses={"CONFIRMED", "INFERRED"},
        )
        self.assertEqual(len(alignments), 2)

        subgraph = service.local_subgraph_for_node(GraphNodeRef("PaperConcept", "bridge_attention"), max_hops=1)
        self.assertEqual(len(subgraph.subgraph.nodes), 3)
        self.assertEqual(len(subgraph.subgraph.edges), 2)

    def test_python_ast_code_parser_extracts_symbols_imports_and_relations(self) -> None:
        parser = PythonAstCodeParser()
        source = """
from foo import Bar

class Policy(Bar):
    def forward(self):
        model = ActionHead()
        return model.predict()

def helper():
    return build_model()
"""
        parsed = parser.parse_file(Path("policy.py"), source)
        self.assertEqual(parsed.language, "python")
        self.assertEqual([symbol.name for symbol in parsed.symbols], ["Policy", "helper"])
        self.assertEqual(parsed.imports[0].module, "foo")
        relation_types = {(relation.relation_type, relation.target_name) for relation in parsed.relations}
        self.assertIn(("inherits", "Bar"), relation_types)
        self.assertIn(("calls", "ActionHead"), relation_types)
        self.assertIn(("instantiates", "ActionHead"), relation_types)
        self.assertIn(("calls", "model.predict"), relation_types)
        self.assertIn(("calls", "build_model"), relation_types)


if __name__ == "__main__":
    unittest.main()
