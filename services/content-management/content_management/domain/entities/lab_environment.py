"""
Lab Environment Entity - Domain Layer
Single Responsibility: Lab environment-specific business logic and validation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from content_management.domain.entities.base_content import BaseContent, ContentType


class EnvironmentType(Enum):
    """
    Lab environment technology stack classification.

    Comprehensive enumeration of supported programming languages and
    development environments for hands-on coding labs and interactive
    learning experiences.

    Environment Categories:
    - **PYTHON**: Python programming environment with pip package management
    - **JAVASCRIPT**: JavaScript/Node.js environment with npm package management
    - **JAVA**: Java development environment with Maven/Gradle build tools
    - **CPP**: C++ development environment with GCC/Clang compilers
    - **R**: R statistical computing environment with CRAN packages
    - **JUPYTER**: Jupyter notebook environment for interactive data science
    - **DOCKER**: Containerized environments with Docker infrastructure
    - **WEB**: Full-stack web development with HTML/CSS/JavaScript
    - **DATABASE**: Database management with SQL/NoSQL systems
    - **CLOUD**: Cloud platform environments (AWS, Azure, GCP)

    Educational Benefits:
    - Technology-specific environment provisioning
    - Appropriate tooling and dependencies per language
    - Realistic development environment simulation
    - Industry-standard technology stack exposure
    """
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    R = "r"
    JUPYTER = "jupyter"
    DOCKER = "docker"
    WEB = "web"
    DATABASE = "database"
    CLOUD = "cloud"


class ResourceRequirement:
    """
    Lab environment resource requirements specification.

    BUSINESS REQUIREMENT:
    Lab environments require explicit resource allocation (CPU, memory, disk)
    to ensure consistent performance, prevent resource contention, and
    support fair access in multi-user educational environments.

    TECHNICAL DESIGN:
    Specifies minimum resource requirements for lab provisioning including
    compute resources (CPU cores), memory allocation, storage capacity,
    network connectivity, and specialized hardware (GPU) needs.

    RESOURCE PLANNING:
    - Enables capacity planning for infrastructure
    - Prevents over-subscription of shared resources
    - Ensures consistent student experience
    - Supports SLA compliance and performance guarantees
    """

    def __init__(
        self,
        cpu_cores: int = 1,
        memory_gb: float = 1.0,
        disk_gb: float = 10.0,
        network_required: bool = True,
        gpu_required: bool = False
    ):
        self.cpu_cores = cpu_cores
        self.memory_gb = memory_gb
        self.disk_gb = disk_gb
        self.network_required = network_required
        self.gpu_required = gpu_required
        
        self.validate()
    
    def validate(self) -> None:
        """Validate resource requirements"""
        if self.cpu_cores < 1:
            raise ValueError("CPU cores must be at least 1")
        if self.memory_gb <= 0:
            raise ValueError("Memory must be positive")
        if self.disk_gb <= 0:
            raise ValueError("Disk space must be positive")
    
    def meets_minimum_requirements(self, available_cpu: int, available_memory: float, 
                                  available_disk: float) -> bool:
        """Check if available resources meet requirements"""
        return (
            available_cpu >= self.cpu_cores and
            available_memory >= self.memory_gb and
            available_disk >= self.disk_gb
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_cores": self.cpu_cores,
            "memory_gb": self.memory_gb,
            "disk_gb": self.disk_gb,
            "network_required": self.network_required,
            "gpu_required": self.gpu_required
        }


class LabTool:
    """
    Lab tool specification with version control and configuration.

    BUSINESS REQUIREMENT:
    Educational labs require specific software tools and versions for
    consistent learning experiences, reproducible environments, and
    alignment with industry practices and course learning objectives.

    EDUCATIONAL DESIGN:
    Provides explicit tool specification including version pinning for
    reproducibility, installation commands for automation, and
    configuration for proper tool setup in educational contexts.

    VERSION MANAGEMENT:
    - Explicit version specification prevents compatibility issues
    - Reproducible environments across all student instances
    - Industry-standard tool exposure for career preparation
    - Seamless updates when new versions are required
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        installation_command: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.version = version
        self.description = description or ""
        self.installation_command = installation_command
        self.configuration = configuration or {}
        
        self.validate()
    
    def validate(self) -> None:
        """Validate tool"""
        if not self.name:
            raise ValueError("Tool name is required")
        if not self.version:
            raise ValueError("Tool version is required")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "installation_command": self.installation_command,
            "configuration": self.configuration
        }


class Dataset:
    """
    Educational dataset specification for data-driven labs.

    BUSINESS REQUIREMENT:
    Data science and analytics labs require curated datasets with clear
    licensing, proper attribution, and educational relevance for effective
    hands-on learning in data analysis and machine learning contexts.

    EDUCATIONAL DESIGN:
    Specifies dataset metadata including format, size for resource planning,
    source attribution, and licensing information for legal compliance and
    ethical data usage education.

    DATA GOVERNANCE:
    - Clear licensing for legal compliance
    - Source attribution for academic integrity
    - Size specification for resource allocation
    - Format specification for tool compatibility
    """

    def __init__(
        self,
        name: str,
        description: str,
        format: str,
        size_mb: Optional[float] = None,
        source_url: Optional[str] = None,
        license: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.format = format
        self.size_mb = size_mb
        self.source_url = source_url
        self.license = license
        
        self.validate()
    
    def validate(self) -> None:
        """Validate dataset"""
        if not self.name:
            raise ValueError("Dataset name is required")
        if not self.description:
            raise ValueError("Dataset description is required")
        if not self.format:
            raise ValueError("Dataset format is required")
        if self.size_mb is not None and self.size_mb <= 0:
            raise ValueError("Dataset size must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "format": self.format,
            "size_mb": self.size_mb,
            "source_url": self.source_url,
            "license": self.license
        }


class SetupScript:
    """
    Lab environment setup automation script.

    BUSINESS REQUIREMENT:
    Complex lab environments require automated setup scripts for consistent
    configuration, efficient provisioning, and reproducible environment
    initialization across all student lab instances.

    TECHNICAL DESIGN:
    Specifies setup scripts with execution ordering for dependency management,
    prerequisite checking, and comprehensive configuration automation to
    minimize manual setup and ensure environment consistency.

    AUTOMATION BENEFITS:
    - Consistent environment configuration
    - Reduced setup time and errors
    - Dependency management through ordered execution
    - Scalable provisioning for large student populations
    """

    def __init__(
        self,
        script_name: str,
        script_content: str,
        execution_order: int = 1,
        description: Optional[str] = None,
        requirements: Optional[List[str]] = None
    ):
        self.script_name = script_name
        self.script_content = script_content
        self.execution_order = execution_order
        self.description = description or ""
        self.requirements = requirements or []
        
        self.validate()
    
    def validate(self) -> None:
        """Validate setup script"""
        if not self.script_name:
            raise ValueError("Script name is required")
        if not self.script_content:
            raise ValueError("Script content is required")
        if self.execution_order < 1:
            raise ValueError("Execution order must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "script_name": self.script_name,
            "script_content": self.script_content,
            "execution_order": self.execution_order,
            "description": self.description,
            "requirements": self.requirements
        }


class LabEnvironment(BaseContent):
    """
    Lab Environment domain entity - comprehensive interactive coding environment.

    BUSINESS REQUIREMENT:
    Educational programming labs require complete environment specification including
    technology stack, tool provisioning, dataset integration, resource allocation,
    and automated setup for consistent, reproducible hands-on learning experiences.

    EDUCATIONAL METHODOLOGY:
    Implements experiential learning through hands-on coding in realistic development
    environments, supporting constructivist pedagogy with active learning, immediate
    feedback, and authentic technology stack exposure for career preparation.

    TECHNICAL IMPLEMENTATION:
    - Extends BaseContent for lifecycle management
    - Aggregates LabTool, Dataset, SetupScript value objects
    - Uses ResourceRequirement for capacity planning
    - Supports multiple environment types (Python, Java, Docker, etc.)
    - Provides comprehensive environment validation and completeness checking

    DOMAIN OPERATIONS:
    - Tool management (add, remove, version checking)
    - Dataset management (add, remove, size calculation)
    - Setup script management (add, remove, execution ordering)
    - Resource requirement specification
    - Access instructions and documentation
    - Environment validation and completeness checking

    INFRASTRUCTURE INTEGRATION:
    - Docker base image specification for containerization
    - Resource allocation for capacity planning
    - Network requirements for cloud labs
    - GPU requirements for ML/AI workloads
    - Automated provisioning through setup scripts
    """

    def __init__(
        self,
        title: str,
        course_id: str,
        created_by: str,
        environment_type: EnvironmentType,
        base_image: str,
        id: Optional[str] = None,
        description: Optional[str] = None,
        tools: Optional[List[LabTool]] = None,
        datasets: Optional[List[Dataset]] = None,
        setup_scripts: Optional[List[SetupScript]] = None,
        access_instructions: Optional[str] = None,
        estimated_setup_time_minutes: Optional[int] = None,
        resource_requirements: Optional[ResourceRequirement] = None,
        **kwargs
    ):
        # Initialize base content
        super().__init__(
            title=title,
            course_id=course_id,
            created_by=created_by,
            id=id,
            description=description,
            **kwargs
        )
        
        # Lab environment-specific attributes
        self.environment_type = environment_type
        self.base_image = base_image
        self.tools = tools or []
        self.datasets = datasets or []
        self.setup_scripts = setup_scripts or []
        self.access_instructions = access_instructions or ""
        self.estimated_setup_time_minutes = estimated_setup_time_minutes
        self.resource_requirements = resource_requirements or ResourceRequirement()
        
        # Additional validation
        self._validate_lab_environment()
    
    def get_content_type(self) -> ContentType:
        """Get content type"""
        return ContentType.LAB_ENVIRONMENT
    
    def _validate_lab_environment(self) -> None:
        """Validate lab environment-specific data"""
        if not self.base_image:
            raise ValueError("Base image is required")
        if self.estimated_setup_time_minutes is not None and self.estimated_setup_time_minutes <= 0:
            raise ValueError("Estimated setup time must be positive")
    
    def add_tool(self, tool: LabTool) -> None:
        """Add tool to environment"""
        # Check for duplicate tools
        existing_tools = [(t.name, t.version) for t in self.tools]
        if (tool.name, tool.version) in existing_tools:
            raise ValueError(f"Tool {tool.name} v{tool.version} already exists")
        
        self.tools.append(tool)
        self._mark_updated()
    
    def remove_tool(self, tool_name: str, version: Optional[str] = None) -> bool:
        """Remove tool from environment"""
        for i, tool in enumerate(self.tools):
            if tool.name == tool_name and (version is None or tool.version == version):
                del self.tools[i]
                self._mark_updated()
                return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[LabTool]:
        """Get tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def has_tool(self, tool_name: str, version: Optional[str] = None) -> bool:
        """Check if environment has specific tool"""
        for tool in self.tools:
            if tool.name == tool_name and (version is None or tool.version == version):
                return True
        return False
    
    def add_dataset(self, dataset: Dataset) -> None:
        """Add dataset to environment"""
        # Check for duplicate datasets
        existing_datasets = [d.name for d in self.datasets]
        if dataset.name in existing_datasets:
            raise ValueError(f"Dataset {dataset.name} already exists")
        
        self.datasets.append(dataset)
        self._mark_updated()
    
    def remove_dataset(self, dataset_name: str) -> bool:
        """Remove dataset from environment"""
        for i, dataset in enumerate(self.datasets):
            if dataset.name == dataset_name:
                del self.datasets[i]
                self._mark_updated()
                return True
        return False
    
    def get_dataset(self, dataset_name: str) -> Optional[Dataset]:
        """Get dataset by name"""
        for dataset in self.datasets:
            if dataset.name == dataset_name:
                return dataset
        return None
    
    def add_setup_script(self, script: SetupScript) -> None:
        """Add setup script to environment"""
        # Check for duplicate script names
        existing_names = [s.script_name for s in self.setup_scripts]
        if script.script_name in existing_names:
            raise ValueError(f"Setup script {script.script_name} already exists")
        
        self.setup_scripts.append(script)
        # Sort scripts by execution order
        self.setup_scripts.sort(key=lambda x: x.execution_order)
        self._mark_updated()
    
    def remove_setup_script(self, script_name: str) -> bool:
        """Remove setup script"""
        for i, script in enumerate(self.setup_scripts):
            if script.script_name == script_name:
                del self.setup_scripts[i]
                self._mark_updated()
                return True
        return False
    
    def get_setup_script(self, script_name: str) -> Optional[SetupScript]:
        """Get setup script by name"""
        for script in self.setup_scripts:
            if script.script_name == script_name:
                return script
        return None
    
    def update_resource_requirements(self, requirements: ResourceRequirement) -> None:
        """Update resource requirements"""
        self.resource_requirements = requirements
        self._mark_updated()
    
    def set_access_instructions(self, instructions: str) -> None:
        """Set access instructions"""
        self.access_instructions = instructions
        self._mark_updated()
    
    def set_estimated_setup_time(self, minutes: int) -> None:
        """Set estimated setup time"""
        if minutes <= 0:
            raise ValueError("Setup time must be positive")
        self.estimated_setup_time_minutes = minutes
        self._mark_updated()
    
    def get_total_dataset_size(self) -> float:
        """Calculate total dataset size in MB"""
        return sum(
            dataset.size_mb for dataset in self.datasets 
            if dataset.size_mb is not None
        )
    
    def get_tools_count(self) -> int:
        """Get number of tools"""
        return len(self.tools)
    
    def get_datasets_count(self) -> int:
        """Get number of datasets"""
        return len(self.datasets)
    
    def get_setup_scripts_count(self) -> int:
        """Get number of setup scripts"""
        return len(self.setup_scripts)
    
    def is_python_environment(self) -> bool:
        """Check if this is a Python environment"""
        return self.environment_type == EnvironmentType.PYTHON
    
    def is_jupyter_environment(self) -> bool:
        """Check if this is a Jupyter environment"""
        return self.environment_type == EnvironmentType.JUPYTER
    
    def is_docker_environment(self) -> bool:
        """Check if this is a Docker environment"""
        return self.environment_type == EnvironmentType.DOCKER
    
    def requires_gpu(self) -> bool:
        """Check if environment requires GPU"""
        return self.resource_requirements.gpu_required
    
    def has_datasets(self) -> bool:
        """Check if environment has datasets"""
        return bool(self.datasets)
    
    def has_setup_scripts(self) -> bool:
        """Check if environment has setup scripts"""
        return bool(self.setup_scripts)
    
    def is_complete(self) -> bool:
        """Check if lab environment definition is complete"""
        return all([
            self.title,
            self.description,
            self.base_image,
            self.access_instructions,
            self.estimated_setup_time_minutes is not None
        ])
    
    def can_run_on_resources(self, available_cpu: int, available_memory: float, 
                           available_disk: float) -> bool:
        """Check if environment can run on available resources"""
        return self.resource_requirements.meets_minimum_requirements(
            available_cpu, available_memory, available_disk
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "environment_type": self.environment_type.value,
            "base_image": self.base_image,
            "tools": [tool.to_dict() for tool in self.tools],
            "tools_count": self.get_tools_count(),
            "datasets": [dataset.to_dict() for dataset in self.datasets],
            "datasets_count": self.get_datasets_count(),
            "total_dataset_size_mb": self.get_total_dataset_size(),
            "setup_scripts": [script.to_dict() for script in self.setup_scripts],
            "setup_scripts_count": self.get_setup_scripts_count(),
            "access_instructions": self.access_instructions,
            "estimated_setup_time_minutes": self.estimated_setup_time_minutes,
            "resource_requirements": self.resource_requirements.to_dict(),
            "is_python_environment": self.is_python_environment(),
            "is_jupyter_environment": self.is_jupyter_environment(),
            "is_docker_environment": self.is_docker_environment(),
            "requires_gpu": self.requires_gpu(),
            "has_datasets": self.has_datasets(),
            "has_setup_scripts": self.has_setup_scripts(),
            "is_complete": self.is_complete()
        })
        return base_dict