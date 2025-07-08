#!/usr/bin/env python3
"""
Dependency Graph System for Software Engineering Agent
Analyzes service dependencies, data flow, and architecture relationships
"""

import json
import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from pathlib import Path

logger = logging.getLogger(__name__)

class DependencyType(Enum):
    """Types of dependencies between services"""
    API_CALL = "api_call"           # Service A calls Service B's API
    DATA_FLOW = "data_flow"         # Data flows from A to B
    SHARED_DATABASE = "shared_db"   # Services share database tables
    EVENT_PUBLISH = "event_publish" # Service A publishes events to B
    AUTH_DEPENDENCY = "auth_dep"    # Service A depends on B for authentication
    STORAGE_DEPENDENCY = "storage_dep" # Service A stores data via B

class ServiceType(Enum):
    """Types of services in the platform"""
    AUTHENTICATION = "authentication"
    BUSINESS_LOGIC = "business_logic"
    DATA_STORAGE = "data_storage"
    CONTENT_GENERATION = "content_generation"
    USER_INTERFACE = "user_interface"
    GATEWAY = "gateway"

@dataclass
class ServiceNode:
    """Represents a service in the dependency graph"""
    name: str
    service_type: ServiceType
    description: str
    port: int
    database_models: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    data_entities: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    
@dataclass
class DependencyEdge:
    """Represents a dependency between services"""
    from_service: str
    to_service: str
    dependency_type: DependencyType
    description: str
    data_flow: Optional[str] = None
    endpoints_used: List[str] = field(default_factory=list)
    required: bool = True

class ServiceDependencyGraph:
    """Manages the dependency graph for service architecture"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.services: Dict[str, ServiceNode] = {}
        self.dependencies: List[DependencyEdge] = []
        
    def add_service(self, service: ServiceNode):
        """Add a service to the graph"""
        self.services[service.name] = service
        self.graph.add_node(service.name, **service.__dict__)
        logger.info(f"Added service: {service.name} ({service.service_type.value})")
    
    def add_dependency(self, dependency: DependencyEdge):
        """Add a dependency between services"""
        self.dependencies.append(dependency)
        self.graph.add_edge(
            dependency.from_service,
            dependency.to_service,
            dependency_type=dependency.dependency_type,
            description=dependency.description,
            data_flow=dependency.data_flow,
            endpoints_used=dependency.endpoints_used,
            required=dependency.required
        )
        logger.info(f"Added dependency: {dependency.from_service} -> {dependency.to_service} ({dependency.dependency_type.value})")
    
    def analyze_service_dependencies(self, service_name: str) -> Dict[str, Any]:
        """Analyze dependencies for a specific service"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found")
        
        # Get incoming dependencies (services this service depends on)
        incoming = list(self.graph.predecessors(service_name))
        
        # Get outgoing dependencies (services that depend on this service)
        outgoing = list(self.graph.successors(service_name))
        
        # Analyze dependency types
        dependency_analysis = {
            "service": service_name,
            "depends_on": [],
            "depended_by": [],
            "critical_dependencies": [],
            "optional_dependencies": [],
            "data_sources": [],
            "data_consumers": [],
            "auth_providers": [],
            "storage_providers": []
        }
        
        # Analyze incoming dependencies
        for dep_service in incoming:
            edge_data = self.graph.get_edge_data(dep_service, service_name)
            dep_type = edge_data['dependency_type']
            
            dependency_analysis["depends_on"].append({
                "service": dep_service,
                "type": dep_type.value,
                "description": edge_data.get('description', ''),
                "required": edge_data.get('required', True)
            })
            
            if edge_data.get('required', True):
                dependency_analysis["critical_dependencies"].append(dep_service)
            else:
                dependency_analysis["optional_dependencies"].append(dep_service)
            
            # Categorize by type
            if dep_type == DependencyType.DATA_FLOW:
                dependency_analysis["data_sources"].append(dep_service)
            elif dep_type == DependencyType.AUTH_DEPENDENCY:
                dependency_analysis["auth_providers"].append(dep_service)
            elif dep_type == DependencyType.STORAGE_DEPENDENCY:
                dependency_analysis["storage_providers"].append(dep_service)
        
        # Analyze outgoing dependencies
        for dep_service in outgoing:
            edge_data = self.graph.get_edge_data(service_name, dep_service)
            dependency_analysis["depended_by"].append({
                "service": dep_service,
                "type": edge_data['dependency_type'].value,
                "description": edge_data.get('description', '')
            })
            
            if edge_data['dependency_type'] == DependencyType.DATA_FLOW:
                dependency_analysis["data_consumers"].append(dep_service)
        
        return dependency_analysis
    
    def get_service_generation_order(self) -> List[str]:
        """Get the optimal order for generating services based on dependencies"""
        try:
            # Topological sort to get dependency order
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            logger.warning("Circular dependencies detected, using fallback ordering")
            # Fallback: order by service type priority
            type_priority = {
                ServiceType.AUTHENTICATION: 1,
                ServiceType.DATA_STORAGE: 2,
                ServiceType.BUSINESS_LOGIC: 3,
                ServiceType.CONTENT_GENERATION: 4,
                ServiceType.USER_INTERFACE: 5,
                ServiceType.GATEWAY: 6
            }
            
            services = list(self.services.values())
            services.sort(key=lambda s: type_priority.get(s.service_type, 999))
            return [s.name for s in services]
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the graph"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                logger.warning(f"Detected {len(cycles)} circular dependencies: {cycles}")
            return cycles
        except nx.NetworkXError:
            return []
    
    def get_critical_path(self) -> List[str]:
        """Get the critical path through the service dependencies"""
        # Find services with no dependencies (sources)
        sources = [node for node in self.graph.nodes() if self.graph.in_degree(node) == 0]
        
        # Find services with no dependents (sinks)
        sinks = [node for node in self.graph.nodes() if self.graph.out_degree(node) == 0]
        
        if not sources or not sinks:
            return list(self.services.keys())
        
        # Find longest path from any source to any sink
        longest_path = []
        for source in sources:
            for sink in sinks:
                try:
                    path = nx.shortest_path(self.graph, source, sink)
                    if len(path) > len(longest_path):
                        longest_path = path
                except nx.NetworkXNoPath:
                    continue
        
        return longest_path
    
    def generate_service_interfaces(self, service_name: str) -> Dict[str, Any]:
        """Generate interface specifications for a service based on its dependencies"""
        analysis = self.analyze_service_dependencies(service_name)
        service = self.services[service_name]
        
        interfaces = {
            "service_name": service_name,
            "required_clients": [],
            "exposed_endpoints": [],
            "data_models": [],
            "configuration": {
                "dependencies": {},
                "database": {},
                "external_apis": {}
            }
        }
        
        # Generate client interfaces for services this depends on
        for dep in analysis["depends_on"]:
            dep_service = dep["service"]
            dep_type = dep["type"]
            
            if dep_type in ["api_call", "auth_dep", "storage_dep"]:
                client_config = {
                    "service": dep_service,
                    "base_url": f"${{oc.env:{dep_service.upper().replace('-', '_')}_URL,http://localhost:{self.services[dep_service].port}}}",
                    "timeout": 30,
                    "retry_attempts": 3
                }
                interfaces["required_clients"].append(client_config)
                interfaces["configuration"]["dependencies"][dep_service] = client_config
        
        # Generate endpoint specifications
        for endpoint in service.api_endpoints:
            endpoint_spec = {
                "path": endpoint,
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "authentication_required": service.service_type != ServiceType.AUTHENTICATION,
                "rate_limiting": True
            }
            interfaces["exposed_endpoints"].append(endpoint_spec)
        
        # Generate data model specifications
        interfaces["data_models"] = service.database_models
        
        # Database configuration
        if service.database_models:
            interfaces["configuration"]["database"] = {
                "url": "${oc.env:DATABASE_URL,postgresql://user:pass@localhost/db}",
                "pool_size": 10,
                "echo": False
            }
        
        return interfaces
    
    def export_graph(self, format: str = "json") -> str:
        """Export the dependency graph in various formats"""
        if format == "json":
            graph_data = {
                "services": {name: service.__dict__ for name, service in self.services.items()},
                "dependencies": [
                    {
                        "from": dep.from_service,
                        "to": dep.to_service,
                        "type": dep.dependency_type.value,
                        "description": dep.description,
                        "required": dep.required
                    }
                    for dep in self.dependencies
                ]
            }
            return json.dumps(graph_data, indent=2, default=str)
        
        elif format == "dot":
            # Generate Graphviz DOT format
            dot_lines = ["digraph ServiceDependencies {"]
            dot_lines.append("  rankdir=LR;")
            dot_lines.append("  node [shape=box];")
            
            # Add nodes
            for service in self.services.values():
                color = {
                    ServiceType.AUTHENTICATION: "lightblue",
                    ServiceType.DATA_STORAGE: "lightgreen",
                    ServiceType.BUSINESS_LOGIC: "lightyellow",
                    ServiceType.CONTENT_GENERATION: "lightpink",
                    ServiceType.USER_INTERFACE: "lightgray",
                    ServiceType.GATEWAY: "lightcoral"
                }.get(service.service_type, "white")
                
                dot_lines.append(f'  "{service.name}" [fillcolor="{color}", style=filled];')
            
            # Add edges
            for dep in self.dependencies:
                style = "solid" if dep.required else "dashed"
                dot_lines.append(f'  "{dep.from_service}" -> "{dep.to_service}" [label="{dep.dependency_type.value}", style="{style}"];')
            
            dot_lines.append("}")
            return "\n".join(dot_lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

def build_course_creator_graph() -> ServiceDependencyGraph:
    """Build the dependency graph for the course creator platform"""
    graph = ServiceDependencyGraph()
    
    # Define services
    user_management = ServiceNode(
        name="user-management",
        service_type=ServiceType.AUTHENTICATION,
        description="User registration, authentication, and profile management",
        port=8000,
        database_models=["User", "Role", "Permission", "UserSession"],
        api_endpoints=["/auth/login", "/auth/register", "/users/profile", "/users/{id}", "/roles"],
        responsibilities=["User authentication", "Authorization", "Profile management", "Role-based access control"]
    )
    
    course_generator = ServiceNode(
        name="course-generator",
        service_type=ServiceType.CONTENT_GENERATION,
        description="AI-powered course content generation",
        port=8001,
        database_models=["CourseTemplate", "GenerationJob", "ContentPrompt"],
        api_endpoints=["/generate/course", "/templates", "/jobs/{id}"],
        external_dependencies=["anthropic-api"],
        responsibilities=["Course content generation", "Template management", "AI prompt processing"]
    )
    
    course_management = ServiceNode(
        name="course-management",
        service_type=ServiceType.BUSINESS_LOGIC,
        description="Course lifecycle and enrollment management",
        port=8004,
        database_models=["Course", "CourseModule", "CourseLesson", "Enrollment", "Progress"],
        api_endpoints=["/courses", "/courses/{id}", "/enrollments", "/progress"],
        responsibilities=["Course CRUD operations", "Enrollment management", "Progress tracking"]
    )
    
    content_storage = ServiceNode(
        name="content-storage",
        service_type=ServiceType.DATA_STORAGE,
        description="File storage and content management",
        port=8003,
        database_models=["ContentFile", "MediaAsset", "StorageMetadata"],
        api_endpoints=["/upload", "/files/{id}", "/media", "/storage/metadata"],
        responsibilities=["File upload/download", "Media processing", "Storage management"]
    )
    
    # Add services to graph
    for service in [user_management, course_generator, course_management, content_storage]:
        graph.add_service(service)
    
    # Define dependencies
    dependencies = [
        # Course management depends on user management for authentication
        DependencyEdge(
            from_service="course-management",
            to_service="user-management",
            dependency_type=DependencyType.AUTH_DEPENDENCY,
            description="Requires user authentication for course operations",
            endpoints_used=["/auth/verify", "/users/{id}"]
        ),
        
        # Course generator depends on user management for authentication
        DependencyEdge(
            from_service="course-generator",
            to_service="user-management",
            dependency_type=DependencyType.AUTH_DEPENDENCY,
            description="Requires authentication for course generation",
            endpoints_used=["/auth/verify"]
        ),
        
        # Course management uses course generator for content creation
        DependencyEdge(
            from_service="course-management",
            to_service="course-generator",
            dependency_type=DependencyType.API_CALL,
            description="Calls generator service to create course content",
            endpoints_used=["/generate/course", "/templates"]
        ),
        
        # Course management uses content storage for media files
        DependencyEdge(
            from_service="course-management",
            to_service="content-storage",
            dependency_type=DependencyType.STORAGE_DEPENDENCY,
            description="Stores course materials and media files",
            endpoints_used=["/upload", "/files/{id}"]
        ),
        
        # Course generator uses content storage for generated content
        DependencyEdge(
            from_service="course-generator",
            to_service="content-storage",
            dependency_type=DependencyType.STORAGE_DEPENDENCY,
            description="Stores generated course content and assets",
            endpoints_used=["/upload", "/media"]
        ),
        
        # Content storage optionally depends on user management for access control
        DependencyEdge(
            from_service="content-storage",
            to_service="user-management",
            dependency_type=DependencyType.AUTH_DEPENDENCY,
            description="Optional authentication for file access control",
            endpoints_used=["/auth/verify"],
            required=False
        ),
        
    ]
    
    # Add dependencies to graph
    for dep in dependencies:
        graph.add_dependency(dep)
    
    return graph