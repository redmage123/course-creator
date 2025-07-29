"""
Lab Environment Entity - Domain Layer
Single Responsibility: Lab environment-specific business logic and validation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .base_content import BaseContent, ContentType


class EnvironmentType(Enum):
    """Environment type enumeration"""
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
    """Resource requirement value object"""
    
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
    """Lab tool value object"""
    
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
    """Dataset value object"""
    
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
    """Setup script value object"""
    
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
    Lab Environment domain entity following SOLID principles
    Single Responsibility: Lab environment-specific business logic
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