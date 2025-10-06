"""
Domain Entities Package

Contains core business entities for the knowledge graph.
"""

from domain.entities.node import Node, NodeType
from domain.entities.edge import Edge, EdgeType

__all__ = ['Node', 'NodeType', 'Edge', 'EdgeType']
