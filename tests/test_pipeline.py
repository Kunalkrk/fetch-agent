"""Placeholder pipeline tests.

Fill in once parse_retrieve / draft_act / verify are implemented (Blocks 2-4).
For the MVP, at least cover:
- the graph compiles and has the expected node order
- verify() correctly flags a bad draft as failing
"""

from src.graph import build_graph


def test_graph_compiles():
    graph = build_graph()
    assert graph is not None
