"""
Domain Entities Package

Contains core business entities for the knowledge graph.
"""

from knowledge_graph_service.domain.entities.node import Node, NodeType
from knowledge_graph_service.domain.entities.edge import Edge, EdgeType

__all__ = ['Node', 'NodeType', 'Edge', 'EdgeType']
