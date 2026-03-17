"""
Custom exceptions for Analytics Service following SOLID principles.
Single Responsibility: Each exception handles a specific error type.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class CourseCreatorBaseException(Exception):
    """Base exception for all Course Creator service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "COURSE_CREATOR_ERROR",
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()
        
        super().__init__(self.message)
        
        # Log the exception with structured data
        logger = logging.getLogger(__name__)
        logger.error(
            f"CourseCreatorBaseException: {message}",
            extra={
                "error_code": error_code,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
                "original_exception": str(original_exception) if original_exception else None
            }
        )

class AnalyticsException(CourseCreatorBaseException):
    """Base exception for all Analytics service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "ANALYTICS_ERROR",
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
        """Log the exception with proper formatting and context."""
        logger = logging.getLogger(__name__)
        
        log_context = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "service": "analytics"
        }
        
        if self.original_exception:
            log_context["original_error"] = str(self.original_exception)
            log_context["original_type"] = type(self.original_exception).__name__
        
        logger.error(
            f"Analytics Exception: {self.error_code} - {self.message}",
            extra=log_context,
            exc_info=self.original_exception if self.original_exception else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "service": "analytics"
        }

class DataCollectionException(AnalyticsException):
    """Exception raised when data collection fails."""
    
    def __init__(
        self,
        message: str = "Data collection failed",
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        data_type: Optional[str] = None,
        collection_method: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if student_id:
            details["student_id"] = student_id
        if course_id:
            details["course_id"] = course_id
        if data_type:
            details["data_type"] = data_type
        if collection_method:
            details["collection_method"] = collection_method
            
        super().__init__(
            message=message,
            error_code="DATA_COLLECTION_ERROR",
            details=details,
            original_exception=original_exception
        )

class AnalyticsProcessingException(AnalyticsException):
    """Exception raised when analytics processing fails."""
    
    def __init__(
        self,
        message: str = "Analytics processing failed",
        processing_stage: Optional[str] = None,
        algorithm: Optional[str] = None,
        dataset_size: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if processing_stage:
            details["processing_stage"] = processing_stage
        if algorithm:
            details["algorithm"] = algorithm
        if dataset_size is not None:
            details["dataset_size"] = dataset_size
            
        super().__init__(
            message=message,
            error_code="ANALYTICS_PROCESSING_ERROR",
            details=details,
            original_exception=original_exception
        )

class ReportGenerationException(AnalyticsException):
    """Exception raised when report generation fails."""
    
    def __init__(
        self,
        message: str = "Report generation failed",
        report_type: Optional[str] = None,
        output_format: Optional[str] = None,
        template_name: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if report_type:
            details["report_type"] = report_type
        if output_format:
            details["output_format"] = output_format
        if template_name:
            details["template_name"] = template_name
            
        super().__init__(
            message=message,
            error_code="REPORT_GENERATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class StudentAnalyticsException(AnalyticsException):
    """Exception raised when student analytics operations fail."""
    
    def __init__(
        self,
        message: str = "Student analytics operation failed",
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        time_period: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if student_id:
            details["student_id"] = student_id
        if course_id:
            details["course_id"] = course_id
        if metric_type:
            details["metric_type"] = metric_type
        if time_period:
            details["time_period"] = time_period
            
        super().__init__(
            message=message,
            error_code="STUDENT_ANALYTICS_ERROR",
            details=details,
            original_exception=original_exception
        )

class LearningAnalyticsException(AnalyticsException):
    """Exception raised when learning analytics operations fail."""
    
    def __init__(
        self,
        message: str = "Learning analytics operation failed",
        course_id: Optional[str] = None,
        analysis_type: Optional[str] = None,
        location_size: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if course_id:
            details["course_id"] = course_id
        if analysis_type:
            details["analysis_type"] = analysis_type
        if location_size is not None:
            details["location_size"] = location_size
            
        super().__init__(
            message=message,
            error_code="LEARNING_ANALYTICS_ERROR",
            details=details,
            original_exception=original_exception
        )

class ValidationException(AnalyticsException):
    """Exception raised when input validation fails."""
    
    def __init__(
        self,
        message: str = "Input validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        field_name: Optional[str] = None,
        expected_format: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        if field_name:
            details["field_name"] = field_name
        if expected_format:
            details["expected_format"] = expected_format
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class DatabaseException(AnalyticsException):
    """Exception raised when database operations fail."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table_name: Optional[str] = None,
        query_type: Optional[str] = None,
        record_count: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if table_name:
            details["table_name"] = table_name
        if query_type:
            details["query_type"] = query_type
        if record_count is not None:
            details["record_count"] = record_count
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            original_exception=original_exception
        )

class DataVisualizationException(AnalyticsException):
    """Exception raised when data visualization fails."""
    
    def __init__(
        self,
        message: str = "Data visualization failed",
        chart_type: Optional[str] = None,
        data_points: Optional[int] = None,
        visualization_library: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if chart_type:
            details["chart_type"] = chart_type
        if data_points is not None:
            details["data_points"] = data_points
        if visualization_library:
            details["visualization_library"] = visualization_library
            
        super().__init__(
            message=message,
            error_code="DATA_VISUALIZATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class MetricsCalculationException(AnalyticsException):
    """Exception raised when metrics calculation fails."""
    
    def __init__(
        self,
        message: str = "Metrics calculation failed",
        metric_name: Optional[str] = None,
        calculation_method: Optional[str] = None,
        input_data_size: Optional[int] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if metric_name:
            details["metric_name"] = metric_name
        if calculation_method:
            details["calculation_method"] = calculation_method
        if input_data_size is not None:
            details["input_data_size"] = input_data_size
            
        super().__init__(
            message=message,
            error_code="METRICS_CALCULATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class PDFGenerationException(AnalyticsException):
    """Exception raised when PDF generation fails."""
    
    def __init__(
        self,
        message: str = "PDF generation failed",
        report_type: Optional[str] = None,
        template_path: Optional[str] = None,
        output_path: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if report_type:
            details["report_type"] = report_type
        if template_path:
            details["template_path"] = template_path
        if output_path:
            details["output_path"] = output_path
            
        super().__init__(
            message=message,
            error_code="PDF_GENERATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class DataNotFoundException(AnalyticsException):
    """Exception raised when requested data is not found."""
    
    def __init__(
        self,
        message: str = "Requested data not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            error_code="DATA_NOT_FOUND",
            details=details,
            original_exception=original_exception
        )

class DataValidationException(AnalyticsException):
    """Exception raised when data validation fails."""
    
    def __init__(
        self,
        message: str = "Data validation failed",
        validation_errors: Optional[Dict[str, str]] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
            
        super().__init__(
            message=message,
            error_code="DATA_VALIDATION_ERROR",
            details=details,
            original_exception=original_exception
        )

class DatabaseOperationException(AnalyticsException):
    """Exception raised when database operation fails."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="DATABASE_OPERATION_ERROR",
            details=details,
            original_exception=original_exception
        )