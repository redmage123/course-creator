"""
Educational Content Management Exception System - Comprehensive Error Handling

Advanced exception handling system for educational content management operations,
following SOLID principles with comprehensive error context and educational workflow integration.

## Exception Architecture Principles:

### SOLID Design Implementation
- **Single Responsibility**: Each exception handles a specific educational content error type
  with focused error context and educational workflow information
- **Open/Closed**: Extensible exception hierarchy supporting new educational content error types
  without modifying existing educational error handling infrastructure
- **Liskov Substitution**: All educational exceptions inherit consistent error handling interface
  enabling uniform educational error processing and response generation
- **Interface Segregation**: Focused exception interfaces for specific educational error contexts
  without unnecessary educational error handling complexity
- **Dependency Inversion**: Abstract exception handling supporting diverse educational error scenarios
  with consistent educational error reporting and context preservation

### Educational Error Context Preservation
- **Educational Content Context**: Comprehensive preservation of educational content information
  including course context, content type, and educational workflow state
- **Pedagogical Error Impact**: Understanding of educational error impact on learning objectives,
  course delivery, and educational content quality
- **Institutional Error Reporting**: Educational error information suitable for institutional
  reporting, compliance documentation, and educational quality assurance
- **Recovery Strategy Integration**: Educational error context supporting automated recovery
  and educational workflow continuation strategies

### Error Handling Quality Assurance
- **Comprehensive Logging**: Detailed educational error logging with structured context
  for educational workflow debugging and institutional compliance
- **Educational Audit Trail**: Complete educational error tracking for institutional
  quality assurance and educational content management accountability
- **Performance Impact Analysis**: Educational error impact assessment on educational
  content processing performance and institutional resource utilization
- **Educational Error Analytics**: Error pattern analysis for educational content
  quality improvement and institutional educational workflow optimization

## Educational Exception Categories:

### File Processing Exceptions
- **Educational Content Processing Errors**: File format, structure, and educational content issues
- **Educational Document Analysis Errors**: Content extraction and educational analysis failures
- **Educational Content Validation Errors**: Quality assurance and educational standard compliance
- **Educational File Security Errors**: Security validation and educational content safety

### AI Integration Exceptions
- **Educational Content Generation Errors**: AI service failures and educational content quality
- **Educational Content Enhancement Errors**: AI-driven improvement and validation failures
- **Educational Service Communication Errors**: AI service connectivity and response handling
- **Educational Content Validation Errors**: AI-generated content quality and compliance

### Storage and Database Exceptions
- **Educational Content Storage Errors**: File storage, retrieval, and educational content management
- **Educational Metadata Errors**: Educational content metadata and relationship management
- **Educational Database Errors**: Educational content database operations and data integrity
- **Educational Content Access Errors**: Permission, security, and educational content availability

### Content Management Exceptions
- **Educational Content Upload Errors**: Educational content upload and validation failures
- **Educational Content Export Errors**: Educational content generation and delivery failures
- **Educational Content Search Errors**: Educational content discovery and search functionality
- **Educational Template Errors**: Educational template processing and application failures

## Educational Error Handling Benefits:

### Institutional Quality Assurance
- **Educational Error Tracking**: Comprehensive monitoring of educational content errors
  for institutional quality assurance and educational workflow optimization
- **Educational Compliance Reporting**: Error reporting suitable for educational compliance
  documentation and institutional accountability requirements
- **Educational Error Analysis**: Pattern analysis for educational content quality improvement
  and institutional educational workflow enhancement

### Educational Workflow Continuity
- **Graceful Error Recovery**: Educational workflow continuation with minimal disruption
  to educational content processing and course delivery operations
- **Educational Error Communication**: Clear error communication to educational stakeholders
  with appropriate educational context and recovery guidance
- **Educational Error Prevention**: Proactive error detection and educational content
  quality assurance to prevent educational workflow disruptions

### Developer and Administrator Support
- **Educational Error Debugging**: Comprehensive error context for educational content
  development and institutional educational system maintenance
- **Educational Error Documentation**: Detailed error documentation for educational
  system administration and educational workflow troubleshooting
- **Educational Error Monitoring**: Real-time educational error monitoring and alerting
  for proactive educational system management and quality assurance

This exception system ensures robust, educational-context-aware error handling
that supports institutional educational quality requirements while maintaining
educational workflow continuity and system reliability.
"""
import logging  # Centralized educational error logging and institutional compliance tracking
from typing import Dict, Any, Optional
from datetime import datetime

class ContentManagementException(Exception):
    """
    Base exception for all educational content management service errors.
    
    Provides comprehensive error handling foundation for educational content operations
    with structured error information, educational context preservation, and
    institutional compliance support.
    
    ## Educational Error Handling Features:
    
    ### Comprehensive Error Context
    - **Educational Content Information**: Preserves educational context including course,
      content type, and educational workflow state for comprehensive error analysis
    - **Error Classification**: Structured error categorization supporting educational
      error pattern analysis and institutional quality assurance
    - **Timestamp Tracking**: Educational error occurrence tracking for educational
      workflow analysis and institutional compliance documentation
    - **Error Details**: Comprehensive error information supporting educational
      troubleshooting and institutional educational system maintenance
    
    ### Educational Audit and Compliance
    - **Structured Logging**: Educational error logging with comprehensive context
      for institutional compliance and educational quality assurance
    - **Educational Error Reporting**: Error information suitable for institutional
      reporting and educational compliance documentation
    - **Error Impact Assessment**: Educational error impact analysis for educational
      workflow optimization and institutional resource planning
    - **Recovery Information**: Error context supporting educational workflow recovery
      and educational content processing continuation
    
    ### API Integration Support
    - **Standardized Error Response**: Consistent error response format for educational
      API consumers and educational technology integration
    - **Error Code Classification**: Structured error codes supporting educational
      error handling automation and educational workflow integration
    - **Educational Context Preservation**: Educational information preservation in
      error responses for educational client applications and institutional systems
    
    Educational Benefits:
    - Comprehensive educational error tracking and institutional quality assurance
    - Educational workflow continuity with structured error recovery support
    - Educational compliance documentation and institutional accountability
    - Educational error analysis and institutional educational system optimization
    """
    """Base exception for all Content Management service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "CONTENT_MANAGEMENT_ERROR",
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()
        
        # Log the exception with proper context
        self._log_exception()
        
        super().__init__(self.message)
    
    def _log_exception(self):
        """
        Log educational content management exception with comprehensive context and structure.
        
        Provides detailed educational error logging with structured context information
        supporting institutional compliance, educational quality assurance, and system debugging.
        
        Educational Logging Features:
        - **Structured Educational Context**: Comprehensive educational information including
          course context, content type, and educational workflow state
        - **Educational Error Classification**: Error categorization supporting educational
          error pattern analysis and institutional quality improvement
        - **Educational Impact Assessment**: Error impact analysis for educational workflow
          optimization and institutional resource planning
        - **Educational Compliance Information**: Error information suitable for institutional
          compliance documentation and educational accountability
        
        Logging Context Integration:
        - **Educational Service Information**: Service identification and educational context
        - **Educational Error Details**: Comprehensive error information and educational impact
        - **Educational Timestamp Information**: Educational error occurrence tracking
        - **Educational Original Exception**: Root cause information for educational troubleshooting
        
        Educational Benefits:
        - Comprehensive educational error tracking for institutional quality assurance
        - Educational error pattern analysis for institutional educational system optimization
        - Educational compliance documentation and institutional accountability support
        - Educational troubleshooting and institutional educational system maintenance
        """
        """Log the exception with proper formatting and context."""
        logger = logging.getLogger(__name__)
        
        log_context = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "service": "content-management"
        }
        
        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__
        
        logger.error(
            f"ContentManagement Exception: {self.error_code} - {self.message}",
            extra=log_context,
            exc_info=self.original_exception if self.original_exception else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert educational content exception to structured dictionary for API responses.
        
        Provides standardized educational error response format supporting educational
        API consumers, institutional integration, and educational error handling automation.
        
        Educational Error Response Structure:
        - **Educational Error Code**: Structured error classification supporting educational
          error handling automation and institutional educational system integration
        - **Educational Error Message**: Clear educational error description with
          appropriate educational context and institutional terminology
        - **Educational Error Details**: Comprehensive educational error information
          supporting educational troubleshooting and institutional quality assurance
        - **Educational Service Information**: Service identification and educational context
          for institutional educational system monitoring and management
        
        API Integration Benefits:
        - **Standardized Educational Error Format**: Consistent error response structure
          for educational API consumers and institutional educational technology integration
        - **Educational Error Automation**: Structured error information supporting
          educational error handling automation and institutional workflow optimization
        - **Educational Error Monitoring**: Error information suitable for institutional
          educational system monitoring and educational quality assurance
        - **Educational Error Analytics**: Error data supporting institutional educational
          error pattern analysis and educational system optimization
        
        Returns:
            Dict containing structured educational error information with:
                - Educational error classification and identification
                - Educational error context and impact information
                - Educational service information and context
                - Educational timestamp and occurrence tracking
                
        Educational Use Cases:
        - Educational API error response generation and client integration
        - Educational error monitoring and institutional quality assurance
        - Educational error analytics and institutional educational system optimization
        - Educational compliance documentation and institutional accountability
        """
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "service": "content-management"
        }

class FileProcessingException(ContentManagementException):
    """
    Exception for educational content file processing failures.
    
    Handles errors in educational content file processing including document parsing,
    content extraction, educational analysis, and format conversion operations.
    
    ## Educational File Processing Error Scenarios:
    
    ### Document Format and Structure Errors
    - **Educational Document Parsing Failures**: PDF, DOCX, PPTX parsing errors with educational context
    - **Educational Content Structure Issues**: Malformed educational documents and content organization
    - **Educational Format Validation Errors**: Educational content format compliance and standard validation
    - **Educational Content Extraction Failures**: Text and metadata extraction from educational documents
    
    ### Educational Content Analysis Errors
    - **Syllabus Analysis Failures**: Educational structure recognition and learning objective extraction
    - **Educational Content Classification Errors**: Content type identification and educational taxonomy
    - **Educational Quality Assessment Failures**: Educational content quality validation and compliance
    - **Educational Metadata Extraction Errors**: Educational context and relationship information processing
    
    Educational Context Preservation:
    - **File Information**: Educational document details and processing context
    - **Processing Stage**: Educational content processing workflow stage and operation
    - **Educational Impact**: Error impact on educational workflow and content quality
    - **Recovery Options**: Educational content processing recovery and alternative approaches
    
    Use Cases:
    - Educational document upload and processing error handling
    - Educational content analysis and validation error management
    - Educational file format conversion and transformation error handling
    - Educational content quality assurance and compliance error processing
    """
    """Exception raised when file processing fails."""
    
    def __init__(
        self,
        message: str = "File processing failed",
        file_path: Optional[str] = None,
        file_type: Optional[str] = None,
        processing_stage: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if file_path:
            details["file_path"] = file_path
        if file_type:
            details["file_type"] = file_type
        if processing_stage:
            details["processing_stage"] = processing_stage
            
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details=details,
            original_exception=original_exception
        )

class ContentUploadException(ContentManagementException):
    """Exception raised when content upload fails."""
    
    def __init__(
        self,
        message: str = "Content upload failed",
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        content_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if file_size is not None:
            details["file_size"] = file_size
        if content_type:
            details["content_type"] = content_type
            
        super().__init__(
            message=message,
            error_code="CONTENT_UPLOAD_ERROR",
            details=details,
            original_exception=original_exception
        )

class ContentExportException(ContentManagementException):
    """Exception raised when content export fails."""
    
    def __init__(
        self,
        message: str = "Content export failed",
        export_format: Optional[str] = None,
        course_id: Optional[str] = None,
        content_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if export_format:
            details["export_format"] = export_format
        if course_id:
            details["course_id"] = course_id
        if content_type:
            details["content_type"] = content_type
            
        super().__init__(
            message=message,
            error_code="CONTENT_EXPORT_ERROR",
            details=details,
            original_exception=original_exception
        )

class AIIntegrationException(ContentManagementException):
    """
    Exception for educational content AI service integration failures.
    
    Handles errors in AI-driven educational content generation, enhancement,
    and validation operations with comprehensive educational context preservation.
    
    ## AI Educational Content Error Scenarios:
    
    ### Educational Content Generation Failures
    - **Educational Content Creation Errors**: AI service failures in educational content generation
    - **Educational Quality Validation Errors**: AI-generated content quality and compliance issues
    - **Educational Content Enhancement Failures**: AI-driven content improvement and optimization errors
    - **Educational Template Application Errors**: AI template processing and educational design failures
    
    ### AI Service Communication Errors
    - **Educational AI Service Connectivity**: Network and authentication failures for educational AI services
    - **Educational AI Service Response Errors**: Invalid or incomplete educational content responses
    - **Educational AI Service Timeout Errors**: Educational content generation timeout and performance issues
    - **Educational AI Service Rate Limiting**: Educational content generation capacity and usage limits
    
    Educational AI Integration Context:
    - **AI Service Information**: Educational AI service details and configuration context
    - **Educational Operation**: Specific educational content generation or enhancement operation
    - **Educational Prompt Context**: Educational content generation prompts and requirements
    - **Educational Content Impact**: Error impact on educational content quality and delivery
    
    Educational Benefits:
    - Comprehensive educational AI error tracking and service reliability monitoring
    - Educational content generation workflow continuity with fallback mechanisms
    - Educational AI service optimization and institutional educational technology planning
    - Educational content quality assurance and AI-generated content validation
    
    Use Cases:
    - Educational content generation error handling and fallback activation
    - Educational AI service monitoring and institutional service reliability tracking
    - Educational content quality validation and AI-generated content compliance
    - Educational AI integration debugging and institutional educational technology optimization
    """
    """Exception raised when AI integration fails."""
    
    def __init__(
        self,
        message: str = "AI integration failed",
        ai_service: Optional[str] = None,
        operation: Optional[str] = None,
        prompt_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if ai_service:
            details["ai_service"] = ai_service
        if operation:
            details["operation"] = operation
        if prompt_type:
            details["prompt_type"] = prompt_type
            
        super().__init__(
            message=message,
            error_code="AI_INTEGRATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class ValidationException(ContentManagementException):
    """
    Exception for educational content input validation failures.
    
    Handles comprehensive validation errors for educational content including data validation,
    educational standard compliance, and pedagogical requirement verification.
    
    ## Educational Validation Error Categories:
    
    ### Educational Content Data Validation
    - **Educational Content Structure Validation**: Required fields and educational content organization
    - **Educational Content Format Validation**: Educational content format compliance and standards
    - **Educational Content Size Validation**: Educational content size limits and resource constraints
    - **Educational Content Type Validation**: Educational content classification and taxonomy compliance
    
    ### Educational Standard Compliance
    - **Educational Quality Standards**: Educational content quality requirements and institutional policies
    - **Educational Accessibility Standards**: Educational content accessibility and universal design compliance
    - **Educational Pedagogy Standards**: Educational content pedagogical appropriateness and effectiveness
    - **Educational Institution Standards**: Institutional educational content policies and requirements
    
    Educational Validation Context:
    - **Validation Errors**: Comprehensive educational content validation error details
    - **Field Information**: Specific educational content fields and validation requirements
    - **Educational Standards**: Educational standard compliance requirements and expectations
    - **Educational Impact**: Validation error impact on educational content quality and compliance
    
    Educational Benefits:
    - Comprehensive educational content quality assurance and validation
    - Educational standard compliance verification and institutional policy enforcement
    - Educational content improvement guidance and quality enhancement recommendations
    - Educational workflow integrity and institutional educational content consistency
    
    Use Cases:
    - Educational content upload validation and quality assurance
    - Educational content creation validation and standard compliance verification
    - Educational content modification validation and change impact assessment
    - Educational content export validation and delivery quality assurance
    """
    """Exception raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Input validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        field_name: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if field_name:
            details["field_name"] = field_name
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class ContentNotFoundException(ContentManagementException):
    """
    Exception for educational content discovery and access failures.
    
    Handles educational content not found scenarios including missing educational content,
    access permission issues, and educational content availability problems.
    
    ## Educational Content Access Error Scenarios:
    
    ### Educational Content Availability
    - **Missing Educational Content**: Educational content deletion or unavailability
    - **Educational Content Access Restrictions**: Permission and security access limitations
    - **Educational Content Status Issues**: Educational content status and availability changes
    - **Educational Content Location Errors**: Educational content storage and retrieval failures
    
    ### Educational Content Discovery
    - **Educational Content Search Failures**: Educational content discovery and search result issues
    - **Educational Content Reference Errors**: Educational content relationship and reference failures
    - **Educational Content Index Issues**: Educational content indexing and discovery system problems
    - **Educational Content Metadata Errors**: Educational content metadata and classification issues
    
    Educational Content Context:
    - **Content Identification**: Educational content ID and identification information
    - **Educational Content Type**: Educational content classification and type information
    - **Search Criteria**: Educational content search and discovery criteria
    - **Educational Access Context**: Educational content access context and permission information
    
    Educational Benefits:
    - Educational content availability monitoring and access issue resolution
    - Educational content discovery optimization and search result improvement
    - Educational content access control and permission management
    - Educational workflow continuity and alternative content recommendation
    
    Use Cases:
    - Educational content retrieval error handling and alternative content suggestion
    - Educational content search result optimization and discovery improvement
    - Educational content access permission management and security enforcement
    - Educational content availability monitoring and institutional content management
    """
    """Exception raised when content is not found."""
    
    def __init__(
        self,
        message: str = "Content not found",
        content_id: Optional[str] = None,
        content_type: Optional[str] = None,
        search_criteria: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if content_id:
            details["content_id"] = content_id
        if content_type:
            details["content_type"] = content_type
        if search_criteria:
            details["search_criteria"] = search_criteria
            
        super().__init__(
            message=message,
            error_code="CONTENT_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )

class DatabaseException(ContentManagementException):
    """Exception raised when database operations fail."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table_name:
            details["table_name"] = table_name
        if record_id:
            details["record_id"] = record_id
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            original_exception=original_exception
        )

class StorageException(ContentManagementException):
    """
    Exception for educational content storage operation failures.
    
    Handles comprehensive storage errors for educational content including file system issues,
    storage capacity problems, and educational content storage operation failures.
    
    ## Educational Storage Error Categories:
    
    ### Educational Content Storage Operations
    - **Educational Content Upload Failures**: Educational content file upload and storage errors
    - **Educational Content Retrieval Failures**: Educational content access and download errors
    - **Educational Content Modification Failures**: Educational content update and change errors
    - **Educational Content Deletion Failures**: Educational content removal and cleanup errors
    
    ### Educational Storage System Issues
    - **Educational Storage Capacity Issues**: Educational content storage space and resource limitations
    - **Educational Storage Performance Issues**: Educational content storage speed and efficiency problems
    - **Educational Storage Security Issues**: Educational content storage security and access control errors
    - **Educational Storage Integrity Issues**: Educational content storage corruption and data integrity problems
    
    Educational Storage Context:
    - **Storage Path Information**: Educational content storage location and file system details
    - **Storage Operation**: Specific educational content storage operation and context
    - **Storage Type**: Educational content storage system type and configuration
    - **Educational Impact**: Storage error impact on educational content availability and quality
    
    Educational Benefits:
    - Comprehensive educational content storage monitoring and issue resolution
    - Educational storage optimization and institutional resource planning
    - Educational content integrity assurance and data protection
    - Educational storage performance optimization and institutional infrastructure planning
    
    Use Cases:
    - Educational content upload error handling and storage optimization
    - Educational content backup and recovery operation error management
    - Educational storage capacity planning and institutional resource optimization
    - Educational content storage security and access control error handling
    """
    """Exception raised when storage operations fail."""
    
    def __init__(
        self,
        message: str = "Storage operation failed",
        storage_path: Optional[str] = None,
        operation: Optional[str] = None,
        storage_type: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if storage_path:
            details["storage_path"] = storage_path
        if operation:
            details["operation"] = operation
        if storage_type:
            details["storage_type"] = storage_type
            
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            details=details,
            original_exception=original_exception
        )

class ContentSearchException(ContentManagementException):
    """
    Exception for educational content search and discovery operation failures.
    
    Handles errors in educational content search functionality including search index issues,
    query processing failures, and educational content discovery system problems.
    
    ## Educational Search Error Categories:
    
    ### Educational Content Search Operations
    - **Educational Search Query Failures**: Educational content search query processing and execution errors
    - **Educational Search Index Failures**: Educational content search index corruption and maintenance errors
    - **Educational Search Performance Issues**: Educational content search speed and efficiency problems
    - **Educational Search Result Issues**: Educational content search result generation and formatting errors
    
    ### Educational Discovery System Issues
    - **Educational Content Classification Errors**: Educational content taxonomy and classification failures
    - **Educational Content Recommendation Errors**: Educational content recommendation algorithm and suggestion failures
    - **Educational Content Relationship Errors**: Educational content relationship mapping and dependency errors
    - **Educational Content Analytics Errors**: Educational content usage analytics and pattern analysis failures
    
    Educational Search Context:
    - **Search Query Information**: Educational content search terms and query parameters
    - **Search Type**: Educational content search type and discovery method
    - **Search Filters**: Educational content filtering criteria and search constraints
    - **Educational Impact**: Search error impact on educational content discovery and access
    
    Educational Benefits:
    - Comprehensive educational content search optimization and discovery improvement
    - Educational content organization and classification enhancement
    - Educational content recommendation accuracy and relevance improvement
    - Educational search performance optimization and institutional search system planning
    
    Use Cases:
    - Educational content search error handling and alternative discovery methods
    - Educational content search optimization and institutional search system improvement
    - Educational content recommendation enhancement and personalization error handling
    - Educational search analytics and institutional content discovery optimization
    """
    """Exception raised when content search operations fail."""
    
    def __init__(
        self,
        message: str = "Content search failed",
        search_query: Optional[str] = None,
        search_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if search_query:
            details["search_query"] = search_query
        if search_type:
            details["search_type"] = search_type
        if filters:
            details["filters"] = filters
            
        super().__init__(
            message=message,
            error_code="CONTENT_SEARCH_ERROR",
            details=details,
            original_exception=original_exception
        )

class TemplateException(ContentManagementException):
    """
    Exception for educational content template processing failures.
    
    Handles errors in educational template application, customization, and educational
    content generation using institutional and pedagogical templates.
    
    ## Educational Template Error Categories:
    
    ### Educational Template Processing
    - **Educational Template Loading Failures**: Educational template file access and format errors
    - **Educational Template Parsing Failures**: Educational template structure and syntax errors
    - **Educational Template Variable Errors**: Educational template variable processing and substitution errors
    - **Educational Template Validation Errors**: Educational template compliance and standard validation errors
    
    ### Educational Template Application
    - **Educational Template Customization Errors**: Educational template adaptation and personalization failures
    - **Educational Template Integration Errors**: Educational template application to educational content failures
    - **Educational Template Output Errors**: Educational template result generation and formatting failures
    - **Educational Template Quality Errors**: Educational template output quality and compliance issues
    
    Educational Template Context:
    - **Template Information**: Educational template details and configuration
    - **Template Type**: Educational template classification and application type
    - **Template Variables**: Educational template variables and customization parameters
    - **Educational Impact**: Template error impact on educational content generation and quality
    
    Educational Benefits:
    - Comprehensive educational template quality assurance and validation
    - Educational template optimization and institutional template management
    - Educational content consistency and institutional branding compliance
    - Educational template performance optimization and institutional design standard enforcement
    
    Use Cases:
    - Educational template application error handling and alternative template selection
    - Educational template customization error management and institutional template optimization
    - Educational template quality validation and institutional design standard compliance
    - Educational template performance optimization and institutional educational technology planning
    """
    """Exception raised when template processing fails."""
    
    def __init__(
        self,
        message: str = "Template processing failed",
        template_name: Optional[str] = None,
        template_type: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if template_name:
            details["template_name"] = template_name
        if template_type:
            details["template_type"] = template_type
        if variables:
            details["variables"] = list(variables.keys()) if variables else []
            
        super().__init__(
            message=message,
            error_code="TEMPLATE_ERROR",
            details=details,
            original_exception=original_exception
        )