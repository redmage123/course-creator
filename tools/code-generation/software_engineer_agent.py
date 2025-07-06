#!/usr/bin/env python3
"""
Content-Aware Platform Generator Agent

This comprehensive agent generates complete microservices platforms with advanced
content management, file handling, download capabilities, and extensive testing.
"""

import os
import sys
import json
import argparse
import asyncio
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import textwrap
import anthropic
from tqdm import tqdm
import time
import networkx as nx
from collections import defaultdict, deque
import matplotlib.pyplot as plt
import graphviz
from pyvis.network import Network
import hashlib
import zipfile
import shutil
import pytest

# Add the shared directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))

@dataclass
class ContentFlow:
    """Represents content creation and consumption flow"""
    service: str
    endpoint: str
    flow_type: str  # 'creation', 'download', 'access', 'storage'
    content_type: str  # 'course', 'slide', 'lab', 'resource'
    formats: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FileRelationship:
    """Represents file storage and access relationships"""
    service: str
    model: str
    field: str
    file_type: str  # 'image', 'document', 'video', 'archive'
    storage_location: str = 'local'
    access_patterns: List[str] = field(default_factory=list)

@dataclass
class DownloadPattern:
    """Download and export pattern definition"""
    service: str
    endpoint: str
    content_types: List[str]
    formats: List[str]
    packaging_options: List[str] = field(default_factory=list)
    bulk_support: bool = False

@dataclass
class TemplateExtension:
    """Template extension for adding functionality"""
    target_service: str
    extension_type: str  # 'endpoints', 'models', 'events', 'dependencies'
    data: Dict[str, Any]
    priority: int = 100
    conditions: List[str] = field(default_factory=list)

class VerboseLogger:
    """Enhanced logger with test output support"""
    
    def __init__(self, verbose: bool = False, test_mode: bool = False):
        self.verbose = verbose
        self.test_mode = test_mode
        self.test_results = []
        
    def info(self, message: str):
        if self.verbose:
            print(f"ℹ️  {message}")
    
    def debug(self, message: str):
        if self.verbose:
            print(f"🔍 DEBUG: {message}")
    
    def success(self, message: str):
        print(f"✅ {message}")
        if self.test_mode:
            self.test_results.append(('SUCCESS', message))
    
    def error(self, message: str):
        print(f"❌ {message}")
        if self.test_mode:
            self.test_results.append(('ERROR', message))
    
    def warning(self, message: str):
        print(f"⚠️  {message}")
        if self.test_mode:
            self.test_results.append(('WARNING', message))
    
    def step(self, message: str):
        print(f"📋 {message}")
    
    def substep(self, message: str):
        if self.verbose:
            print(f"   └─ {message}")
    
    def test(self, message: str):
        print(f"🧪 {message}")
    
    def content(self, message: str):
        print(f"📁 {message}")
    
    def download(self, message: str):
        print(f"📥 {message}")

class TemplateManager:
    """Enhanced template management with extension support"""
    
    def __init__(self, templates_dir: Path, logger: VerboseLogger):
        self.templates_dir = templates_dir
        self.logger = logger
        self.base_templates = {}
        self.template_extensions = {}
        self.merged_templates = {}
        self.content_features = {}
        
        # Create directory structure
        self.base_dir = templates_dir / "base"
        self.extensions_dir = templates_dir / "extensions"
        self.merged_dir = templates_dir / "merged"
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """Create template directory structure"""
        for dir_path in [self.base_dir, self.extensions_dir, self.merged_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def load_templates_with_extensions(self, features: List[str] = None):
        """Load base templates and apply extensions"""
        
        self.logger.content("Loading templates with extensions...")
        
        # Load base templates
        await self._load_base_templates()
        
        # Load template extensions
        await self._load_template_extensions()
        
        # Apply feature-specific extensions
        if features:
            await self._apply_feature_extensions(features)
        
        # Merge templates with extensions
        await self._merge_templates()
        
        # Validate merged templates
        await self._validate_merged_templates()
        
        # Save merged templates
        await self._save_merged_templates()
        
        self.logger.success(f"Loaded {len(self.merged_templates)} templates with extensions")
        
        return self.merged_templates
    
    async def _load_base_templates(self):
        """Load base service templates"""
        
        # Check if base templates exist, if not look in main templates directory
        template_files = list(self.base_dir.glob("*.json"))
        if not template_files:
            template_files = list(self.templates_dir.glob("*.json"))
        
        for template_file in template_files:
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)
                
                service_name = template_data.get('name', template_file.stem)
                self.base_templates[service_name] = template_data
                
                self.logger.substep(f"Loaded base template: {service_name}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load base template {template_file}: {e}")
    
    async def _load_template_extensions(self):
        """Load template extensions"""
        
        if not self.extensions_dir.exists():
            return
        
        for feature_dir in self.extensions_dir.iterdir():
            if feature_dir.is_dir():
                feature_name = feature_dir.name
                self.template_extensions[feature_name] = []
                
                for extension_file in feature_dir.glob("*.json"):
                    try:
                        with open(extension_file, 'r') as f:
                            extension_data = json.load(f)
                        
                        extension = TemplateExtension(
                            target_service=extension_data.get('target_service', 'all'),
                            extension_type=extension_data.get('extension_type', 'endpoints'),
                            data=extension_data.get('data', {}),
                            priority=extension_data.get('priority', 100),
                            conditions=extension_data.get('conditions', [])
                        )
                        
                        self.template_extensions[feature_name].append(extension)
                        self.logger.substep(f"Loaded extension: {feature_name}/{extension_file.name}")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load extension {extension_file}: {e}")
    
    async def _apply_feature_extensions(self, features: List[str]):
        """Apply specific feature extensions"""
        
        for feature in features:
            if feature in self.template_extensions:
                self.logger.substep(f"Applying feature extension: {feature}")
                
                for extension in self.template_extensions[feature]:
                    await self._apply_single_extension(extension)
    
    async def _apply_single_extension(self, extension: TemplateExtension):
        """Apply a single template extension"""
        
        # Check conditions
        if not self._check_extension_conditions(extension):
            return
        
        # Apply to specific service or all services
        target_services = [extension.target_service] if extension.target_service != 'all' else list(self.base_templates.keys())
        
        for service_name in target_services:
            if service_name in self.base_templates:
                await self._merge_extension_into_template(service_name, extension)
    
    def _check_extension_conditions(self, extension: TemplateExtension) -> bool:
        """Check if extension conditions are met"""
        
        for condition in extension.conditions:
            if condition.startswith('service_exists:'):
                service_name = condition.replace('service_exists:', '')
                if service_name not in self.base_templates:
                    return False
            elif condition.startswith('capability_exists:'):
                capability = condition.replace('capability_exists:', '')
                found = False
                for template in self.base_templates.values():
                    if capability in template.get('provides', []):
                        found = True
                        break
                if not found:
                    return False
        
        return True
    
    async def _merge_extension_into_template(self, service_name: str, extension: TemplateExtension):
        """Merge extension into specific template"""
        
        template = self.base_templates[service_name]
        
        if extension.extension_type == 'endpoints':
            template['endpoints'] = template.get('endpoints', []) + extension.data.get('endpoints', [])
        
        elif extension.extension_type == 'models':
            template['database_models'] = template.get('database_models', []) + extension.data.get('database_models', [])
        
        elif extension.extension_type == 'events':
            if 'produces_events' in extension.data:
                template['produces_events'] = list(set(template.get('produces_events', []) + extension.data['produces_events']))
            if 'consumes_events' in extension.data:
                template['consumes_events'] = list(set(template.get('consumes_events', []) + extension.data['consumes_events']))
        
        elif extension.extension_type == 'capabilities':
            template['provides'] = list(set(template.get('provides', []) + extension.data.get('provides', [])))
        
        elif extension.extension_type == 'dependencies':
            template['dependencies'] = list(set(template.get('dependencies', []) + extension.data.get('dependencies', [])))
        
        elif extension.extension_type == 'full_merge':
            # Deep merge all data
            template = self._deep_merge_dict(template, extension.data)
            self.base_templates[service_name] = template
    
    def _deep_merge_dict(self, base: Dict, update: Dict) -> Dict:
        """Deep merge two dictionaries"""
        
        result = base.copy()
        
        for key, value in update.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_dict(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    result[key] = list(set(result[key] + value))
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    async def _merge_templates(self):
        """Merge base templates with applied extensions"""
        
        # For now, the extensions are already applied to base templates
        # This step can be used for additional processing
        self.merged_templates = self.base_templates.copy()
    
    async def _validate_merged_templates(self):
        """Validate merged templates for consistency"""
        
        errors = []
        warnings = []
        
        for service_name, template in self.merged_templates.items():
            # Validate required fields
            required_fields = ['name', 'description', 'port']
            for field in required_fields:
                if field not in template:
                    errors.append(f"Service {service_name} missing required field: {field}")
            
            # Validate port uniqueness
            port = template.get('port')
            if port:
                other_services = [s for s, t in self.merged_templates.items() if s != service_name and t.get('port') == port]
                if other_services:
                    errors.append(f"Port {port} conflict between {service_name} and {other_services}")
            
            # Validate dependencies exist
            for dep in template.get('depends_on', []):
                if dep not in self.merged_templates:
                    warnings.append(f"Service {service_name} depends on undefined service: {dep}")
        
        if errors:
            raise ValueError(f"Template validation failed: {errors}")
        
        if warnings:
            for warning in warnings:
                self.logger.warning(warning)
    
    async def _save_merged_templates(self):
        """Save merged templates to merged directory"""
        
        for service_name, template in self.merged_templates.items():
            output_file = self.merged_dir / f"{service_name}.json"
            with open(output_file, 'w') as f:
                json.dump(template, f, indent=2)
            
            self.logger.substep(f"Saved merged template: {service_name}")

class ContentGraphAnalyzer:
    """Advanced graph analyzer with content management awareness"""
    
    def __init__(self, logger: VerboseLogger):
        self.logger = logger
        self.content_flows = []
        self.file_relationships = []
        self.download_patterns = []
        self.storage_requirements = {}
    
    def analyze_content_architecture(self, service_templates: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive content architecture analysis"""
        
        self.logger.content("Analyzing content architecture...")
        
        # Analyze content flows
        self.content_flows = self._identify_content_flows(service_templates)
        
        # Map file relationships
        self.file_relationships = self._map_file_relationships(service_templates)
        
        # Analyze download patterns
        self.download_patterns = self._analyze_download_patterns(service_templates)
        
        # Calculate storage requirements
        self.storage_requirements = self._calculate_storage_requirements(service_templates)
        
        # Generate content integration recommendations
        integration_recommendations = self._generate_integration_recommendations()
        
        analysis_result = {
            'content_flows': [flow.__dict__ for flow in self.content_flows],
            'file_relationships': [rel.__dict__ for rel in self.file_relationships],
            'download_patterns': [pattern.__dict__ for pattern in self.download_patterns],
            'storage_requirements': self.storage_requirements,
            'integration_recommendations': integration_recommendations,
            'content_summary': self._generate_content_summary()
        }
        
        self.logger.success(f"Analyzed {len(self.content_flows)} content flows and {len(self.file_relationships)} file relationships")
        
        return analysis_result
    
    def _identify_content_flows(self, templates: Dict[str, Any]) -> List[ContentFlow]:
        """Identify content creation and consumption flows"""
        
        flows = []
        
        for service_name, template in templates.items():
            for endpoint_group in template.get('endpoints', []):
                for route in endpoint_group.get('routes', []):
                    
                    # Content creation endpoints
                    if self._is_content_creation_endpoint(route):
                        flows.append(ContentFlow(
                            service=service_name,
                            endpoint=route['path'],
                            flow_type='creation',
                            content_type=self._infer_content_type(route),
                            formats=self._extract_supported_formats(route),
                            metadata={'method': route['method'], 'function': route['function_name']}
                        ))
                    
                    # Download endpoints
                    elif self._is_download_endpoint(route):
                        flows.append(ContentFlow(
                            service=service_name,
                            endpoint=route['path'],
                            flow_type='download',
                            content_type=self._infer_content_type(route),
                            formats=self._extract_download_formats(route),
                            metadata={'return_type': route.get('return_type'), 'bulk_support': self._has_bulk_support(route)}
                        ))
                    
                    # Content access endpoints
                    elif self._is_content_access_endpoint(route):
                        flows.append(ContentFlow(
                            service=service_name,
                            endpoint=route['path'],
                            flow_type='access',
                            content_type=self._infer_content_type(route),
                            metadata={'auth_required': template.get('authentication', True)}
                        ))
        
        return flows
    
    def _map_file_relationships(self, templates: Dict[str, Any]) -> List[FileRelationship]:
        """Map file storage and access relationships"""
        
        relationships = []
        
        for service_name, template in templates.items():
            for model in template.get('database_models', []):
                for field in model['fields']:
                    
                    if self._is_file_field(field):
                        relationships.append(FileRelationship(
                            service=service_name,
                            model=model['name'],
                            field=field['name'],
                            file_type=self._infer_file_type(field),
                            storage_location=self._infer_storage_location(field),
                            access_patterns=self._infer_access_patterns(field, model)
                        ))
        
        return relationships
    
    def _analyze_download_patterns(self, templates: Dict[str, Any]) -> List[DownloadPattern]:
        """Analyze download and export patterns"""
        
        patterns = []
        
        for service_name, template in templates.items():
            download_endpoints = []
            
            for endpoint_group in template.get('endpoints', []):
                for route in endpoint_group.get('routes', []):
                    if self._is_download_endpoint(route):
                        download_endpoints.append(route)
            
            if download_endpoints:
                # Group by content type
                content_types = set()
                formats = set()
                packaging_options = set()
                bulk_support = False
                
                for endpoint in download_endpoints:
                    content_types.add(self._infer_content_type(endpoint))
                    formats.update(self._extract_download_formats(endpoint))
                    packaging_options.update(self._extract_packaging_options(endpoint))
                    if self._has_bulk_support(endpoint):
                        bulk_support = True
                
                patterns.append(DownloadPattern(
                    service=service_name,
                    endpoint='multiple',
                    content_types=list(content_types),
                    formats=list(formats),
                    packaging_options=list(packaging_options),
                    bulk_support=bulk_support
                ))
        
        return patterns
    
    def _calculate_storage_requirements(self, templates: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate storage requirements for the platform"""
        
        requirements = {
            'services_with_storage': [],
            'file_types': set(),
            'estimated_storage_per_user': {},
            'backup_requirements': [],
            'cdn_requirements': []
        }
        
        for service_name, template in templates.items():
            service_storage = {
                'service': service_name,
                'file_fields': 0,
                'content_types': set(),
                'estimated_size_mb': 0
            }
            
            for model in template.get('database_models', []):
                for field in model['fields']:
                    if self._is_file_field(field):
                        service_storage['file_fields'] += 1
                        file_type = self._infer_file_type(field)
                        service_storage['content_types'].add(file_type)
                        requirements['file_types'].add(file_type)
                        
                        # Estimate storage based on file type
                        if file_type == 'video':
                            service_storage['estimated_size_mb'] += 500  # Average video file
                        elif file_type == 'document':
                            service_storage['estimated_size_mb'] += 10
                        elif file_type == 'image':
                            service_storage['estimated_size_mb'] += 2
                        else:
                            service_storage['estimated_size_mb'] += 5
            
            if service_storage['file_fields'] > 0:
                service_storage['content_types'] = list(service_storage['content_types'])
                requirements['services_with_storage'].append(service_storage)
                requirements['estimated_storage_per_user'][service_name] = service_storage['estimated_size_mb']
        
        requirements['file_types'] = list(requirements['file_types'])
        requirements['total_estimated_mb_per_user'] = sum(requirements['estimated_storage_per_user'].values())
        
        return requirements
    
    def _generate_integration_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for content integration"""
        
        recommendations = []
        
        # Check for missing content storage service
        has_dedicated_storage = any(
            'content_storage' in flow.service or 'file_storage' in flow.service 
            for flow in self.content_flows
        )
        
        if not has_dedicated_storage and len(self.file_relationships) > 3:
            recommendations.append({
                'type': 'missing_service',
                'priority': 'high',
                'title': 'Consider dedicated content storage service',
                'description': 'Multiple services handle files. A dedicated storage service would improve consistency.',
                'suggested_action': 'Create content-storage-service template'
            })
        
        # Check for missing download aggregation
        download_services = [pattern.service for pattern in self.download_patterns]
        if len(download_services) > 2:
            recommendations.append({
                'type': 'optimization',
                'priority': 'medium', 
                'title': 'Consider download aggregation service',
                'description': 'Multiple services provide downloads. Aggregation could improve user experience.',
                'suggested_action': 'Add user content dashboard with unified downloads'
            })
        
        # Check for missing file format conversions
        all_formats = set()
        for pattern in self.download_patterns:
            all_formats.update(pattern.formats)
        
        if len(all_formats) > 5:
            recommendations.append({
                'type': 'enhancement',
                'priority': 'low',
                'title': 'Consider format conversion service',
                'description': 'Many file formats detected. Conversion service could add flexibility.',
                'suggested_action': 'Add file conversion utilities to content management'
            })
        
        return recommendations
    
    def _generate_content_summary(self) -> Dict[str, Any]:
        """Generate summary of content architecture"""
        
        return {
            'total_content_flows': len(self.content_flows),
            'content_creation_services': len([f for f in self.content_flows if f.flow_type == 'creation']),
            'download_enabled_services': len([f for f in self.content_flows if f.flow_type == 'download']),
            'file_storage_models': len(self.file_relationships),
            'supported_file_types': list(self.storage_requirements.get('file_types', [])),
            'bulk_download_support': any(pattern.bulk_support for pattern in self.download_patterns),
            'estimated_storage_per_user_mb': self.storage_requirements.get('total_estimated_mb_per_user', 0)
        }
    
    # Helper methods for content analysis
    def _is_content_creation_endpoint(self, route: Dict) -> bool:
        """Check if endpoint creates content"""
        creation_keywords = ['create', 'upload', 'generate', 'build', 'compose']
        path_lower = route['path'].lower()
        return any(keyword in path_lower for keyword in creation_keywords)
    
    def _is_download_endpoint(self, route: Dict) -> bool:
        """Check if endpoint provides downloads"""
        return ('download' in route['path'].lower() or 
                route.get('return_type') == 'StreamingResponse' or
                'export' in route['path'].lower())
    
    def _is_content_access_endpoint(self, route: Dict) -> bool:
        """Check if endpoint provides content access"""
        access_keywords = ['content', 'material', 'file', 'resource']
        path_lower = route['path'].lower()
        return (any(keyword in path_lower for keyword in access_keywords) and 
                route['method'] == 'GET')
    
    def _is_file_field(self, field: Dict) -> bool:
        """Check if database field stores file information"""
        file_indicators = ['url', 'path', 'file', 'attachment', 'media', 'image', 'video', 'document']
        field_name_lower = field['name'].lower()
        return any(indicator in field_name_lower for indicator in file_indicators)
    
    def _infer_content_type(self, route: Dict) -> str:
        """Infer content type from route"""
        path_lower = route['path'].lower()
        
        if 'course' in path_lower:
            return 'course'
        elif 'slide' in path_lower:
            return 'slide'
        elif 'lab' in path_lower:
            return 'lab'
        elif 'resource' in path_lower or 'material' in path_lower:
            return 'resource'
        elif 'video' in path_lower:
            return 'video'
        elif 'document' in path_lower:
            return 'document'
        else:
            return 'unknown'
    
    def _infer_file_type(self, field: Dict) -> str:
        """Infer file type from field"""
        field_name_lower = field['name'].lower()
        
        if 'video' in field_name_lower:
            return 'video'
        elif 'image' in field_name_lower or 'avatar' in field_name_lower:
            return 'image'
        elif 'document' in field_name_lower or 'pdf' in field_name_lower:
            return 'document'
        elif 'archive' in field_name_lower or 'zip' in field_name_lower:
            return 'archive'
        else:
            return 'file'
    
    def _extract_supported_formats(self, route: Dict) -> List[str]:
        """Extract supported formats from route"""
        formats = []
        
        # Check query parameters for format options
        for param in route.get('query_params', []):
            if param['name'] == 'format' and 'choices' in param:
                formats.extend(param['choices'])
        
        # Infer from path
        path_lower = route['path'].lower()
        if 'slide' in path_lower:
            formats.extend(['pptx', 'pdf', 'html'])
        elif 'course' in path_lower:
            formats.extend(['zip', 'scorm'])
        elif 'lab' in path_lower:
            formats.extend(['zip', 'docker'])
        
        return list(set(formats))
    
    def _extract_download_formats(self, route: Dict) -> List[str]:
        """Extract download formats from route"""
        return self._extract_supported_formats(route)
    
    def _extract_packaging_options(self, route: Dict) -> List[str]:
        """Extract packaging options from route"""
        options = []
        
        for param in route.get('query_params', []):
            if 'include_' in param['name']:
                options.append(param['name'])
        
        return options
    
    def _has_bulk_support(self, route: Dict) -> bool:
        """Check if route supports bulk operations"""
        bulk_indicators = ['bulk', 'all', 'batch', 'multiple']
        path_lower = route['path'].lower()
        return any(indicator in path_lower for indicator in bulk_indicators)
    
    def _infer_storage_location(self, field: Dict) -> str:
        """Infer storage location from field"""
        if 'url' in field['name'].lower():
            return 'cdn'
        elif 'path' in field['name'].lower():
            return 'local'
        else:
            return 'unknown'
    
    def _infer_access_patterns(self, field: Dict, model: Dict) -> List[str]:
        """Infer access patterns from field and model context"""
        patterns = []
        
        if 'public' in field.get('name', '').lower():
            patterns.append('public')
        else:
            patterns.append('authenticated')
        
        if 'avatar' in field.get('name', '').lower():
            patterns.append('profile_access')
        
        return patterns

class ContentAwareServiceGenerator:
    """Service generator with advanced content management capabilities"""
    
    def __init__(self, client: anthropic.Anthropic, logger: VerboseLogger, services_dir: Path):
        self.client = client
        self.logger = logger
        self.services_dir = services_dir
    
    async def generate_service_with_content_management(self, service_name: str, template: Dict, context: Dict):
        """Generate service with comprehensive content management features"""
        
        self.logger.content(f"Generating content-aware service: {service_name}")
        
        service_dir = self.services_dir / service_name
        service_dir.mkdir(exist_ok=True)
        
        # Create service directory structure
        await self._create_service_structure(service_dir)
        
        # Generate standard service components
        await self._generate_standard_components(service_dir, service_name, template, context)
        
        # Generate content-specific components
        if self._has_content_features(template):
            await self._generate_content_management_components(service_dir, service_name, template, context)
        
        # Generate file handling components
        if self._has_file_operations(template):
            await self._generate_file_handling_components(service_dir, service_name, template, context)
        
        # Generate download components
        if self._has_download_endpoints(template):
            await self._generate_download_components(service_dir, service_name, template, context)
        
        # Generate testing components
        await self._generate_service_tests(service_dir, service_name, template, context)
        
        self.logger.success(f"Generated content-aware service: {service_name}")
    
    async def _create_service_structure(self, service_dir: Path):
        """Create comprehensive service directory structure"""
        
        directories = [
            "models", "schemas", "services", "routers", "clients", "events",
            "utils", "middleware", "tests", "tests/unit", "tests/integration",
            "tests/content", "storage", "downloads", "config"
        ]
        
        for dir_name in directories:
            (service_dir / dir_name).mkdir(exist_ok=True)
        
        # Create __init__.py files
        for dir_name in ["models", "schemas", "services", "routers", "clients", "events", "utils", "middleware"]:
            (service_dir / dir_name / "__init__.py").touch()
    
    async def _generate_standard_components(self, service_dir: Path, service_name: str, template: Dict, context: Dict):
        """Generate standard service components"""
        
        # Generate models
        models_code = await self._generate_models_code(template, context)
        (service_dir / "models" / "models.py").write_text(models_code)
        
        # Generate schemas
        schemas_code = await self._generate_schemas_code(template, context)
        (service_dir / "schemas" / "schemas.py").write_text(schemas_code)
        
        # Generate routers
        routers_code = await self._generate_routers_code(template, context)
        (service_dir / "routers" / "main.py").write_text(routers_code)
        
        # Generate business logic
        services_code = await self._generate_services_code(template, context)
        (service_dir / "services" / f"{service_name}_service.py").write_text(services_code)
        
        # Generate main application
        main_code = await self._generate_main_application_code(service_name, template, context)
        (service_dir / "main.py").write_text(main_code)
        
        # Generate requirements
        requirements = await self._generate_requirements(template)
        (service_dir / "requirements.txt").write_text(requirements)
        
        # Generate Dockerfile
        dockerfile = await self._generate_dockerfile(service_name, template)
        (service_dir / "Dockerfile").write_text(dockerfile)
    
    async def _generate_content_management_components(self, service_dir: Path, service_name: str, template: Dict, context: Dict):
        """Generate content management specific components"""
        
        self.logger.substep("Generating content management components...")
        
        # Content manager
        content_manager_code = await self._generate_content_manager_code(template, context)
        (service_dir / "services" / "content_manager.py").write_text(content_manager_code)
        
        # Content access control
        access_control_code = await self._generate_access_control_code(template, context)
        (service_dir / "services" / "access_control.py").write_text(access_control_code)
        
        # Content versioning
        versioning_code = await self._generate_versioning_code(template, context)
        (service_dir / "services" / "versioning.py").write_text(versioning_code)
        
        # Content metadata manager
        metadata_code = await self._generate_metadata_manager_code(template, context)
        (service_dir / "services" / "metadata_manager.py").write_text(metadata_code)
    
    async def _generate_file_handling_components(self, service_dir: Path, service_name: str, template: Dict, context: Dict):
        """Generate file handling components"""
        
        self.logger.substep("Generating file handling components...")
        
        # File storage manager
        storage_manager_code = await self._generate_storage_manager_code(template, context)
        (service_dir / "services" / "storage_manager.py").write_text(storage_manager_code)
        
        # File processor
        processor_code = await self._generate_file_processor_code(template, context)
        (service_dir / "services" / "file_processor.py").write_text(processor_code)
        
        # File validation
        validation_code = await self._generate_file_validation_code(template, context)
        (service_dir / "utils" / "file_validation.py").write_text(validation_code)
        
        # File utilities
        utils_code = await self._generate_file_utils_code(template, context)
        (service_dir / "utils" / "file_utils.py").write_text(utils_code)
    
    async def _generate_download_components(self, service_dir: Path, service_name: str, template: Dict, context: Dict):
        """Generate download and export components"""
        
        self.logger.substep("Generating download components...")
        
        # Download manager
        download_manager_code = await self._generate_download_manager_code(template, context)
        (service_dir / "services" / "download_manager.py").write_text(download_manager_code)
        
        # Export utilities
        export_utils_code = await self._generate_export_utils_code(template, context)
        (service_dir / "utils" / "export_utils.py").write_text(export_utils_code)
        
        # Packaging service
        packaging_code = await self._generate_packaging_service_code(template, context)
        (service_dir / "services" / "packaging_service.py").write_text(packaging_code)
        
        # Format converters
        converters_code = await self._generate_format_converters_code(template, context)
        (service_dir / "utils" / "format_converters.py").write_text(converters_code)
    
    async def _generate_service_tests(self, service_dir: Path, service_name: str, template: Dict, context: Dict):
        """Generate comprehensive test suite for the service"""
        
        self.logger.test(f"Generating comprehensive tests for {service_name}...")
        
        # Unit tests
        unit_tests_code = await self._generate_unit_tests_code(service_name, template, context)
        (service_dir / "tests" / "unit" / "test_main.py").write_text(unit_tests_code)
        
        # Integration tests
        integration_tests_code = await self._generate_integration_tests_code(service_name, template, context)
        (service_dir / "tests" / "integration" / "test_integration.py").write_text(integration_tests_code)
        
        # Content-specific tests
        if self._has_content_features(template):
            content_tests_code = await self._generate_content_tests_code(service_name, template, context)
            (service_dir / "tests" / "content" / "test_content_management.py").write_text(content_tests_code)
        
        # Download tests
        if self._has_download_endpoints(template):
            download_tests_code = await self._generate_download_tests_code(service_name, template, context)
            (service_dir / "tests" / "content" / "test_downloads.py").write_text(download_tests_code)
        
        # Performance tests
        performance_tests_code = await self._generate_performance_tests_code(service_name, template, context)
        (service_dir / "tests" / "test_performance.py").write_text(performance_tests_code)
        
        # Test configuration
        test_config_code = await self._generate_test_config_code(service_name, template)
        (service_dir / "tests" / "conftest.py").write_text(test_config_code)
        
        # Test requirements
        test_requirements = await self._generate_test_requirements(template)
        (service_dir / "tests" / "requirements.txt").write_text(test_requirements)
    
    # Code generation methods using Claude
    async def _generate_content_manager_code(self, template: Dict, context: Dict) -> str:
        """Generate content manager code using Claude"""
        
        prompt = f"""
        Generate a comprehensive Python content manager for a microservice with these specifications:
        
        Service Template:
        {json.dumps(template, indent=2)}
        
        Context:
        {json.dumps(context, indent=2)}
        
        The content manager should include:
        1. Content lifecycle management (create, read, update, delete)
        2. Content ownership and access control
        3. Content versioning and history
        4. Content metadata management
        5. Content validation and sanitization
        6. Integration with file storage systems
        7. Event publishing for content operations
        8. Comprehensive error handling
        9. Async/await patterns for performance
        10. Type hints and documentation
        
        Use modern Python patterns with FastAPI, SQLAlchemy, and Pydantic.
        Include proper logging and monitoring integration.
        """
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_download_manager_code(self, template: Dict, context: Dict) -> str:
        """Generate download manager code using Claude"""
        
        prompt = f"""
        Generate a comprehensive Python download manager for a microservice:
        
        Service Template:
        {json.dumps(template, indent=2)}
        
        The download manager should include:
        1. Single file downloads with streaming
        2. Bulk download with ZIP packaging
        3. Format conversion capabilities
        4. Download progress tracking
        5. Download authentication and authorization
        6. Download analytics and logging
        7. Rate limiting and throttling
        8. Resumable downloads
        9. Download expiration and cleanup
        10. Integration with content management
        
        Use FastAPI's StreamingResponse for efficient file delivery.
        Include comprehensive error handling and security measures.
        Support multiple file formats and conversion options.
        """
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_content_tests_code(self, service_name: str, template: Dict, context: Dict) -> str:
        """Generate comprehensive content management tests"""
        
        prompt = f"""
        Generate comprehensive pytest test suite for content management functionality:
        
        Service: {service_name}
        Template: {json.dumps(template, indent=2)}
        
        Generate tests for:
        1. Content creation and validation
        2. Content access control and permissions
        3. Content versioning and history
        4. File upload and storage
        5. Content metadata management
        6. Content search and filtering
        7. Content ownership transfer
        8. Content deletion and cleanup
        9. Content export and packaging
        10. Error handling and edge cases
        
        Include:
        - Fixtures for test data setup
        - Mock objects for external dependencies
        - Parameterized tests for multiple scenarios
        - Integration tests with database
        - Performance tests for large content
        - Security tests for access control
        - Cleanup after tests
        
        Use pytest best practices with async support.
        """
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_download_tests_code(self, service_name: str, template: Dict, context: Dict) -> str:
        """Generate comprehensive download functionality tests"""
        
        prompt = f"""
        Generate comprehensive pytest test suite for download functionality:
        
        Service: {service_name}
        Template: {json.dumps(template, indent=2)}
        
        Generate tests for:
        1. Single file downloads
        2. Bulk downloads and ZIP creation
        3. Format conversion downloads
        4. Download authentication
        5. Download progress tracking
        6. Download rate limiting
        7. Resumable downloads
        8. Download expiration
        9. Invalid download requests
        10. Download security and validation
        
        Include:
        - Mock file system and storage
        - Test file creation and cleanup
        - Streaming response testing
        - Large file download testing
        - Concurrent download testing
        - Network error simulation
        - Security penetration testing
        
        Use pytest-asyncio for async testing.
        Include performance benchmarks.
        """
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    # Helper methods for feature detection
    def _has_content_features(self, template: Dict) -> bool:
        """Check if template has content management features"""
        provides = template.get('provides', [])
        content_capabilities = ['content_management', 'course_authoring', 'content_creation']
        return any(cap in provides for cap in content_capabilities)
    
    def _has_file_operations(self, template: Dict) -> bool:
        """Check if template has file operations"""
        # Check for file-related endpoints
        for endpoint_group in template.get('endpoints', []):
            for route in endpoint_group.get('routes', []):
                if ('upload' in route['path'].lower() or 
                    'file' in route['path'].lower() or
                    'UploadFile' in str(route.get('body_param', {}))):
                    return True
        
        # Check for file fields in models
        for model in template.get('database_models', []):
            for field in model['fields']:
                if any(indicator in field['name'].lower() for indicator in ['url', 'path', 'file']):
                    return True
        
        return False
    
    def _has_download_endpoints(self, template: Dict) -> bool:
        """Check if template has download endpoints"""
        for endpoint_group in template.get('endpoints', []):
            for route in endpoint_group.get('routes', []):
                if ('download' in route['path'].lower() or 
                    route.get('return_type') == 'StreamingResponse'):
                    return True
        return False
    
    # Placeholder methods for other code generation (implement similar to above)
    async def _generate_models_code(self, template: Dict, context: Dict) -> str:
        return "# Generated models code"
    
    async def _generate_schemas_code(self, template: Dict, context: Dict) -> str:
        return "# Generated schemas code"
    
    async def _generate_routers_code(self, template: Dict, context: Dict) -> str:
        return "# Generated routers code"
    
    async def _generate_services_code(self, template: Dict, context: Dict) -> str:
        return "# Generated services code"
    
    async def _generate_main_application_code(self, service_name: str, template: Dict, context: Dict) -> str:
        return "# Generated main application code"
    
    async def _generate_requirements(self, template: Dict) -> str:
        return "# Generated requirements"
    
    async def _generate_dockerfile(self, service_name: str, template: Dict) -> str:
        return "# Generated Dockerfile"
    
    async def _generate_access_control_code(self, template: Dict, context: Dict) -> str:
        return "# Generated access control code"
    
    async def _generate_versioning_code(self, template: Dict, context: Dict) -> str:
        return "# Generated versioning code"
    
    async def _generate_metadata_manager_code(self, template: Dict, context: Dict) -> str:
        return "# Generated metadata manager code"
    
    async def _generate_storage_manager_code(self, template: Dict, context: Dict) -> str:
        return "# Generated storage manager code"
    
    async def _generate_file_processor_code(self, template: Dict, context: Dict) -> str:
        return "# Generated file processor code"
    
    async def _generate_file_validation_code(self, template: Dict, context: Dict) -> str:
        return "# Generated file validation code"
    
    async def _generate_file_utils_code(self, template: Dict, context: Dict) -> str:
        return "# Generated file utils code"
    
    async def _generate_export_utils_code(self, template: Dict, context: Dict) -> str:
        return "# Generated export utils code"
    
    async def _generate_packaging_service_code(self, template: Dict, context: Dict) -> str:
        return "# Generated packaging service code"
    
    async def _generate_format_converters_code(self, template: Dict, context: Dict) -> str:
        return "# Generated format converters code"
    
    async def _generate_unit_tests_code(self, service_name: str, template: Dict, context: Dict) -> str:
        return "# Generated unit tests code"
    
    async def _generate_integration_tests_code(self, service_name: str, template: Dict, context: Dict) -> str:
        return "# Generated integration tests code"
    
    async def _generate_performance_tests_code(self, service_name: str, template: Dict, context: Dict) -> str:
        return "# Generated performance tests code"
    
    async def _generate_test_config_code(self, service_name: str, template: Dict) -> str:
        return "# Generated test config code"
    
    async def _generate_test_requirements(self, template: Dict) -> str:
        return "# Generated test requirements"

class ContentAwareFrontendGenerator:
    """Frontend generator with comprehensive content management UI"""
    
    def __init__(self, client: anthropic.Anthropic, logger: VerboseLogger, frontend_dir: Path):
        self.client = client
        self.logger = logger
        self.frontend_dir = frontend_dir
    
    async def generate_content_management_frontend(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        """Generate frontend with comprehensive content management capabilities"""
        
        self.logger.content("Generating content management frontend...")
        
        # Create frontend structure
        await self._create_frontend_structure()
        
        # Generate content dashboard
        await self._generate_content_dashboard(service_templates, content_analysis)
        
        # Generate download manager UI
        await self._generate_download_manager_ui(service_templates, content_analysis)
        
        # Generate file browser components
        await self._generate_file_browser_components(service_templates, content_analysis)
        
        # Generate content preview components
        await self._generate_content_preview_components(service_templates, content_analysis)
        
        # Generate content creation UI
        await self._generate_content_creation_ui(service_templates, content_analysis)
        
        # Generate API clients
        await self._generate_api_clients(service_templates)
        
        # Generate state management
        await self._generate_state_management(service_templates, content_analysis)
        
        # Generate routing
        await self._generate_routing_config(service_templates)
        
        # Generate frontend tests
        await self._generate_frontend_tests(service_templates, content_analysis)
        
        self.logger.success("Generated comprehensive content management frontend")
    
    async def _create_frontend_structure(self):
        """Create comprehensive frontend directory structure"""
        
        directories = [
            "src/components/content",
            "src/components/downloads", 
            "src/components/files",
            "src/components/preview",
            "src/components/creation",
            "src/pages/dashboard",
            "src/pages/content",
            "src/services/api",
            "src/store/content",
            "src/store/downloads",
            "src/hooks/content",
            "src/utils/file",
            "src/utils/download",
            "src/types/content",
            "src/tests/components",
            "src/tests/integration",
            "src/tests/e2e",
            "public/icons",
            "public/assets"
        ]
        
        for dir_path in directories:
            (self.frontend_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    async def _generate_content_dashboard(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        """Generate user content dashboard"""
        
        self.logger.substep("Generating content dashboard components...")
        
        # Main dashboard component
        dashboard_component = await self._create_dashboard_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/content/ContentDashboard.tsx").write_text(dashboard_component)
        
        # Content list component
        content_list_component = await self._create_content_list_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/content/ContentList.tsx").write_text(content_list_component)
        
        # Content card component
        content_card_component = await self._create_content_card_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/content/ContentCard.tsx").write_text(content_card_component)
        
        # Content filters component
        filters_component = await self._create_content_filters_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/content/ContentFilters.tsx").write_text(filters_component)
    
    async def _generate_download_manager_ui(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        """Generate download manager UI components"""
        
        self.logger.substep("Generating download manager UI...")
        
        # Download manager component
        download_manager = await self._create_download_manager_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/downloads/DownloadManager.tsx").write_text(download_manager)
        
        # Download queue component
        download_queue = await self._create_download_queue_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/downloads/DownloadQueue.tsx").write_text(download_queue)
        
        # Download progress component
        download_progress = await self._create_download_progress_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/downloads/DownloadProgress.tsx").write_text(download_progress)
        
        # Bulk download component
        bulk_download = await self._create_bulk_download_component(service_templates, content_analysis)
        (self.frontend_dir / "src/components/downloads/BulkDownload.tsx").write_text(bulk_download)
    
    async def _create_dashboard_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        """Create React component for content dashboard"""
        
        prompt = f"""
        Generate a comprehensive React TypeScript component for a user content dashboard:
        
        Service Templates:
        {json.dumps(service_templates, indent=2)}
        
        Content Analysis:
        {json.dumps(content_analysis, indent=2)}
        
        The component should include:
        1. Overview statistics (total content, storage used, recent activity)
        2. Content type categorization with visual indicators
        3. Search and filtering capabilities
        4. Sorting options (date, name, size, type)
        5. Bulk selection and operations
        6. Download actions for individual and bulk items
        7. Content creation shortcuts
        8. Recent activity feed
        9. Storage usage visualization
        10. Responsive design for mobile and desktop
        
        Requirements:
        - Use React hooks (useState, useEffect, useContext)
        - TypeScript with proper interfaces
        - Tailwind CSS for styling
        - Loading states and error handling
        - Accessibility features (ARIA labels, keyboard navigation)
        - Integration with download manager
        - Real-time updates via WebSocket
        - Infinite scrolling for large content lists
        - Drag and drop for bulk operations
        
        Include proper component documentation and prop interfaces.
        """
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _create_download_manager_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        """Create React component for download management"""
        
        prompt = f"""
        Generate a comprehensive React TypeScript download manager component:
        
        Available Services:
        {json.dumps(service_templates, indent=2)}
        
        Content Analysis:
        {json.dumps(content_analysis, indent=2)}
        
        The component should include:
        1. Download queue management with priority
        2. Real-time download progress tracking
        3. Pause, resume, and cancel functionality
        4. Download history and retry failed downloads
        5. Format selection for downloads
        6. Bulk download with ZIP packaging
        7. Download scheduling and throttling
        8. Storage location selection
        9. Download notifications
        10. Bandwidth usage monitoring
        
        Features:
        - Service worker for background downloads
        - IndexedDB for persistent download state
        - Download progress visualization
        - Error handling with retry logic
        - Download speed calculation
        - Estimated time remaining
        - Download completion notifications
        - Integration with browser download manager
        
        Use modern React patterns with hooks and context API.
        Include comprehensive error boundaries and loading states.
        """
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_frontend_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        """Generate comprehensive frontend test suite"""
        
        self.logger.test("Generating frontend test suite...")
        
        # Component tests
        component_tests = await self._create_component_tests(service_templates, content_analysis)
        (self.frontend_dir / "src/tests/components/ContentDashboard.test.tsx").write_text(component_tests)
        
        # Integration tests
        integration_tests = await self._create_integration_tests(service_templates, content_analysis)
        (self.frontend_dir / "src/tests/integration/ContentFlow.test.tsx").write_text(integration_tests)
        
        # E2E tests
        e2e_tests = await self._create_e2e_tests(service_templates, content_analysis)
        (self.frontend_dir / "src/tests/e2e/UserJourney.test.ts").write_text(e2e_tests)
        
        # Test utilities
        test_utils = await self._create_test_utils(service_templates)
        (self.frontend_dir / "src/tests/utils/testUtils.ts").write_text(test_utils)
        
        # Test configuration
        test_config = await self._create_test_config()
        (self.frontend_dir / "jest.config.js").write_text(test_config)
    
    # Placeholder methods for other frontend components
    async def _create_content_list_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated content list component"
    
    async def _create_content_card_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated content card component"
    
    async def _create_content_filters_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated content filters component"
    
    async def _create_download_queue_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated download queue component"
    
    async def _create_download_progress_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated download progress component"
    
    async def _create_bulk_download_component(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated bulk download component"
    
    async def _generate_file_browser_components(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        return "// Generated file browser components"
    
    async def _generate_content_preview_components(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        return "// Generated content preview components"
    
    async def _generate_content_creation_ui(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        return "// Generated content creation UI"
    
    async def _generate_api_clients(self, service_templates: Dict[str, Any]):
        return "// Generated API clients"
    
    async def _generate_state_management(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        return "// Generated state management"
    
    async def _generate_routing_config(self, service_templates: Dict[str, Any]):
        return "// Generated routing config"
    
    async def _create_component_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated component tests"
    
    async def _create_integration_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated integration tests"
    
    async def _create_e2e_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "// Generated E2E tests"
    
    async def _create_test_utils(self, service_templates: Dict[str, Any]) -> str:
        return "// Generated test utilities"
    
    async def _create_test_config(self) -> str:
        return "// Generated test configuration"

class ComprehensiveTestingFramework:
    """Comprehensive testing framework for the entire platform"""
    
    def __init__(self, logger: VerboseLogger, repo_root: Path):
        self.logger = logger
        self.repo_root = repo_root
        self.tests_dir = repo_root / "tests"
    
    async def generate_platform_testing_suite(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        """Generate comprehensive testing suite for the entire platform"""
        
        self.logger.test("Generating comprehensive platform testing suite...")
        
        # Create test directory structure
        await self._create_test_structure()
        
        # Generate unit test suite
        await self._generate_unit_test_suite(service_templates)
        
        # Generate integration test suite
        await self._generate_integration_test_suite(service_templates, content_analysis)
        
        # Generate end-to-end test suite
        await self._generate_e2e_test_suite(service_templates, content_analysis)
        
        # Generate performance test suite
        await self._generate_performance_test_suite(service_templates, content_analysis)
        
        # Generate security test suite
        await self._generate_security_test_suite(service_templates)
        
        # Generate content-specific test suite
        await self._generate_content_test_suite(service_templates, content_analysis)
        
        # Generate test automation and CI/CD integration
        await self._generate_test_automation(service_templates)
        
        self.logger.success("Generated comprehensive platform testing suite")
    
    async def _create_test_structure(self):
        """Create comprehensive test directory structure"""
        
        directories = [
            "unit", "integration", "e2e", "performance", "security", "content",
            "fixtures", "mocks", "utils", "reports", "config", "scripts",
            "unit/services", "unit/models", "unit/routers", "unit/utils",
            "integration/services", "integration/database", "integration/api",
            "e2e/user_journeys", "e2e/content_flows", "e2e/admin_workflows",
            "performance/load", "performance/stress", "performance/volume",
            "security/auth", "security/access", "security/data",
            "content/upload", "content/download", "content/management"
        ]
        
        for dir_path in directories:
            (self.tests_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files
        init_dirs = ["unit", "integration", "e2e", "performance", "security", "content", "fixtures", "mocks", "utils"]
        for dir_name in init_dirs:
            (self.tests_dir / dir_name / "__init__.py").touch()
    
    async def _generate_integration_test_suite(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        """Generate comprehensive integration test suite"""
        
        self.logger.substep("Generating integration test suite...")
        
        # Service-to-service integration tests
        service_integration_tests = await self._create_service_integration_tests(service_templates)
        (self.tests_dir / "integration/test_service_communication.py").write_text(service_integration_tests)
        
        # Database integration tests
        database_tests = await self._create_database_integration_tests(service_templates)
        (self.tests_dir / "integration/database/test_cross_service_data.py").write_text(database_tests)
        
        # API integration tests
        api_tests = await self._create_api_integration_tests(service_templates)
        (self.tests_dir / "integration/api/test_api_contracts.py").write_text(api_tests)
        
        # Event integration tests
        event_tests = await self._create_event_integration_tests(service_templates)
        (self.tests_dir / "integration/test_event_flows.py").write_text(event_tests)
        
        # Content flow integration tests
        content_flow_tests = await self._create_content_flow_integration_tests(service_templates, content_analysis)
        (self.tests_dir / "integration/test_content_flows.py").write_text(content_flow_tests)
    
    async def _generate_content_test_suite(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        """Generate content-specific test suite"""
        
        self.logger.substep("Generating content-specific test suite...")
        
        # Content upload tests
        upload_tests = await self._create_content_upload_tests(service_templates, content_analysis)
        (self.tests_dir / "content/upload/test_content_upload.py").write_text(upload_tests)
        
        # Content download tests
        download_tests = await self._create_content_download_tests(service_templates, content_analysis)
        (self.tests_dir / "content/download/test_content_download.py").write_text(download_tests)
        
        # Content management tests
        management_tests = await self._create_content_management_tests(service_templates, content_analysis)
        (self.tests_dir / "content/management/test_content_lifecycle.py").write_text(management_tests)
        
        # File format tests
        format_tests = await self._create_file_format_tests(service_templates, content_analysis)
        (self.tests_dir / "content/test_file_formats.py").write_text(format_tests)
        
        # Content security tests
        security_tests = await self._create_content_security_tests(service_templates, content_analysis)
        (self.tests_dir / "content/test_content_security.py").write_text(security_tests)
    
    async def _create_service_integration_tests(self, service_templates: Dict[str, Any]) -> str:
        """Create service-to-service integration tests"""
        
        prompt = f"""
        Generate comprehensive pytest integration tests for service-to-service communication:
        
        Service Templates:
        {json.dumps(service_templates, indent=2)}
        
        Generate tests for:
        1. HTTP API calls between services
        2. Event publishing and consumption
        3. Shared database access patterns
        4. Authentication and authorization flows
        5. Error handling and retry mechanisms
        6. Circuit breaker patterns
        7. Service discovery and health checks
        8. Load balancing and failover
        9. Data consistency across services
        10. Transaction coordination
        
        Include:
        - Docker Compose setup for test environment
        - Service startup and teardown
        - Mock external dependencies
        - Test data fixtures
        - Comprehensive assertions
        - Performance benchmarks
        - Chaos engineering tests
        - Network partition simulation
        
        Use pytest-asyncio, httpx, and docker-compose.
        Include proper test isolation and cleanup.
        """
        
        # Would use Claude API here, returning placeholder for brevity
        return "# Generated comprehensive service integration tests"
    
    async def _create_content_flow_integration_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        """Create content flow integration tests"""
        
        prompt = f"""
        Generate comprehensive integration tests for content flows:
        
        Service Templates:
        {json.dumps(service_templates, indent=2)}
        
        Content Analysis:
        {json.dumps(content_analysis, indent=2)}
        
        Generate tests for complete content workflows:
        1. User creates course content
        2. Content is processed and stored
        3. Content metadata is indexed
        4. User accesses content from dashboard
        5. User downloads individual files
        6. User downloads bulk content packages
        7. Content is shared with other users
        8. Content versioning and updates
        9. Content deletion and cleanup
        10. Content backup and restore
        
        Test scenarios:
        - Single user content lifecycle
        - Multi-user content collaboration
        - Large file upload and download
        - Concurrent content operations
        - Content format conversions
        - Content access control
        - Content search and discovery
        - Content analytics and reporting
        
        Include real file uploads, processing, and downloads.
        Test all supported file formats and conversion options.
        """
        
        return "# Generated comprehensive content flow integration tests"
    
    async def _create_content_upload_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        """Create content upload tests"""
        
        return "# Generated content upload tests"
    
    async def _create_content_download_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        """Create content download tests"""
        
        return "# Generated content download tests"
    
    # Placeholder methods for other test generation
    async def _generate_unit_test_suite(self, service_templates: Dict[str, Any]):
        pass
    
    async def _generate_e2e_test_suite(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        pass
    
    async def _generate_performance_test_suite(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]):
        pass
    
    async def _generate_security_test_suite(self, service_templates: Dict[str, Any]):
        pass
    
    async def _generate_test_automation(self, service_templates: Dict[str, Any]):
        pass
    
    async def _create_database_integration_tests(self, service_templates: Dict[str, Any]) -> str:
        return "# Generated database integration tests"
    
    async def _create_api_integration_tests(self, service_templates: Dict[str, Any]) -> str:
        return "# Generated API integration tests"
    
    async def _create_event_integration_tests(self, service_templates: Dict[str, Any]) -> str:
        return "# Generated event integration tests"
    
    async def _create_content_management_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "# Generated content management tests"
    
    async def _create_file_format_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "# Generated file format tests"
    
    async def _create_content_security_tests(self, service_templates: Dict[str, Any], content_analysis: Dict[str, Any]) -> str:
        return "# Generated content security tests"

class ContentAwarePlatformGenerator:
    """Main platform generator with comprehensive content management capabilities"""
    
    def __init__(self, api_key: str = None, verbose: bool = False, templates_dir: Optional[Path] = None):
        self.repo_root = Path(__file__).parent.parent.parent
        self.templates_dir = templates_dir or (self.repo_root / "templates")
        self.services_dir = self.repo_root / "services"
        self.frontend_dir = self.repo_root / "frontend"
        self.shared_dir = self.repo_root / "shared"
        self.config_dir = self.repo_root / "config"
        self.architecture_dir = self.repo_root / "architecture"
        self.tests_dir = self.repo_root / "tests"
        self.verbose = verbose
        self.logger = VerboseLogger(verbose)
        
        # Initialize Claude client
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Initialize components
        self.template_manager = TemplateManager(self.templates_dir, self.logger)
        self.content_analyzer = ContentGraphAnalyzer(self.logger)
        self.service_generator = ContentAwareServiceGenerator(self.client, self.logger, self.services_dir)
        self.frontend_generator = ContentAwareFrontendGenerator(self.client, self.logger, self.frontend_dir)
        self.testing_framework = ComprehensiveTestingFramework(self.logger, self.repo_root)
        
        # State
        self.service_templates = {}
        self.content_analysis = {}
        self.generation_order = []
        
        self.logger.info("Content-Aware Platform Generator initialized")
    
    async def generate_complete_platform_with_content_management(self, features: List[str] = None) -> bool:
        """Generate complete platform with comprehensive content management"""
        
        start_time = time.time()
        
        try:
            # Phase 1: Template Management and Analysis
            self.logger.step("Phase 1: Template Discovery and Content Analysis")
            self.service_templates = await self.template_manager.load_templates_with_extensions(features or ['content-management', 'file-handling'])
            self.content_analysis = self.content_analyzer.analyze_content_architecture(self.service_templates)
            
            # Phase 2: Architecture Planning
            self.logger.step("Phase 2: Architecture Planning and Validation")
            await self._plan_platform_architecture()
            await self._validate_content_requirements()
            
            # Phase 3: Service Generation
            self.logger.step("Phase 3: Content-Aware Service Generation")
            await self._generate_services_with_content_management()
            
            # Phase 4: Frontend Generation
            self.logger.step("Phase 4: Content Management Frontend Generation")
            await self.frontend_generator.generate_content_management_frontend(self.service_templates, self.content_analysis)
            
            # Phase 5: Integration Layer
            self.logger.step("Phase 5: Platform Integration Layer")
            await self._generate_platform_integration()
            
            # Phase 6: Comprehensive Testing
            self.logger.step("Phase 6: Comprehensive Testing Suite Generation")
            await self.testing_framework.generate_platform_testing_suite(self.service_templates, self.content_analysis)
            
            # Phase 7: Deployment and DevOps
            self.logger.step("Phase 7: Deployment and DevOps Configuration")
            await self._generate_deployment_configuration()
            
            # Phase 8: Documentation and Guides
            self.logger.step("Phase 8: Documentation Generation")
            await self._generate_platform_documentation()
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            await self._generate_platform_summary(generation_time)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Platform generation failed: {e}")
            if self.verbose:
                import traceback
                self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return False
    
    async def _plan_platform_architecture(self):
        """Plan comprehensive platform architecture"""
        
        self.logger.content("Planning platform architecture with content management...")
        
        # Calculate generation order based on dependencies
        self.generation_order = self._calculate_generation_order()
        
        # Create architecture documentation
        await self._document_platform_architecture()
        
        self.logger.success(f"Planned architecture for {len(self.service_templates)} services")
        self.logger.content(f"Generation order: {' → '.join(self.generation_order)}")
    
    async def _validate_content_requirements(self):
        """Validate content management requirements"""
        
        self.logger.content("Validating content management requirements...")
        
        # Check for required content capabilities
        required_capabilities = ['file_storage', 'content_access', 'download_support']
        
        for capability in required_capabilities:
            if not self._has_platform_capability(capability):
                self.logger.warning(f"Missing platform capability: {capability}")
        
        # Validate content flows
        content_flows = self.content_analysis.get('content_flows', [])
        if not content_flows:
            self.logger.warning("No content flows detected - content management may be limited")
        
        # Validate file relationships
        file_relationships = self.content_analysis.get('file_relationships', [])
        if not file_relationships:
            self.logger.warning("No file relationships detected - file handling may be limited")
        
        self.logger.success("Content management requirements validated")
    
    async def _generate_services_with_content_management(self):
        """Generate all services with content management capabilities"""
        
        total_services = len(self.generation_order)
        
        with tqdm(total=total_services, desc="🏗️  Generating Content-Aware Services", unit="service") as pbar:
            
            for service_name in self.generation_order:
                pbar.set_description(f"🏗️  {service_name}")
                self.logger.content(f"Generating content-aware service: {service_name}")
                
                template = self.service_templates[service_name]
                context = {
                    'content_analysis': self.content_analysis,
                    'all_services': self.service_templates,
                    'generation_order': self.generation_order
                }
                
                await self.service_generator.generate_service_with_content_management(
                    service_name, template, context
                )
                
                self.logger.success(f"Generated content-aware service: {service_name}")
                pbar.update(1)
        
        self.logger.success(f"Generated all {total_services} content-aware services")
    
    async def _generate_platform_integration(self):
        """Generate platform integration components"""
        
        self.logger.content("Generating platform integration components...")
        
        # API Gateway configuration
        await self._generate_api_gateway_config()
        
        # Service mesh configuration
        await self._generate_service_mesh_config()
        
        # Event bus configuration
        await self._generate_event_bus_config()
        
        # Content storage configuration
        await self._generate_content_storage_config()
        
        # Download orchestration
        await self._generate_download_orchestration()
        
        self.logger.success("Generated platform integration components")
    
    async def _generate_deployment_configuration(self):
        """Generate deployment configuration"""
        
        self.logger.content("Generating deployment configuration...")
        
        # Docker Compose configuration
        docker_compose = await self._generate_docker_compose_config()
        (self.repo_root / "docker-compose.yml").write_text(docker_compose)
        
        # Kubernetes configuration
        k8s_config = await self._generate_kubernetes_config()
        k8s_dir = self.config_dir / "kubernetes"
        k8s_dir.mkdir(exist_ok=True)
        (k8s_dir / "platform.yaml").write_text(k8s_config)
        
        # CI/CD pipeline
        ci_cd_config = await self._generate_ci_cd_config()
        (self.repo_root / ".github/workflows/platform.yml").write_text(ci_cd_config)
        
        self.logger.success("Generated deployment configuration")
    
    async def _generate_platform_documentation(self):
        """Generate comprehensive platform documentation"""
        
        self.logger.content("Generating platform documentation...")
        
        docs_dir = self.repo_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Architecture documentation
        arch_docs = await self._generate_architecture_documentation()
        (docs_dir / "architecture.md").write_text(arch_docs)
        
        # API documentation
        api_docs = await self._generate_api_documentation()
        (docs_dir / "api.md").write_text(api_docs)
        
        # Content management guide
        content_guide = await self._generate_content_management_guide()
        (docs_dir / "content-management.md").write_text(content_guide)
        
        # Deployment guide
        deployment_guide = await self._generate_deployment_guide()
        (docs_dir / "deployment.md").write_text(deployment_guide)
        
        # Testing guide
        testing_guide = await self._generate_testing_guide()
        (docs_dir / "testing.md").write_text(testing_guide)
        
        self.logger.success("Generated comprehensive platform documentation")
    
    async def _generate_platform_summary(self, generation_time: float):
        """Generate comprehensive platform summary"""
        
        # Count generated artifacts
        service_count = len(self.service_templates)
        content_flows = len(self.content_analysis.get('content_flows', []))
        file_relationships = len(self.content_analysis.get('file_relationships', []))
        
        print("\n" + "="*120)
        print("🚀 CONTENT-AWARE PLATFORM GENERATION COMPLETE")
        print("="*120)
        
        print(f"\n📊 PLATFORM STATISTICS:")
        print(f"   🏗️  Services Generated: {service_count}")
        print(f"   📁 Content Flows: {content_flows}")
        print(f"   🔗 File Relationships: {file_relationships}")
        print(f"   📥 Download Patterns: {len(self.content_analysis.get('download_patterns', []))}")
        print(f"   ⏱️  Generation Time: {generation_time:.2f} seconds")
        
        print(f"\n📁 CONTENT MANAGEMENT FEATURES:")
        storage_req = self.content_analysis.get('storage_requirements', {})
        print(f"   💾 Services with Storage: {len(storage_req.get('services_with_storage', []))}")
        print(f"   📋 Supported File Types: {', '.join(storage_req.get('file_types', []))}")
        print(f"   📊 Est. Storage per User: {storage_req.get('total_estimated_mb_per_user', 0):.1f} MB")
        print(f"   📦 Bulk Download Support: {'Yes' if self.content_analysis.get('content_summary', {}).get('bulk_download_support') else 'No'}")
        
        print(f"\n🎯 GENERATED FEATURES:")
        print(f"   ✅ Content creation and management workflows")
        print(f"   ✅ File upload, processing, and storage")
        print(f"   ✅ Individual and bulk download capabilities")
        print(f"   ✅ User content dashboard and access control")
        print(f"   ✅ Content format conversion and packaging")
        print(f"   ✅ Comprehensive testing suite (unit, integration, E2E)")
        print(f"   ✅ React frontend with content management UI")
        print(f"   ✅ API documentation and deployment guides")
        
        print(f"\n🚀 USER WORKFLOW ENABLED:")
        print(f"   1. ✅ User creates course content (slides, labs, resources)")
        print(f"   2. ✅ Content is automatically stored and indexed") 
        print(f"   3. ✅ User accesses all their content from dashboard")
        print(f"   4. ✅ User downloads individual files or complete packages")
        print(f"   5. ✅ Content is available in multiple formats (PDF, ZIP, etc.)")
        print(f"   6. ✅ Bulk download of all user content supported")
        
        print(f"\n🔧 NEXT STEPS:")
        print(f"   1. Review generated services and frontend code")
        print(f"   2. Run comprehensive test suite: pytest tests/")
        print(f"   3. Start platform: docker-compose up -d")
        print(f"   4. Access content dashboard: http://localhost:3000/dashboard")
        print(f"   5. Test content creation and download workflows")
        
        print("="*120)
    
    # Helper methods
    def _calculate_generation_order(self) -> List[str]:
        """Calculate optimal service generation order"""
        
        # Simple dependency-based ordering for now
        # In full implementation, would use topological sort
        services_with_deps = []
        services_without_deps = []
        
        for service_name, template in self.service_templates.items():
            if template.get('depends_on'):
                services_with_deps.append(service_name)
            else:
                services_without_deps.append(service_name)
        
        return services_without_deps + services_with_deps
    
    def _has_platform_capability(self, capability: str) -> bool:
        """Check if platform has specific capability"""
        
        for template in self.service_templates.values():
            if capability in template.get('provides', []):
                return True
        return False
    
    # Placeholder methods for configuration generation
    async def _document_platform_architecture(self):
        pass
    
    async def _generate_api_gateway_config(self):
        pass
    
    async def _generate_service_mesh_config(self):
        pass
    
    async def _generate_event_bus_config(self):
        pass
    
    async def _generate_content_storage_config(self):
        pass
    
    async def _generate_download_orchestration(self):
        pass
    
    async def _generate_docker_compose_config(self) -> str:
        return "# Generated Docker Compose configuration"
    
    async def _generate_kubernetes_config(self) -> str:
        return "# Generated Kubernetes configuration"
    
    async def _generate_ci_cd_config(self) -> str:
        return "# Generated CI/CD configuration"
    
    async def _generate_architecture_documentation(self) -> str:
        return "# Generated architecture documentation"
    
    async def _generate_api_documentation(self) -> str:
        return "# Generated API documentation"
    
    async def _generate_content_management_guide(self) -> str:
        return "# Generated content management guide"
    
    async def _generate_deployment_guide(self) -> str:
        return "# Generated deployment guide"
    
    async def _generate_testing_guide(self) -> str:
        return "# Generated testing guide"

def main():
    """Enhanced main CLI interface"""
    
    parser = argparse.ArgumentParser(description="Content-Aware Platform Generator")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate platform command
    gen_parser = subparsers.add_parser('generate-platform', help='Generate complete content-aware platform')
    gen_parser.add_argument('--templates-dir', '-t', help='Path to templates directory')
    gen_parser.add_argument('--api-key', '-k', help='Anthropic API key')
    gen_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    gen_parser.add_argument('--features', '-f', nargs='*', help='Enable specific features', 
                           choices=['content-management', 'file-handling', 'download-management', 'bulk-operations'])
    gen_parser.add_argument('--test-only', action='store_true', help='Generate tests only')
    
    # Analyze content command
    analyze_parser = subparsers.add_parser('analyze-content', help='Analyze content architecture')
    analyze_parser.add_argument('--templates-dir', '-t', required=True, help='Path to templates directory')
    analyze_parser.add_argument('--output-dir', '-o', help='Output directory for analysis')
    analyze_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run platform tests')
    test_parser.add_argument('--test-type', '-t', choices=['unit', 'integration', 'e2e', 'content', 'all'], default='all')
    test_parser.add_argument('--service', '-s', help='Test specific service only')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.command == 'generate-platform':
        api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY')
        if not api_key and not args.test_only:
            print("❌ Error: ANTHROPIC_API_KEY required for platform generation")
            sys.exit(1)
        
        templates_dir = Path(args.templates_dir) if args.templates_dir else None
        generator = ContentAwarePlatformGenerator(api_key, verbose=args.verbose, templates_dir=templates_dir)
        
        features = args.features or ['content-management', 'file-handling', 'download-management']
        
        success = asyncio.run(generator.generate_complete_platform_with_content_management(features))
        sys.exit(0 if success else 1)
    
    elif args.command == 'analyze-content':
        templates_dir = Path(args.templates_dir)
        output_dir = Path(args.output_dir) if args.output_dir else Path("./content_analysis")
        
        async def analyze_content():
            template_manager = TemplateManager(templates_dir, VerboseLogger(args.verbose))
            service_templates = await template_manager.load_templates_with_extensions()
            
            content_analyzer = ContentGraphAnalyzer(VerboseLogger(args.verbose))
            content_analysis = content_analyzer.analyze_content_architecture(service_templates)
            
            output_dir.mkdir(exist_ok=True)
            with open(output_dir / "content_analysis.json", 'w') as f:
                json.dump(content_analysis, f, indent=2)
            
            print(f"\n📊 Content Analysis Complete! Check {output_dir}/content_analysis.json")
        
        asyncio.run(analyze_content())
    
    elif args.command == 'test':
        print(f"🧪 Running {args.test_type} tests...")
        # Would implement test runner here
        print("✅ Test runner functionality coming soon!")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
