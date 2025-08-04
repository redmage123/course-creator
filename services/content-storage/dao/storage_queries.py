"""
Storage Queries DAO - Centralized SQL Query Management

BUSINESS REQUIREMENT:
All SQL queries for storage operations centralized in one location following
DAO (Data Access Object) pattern for better maintainability and separation of concerns.

TECHNICAL IMPLEMENTATION:
Static class containing all SQL queries as string constants, eliminating
inline SQL in repository classes and providing single source of truth
for database schema interactions.

QUERY CATEGORIES:
- File Operations: Create, read, update, delete file records
- Storage Operations: Backup, restore, cleanup operations
- Metadata Operations: File metadata and version management
- Analytics Operations: Storage usage and performance metrics
"""

class StorageQueries:
    """
    Centralized SQL queries for storage operations following DAO pattern.
    All queries are static constants for consistency and maintainability.
    """
    
    # =============================================================================
    # FILE OPERATIONS QUERIES
    # =============================================================================
    
    CREATE_FILE_RECORD = """
        INSERT INTO storage_files (
            file_id, filename, file_path, size_bytes, content_type, 
            checksum, created_at, updated_at, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING file_id, created_at
    """
    
    GET_FILE_BY_ID = """
        SELECT file_id, filename, file_path, size_bytes, content_type,
               checksum, created_at, updated_at, metadata, is_deleted
        FROM storage_files 
        WHERE file_id = $1 AND is_deleted = FALSE
    """
    
    GET_FILE_BY_PATH = """
        SELECT file_id, filename, file_path, size_bytes, content_type,
               checksum, created_at, updated_at, metadata, is_deleted
        FROM storage_files 
        WHERE file_path = $1 AND is_deleted = FALSE
    """
    
    UPDATE_FILE_METADATA = """
        UPDATE storage_files 
        SET metadata = $2, updated_at = $3
        WHERE file_id = $1 AND is_deleted = FALSE
        RETURNING updated_at
    """
    
    SOFT_DELETE_FILE = """
        UPDATE storage_files 
        SET is_deleted = TRUE, deleted_at = $2, updated_at = $2
        WHERE file_id = $1 AND is_deleted = FALSE
        RETURNING deleted_at
    """
    
    LIST_FILES_PAGINATED = """
        SELECT file_id, filename, file_path, size_bytes, content_type,
               checksum, created_at, updated_at, metadata
        FROM storage_files 
        WHERE is_deleted = FALSE
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
    """
    
    # =============================================================================
    # STORAGE OPERATIONS QUERIES  
    # =============================================================================
    
    CREATE_STORAGE_OPERATION = """
        INSERT INTO storage_operations (
            operation_id, operation_type, status, file_id, 
            started_at, completed_at, error_message, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING operation_id, started_at
    """
    
    UPDATE_OPERATION_STATUS = """
        UPDATE storage_operations 
        SET status = $2, completed_at = $3, error_message = $4
        WHERE operation_id = $1
        RETURNING completed_at
    """
    
    GET_OPERATION_STATUS = """
        SELECT operation_id, operation_type, status, file_id,
               started_at, completed_at, error_message, metadata
        FROM storage_operations 
        WHERE operation_id = $1
    """
    
    LIST_OPERATIONS_BY_TYPE = """
        SELECT operation_id, operation_type, status, file_id,
               started_at, completed_at, error_message
        FROM storage_operations 
        WHERE operation_type = $1
        ORDER BY started_at DESC
        LIMIT $2 OFFSET $3
    """
    
    # =============================================================================
    # ANALYTICS AND MONITORING QUERIES
    # =============================================================================
    
    GET_STORAGE_USAGE_STATS = """
        SELECT 
            COUNT(*) as total_files,
            SUM(size_bytes) as total_size_bytes,
            AVG(size_bytes) as avg_file_size,
            MAX(created_at) as last_upload,
            MIN(created_at) as first_upload
        FROM storage_files 
        WHERE is_deleted = FALSE
    """
    
    GET_FILES_BY_TYPE_STATS = """
        SELECT 
            content_type,
            COUNT(*) as file_count,
            SUM(size_bytes) as total_size
        FROM storage_files 
        WHERE is_deleted = FALSE
        GROUP BY content_type
        ORDER BY total_size DESC
    """
    
    GET_RECENT_OPERATIONS_SUMMARY = """
        SELECT 
            operation_type,
            status,
            COUNT(*) as operation_count,
            MAX(completed_at) as last_operation
        FROM storage_operations 
        WHERE started_at > $1
        GROUP BY operation_type, status
        ORDER BY operation_type, status
    """
    
    # =============================================================================
    # CLEANUP AND MAINTENANCE QUERIES
    # =============================================================================
    
    GET_ORPHANED_FILES = """
        SELECT file_id, file_path, size_bytes, deleted_at
        FROM storage_files 
        WHERE is_deleted = TRUE 
        AND deleted_at < $1
        ORDER BY deleted_at ASC
        LIMIT $2
    """
    
    PERMANENTLY_DELETE_FILE = """
        DELETE FROM storage_files 
        WHERE file_id = $1 AND is_deleted = TRUE
        RETURNING file_id, file_path
    """
    
    GET_LARGE_FILES = """
        SELECT file_id, filename, file_path, size_bytes, created_at
        FROM storage_files 
        WHERE size_bytes > $1 AND is_deleted = FALSE
        ORDER BY size_bytes DESC
        LIMIT $2
    """
    
    # =============================================================================
    # STORAGE STATISTICS QUERIES
    # =============================================================================
    
    GET_CONTENT_STORAGE_STATS = """
        SELECT 
            COUNT(*) as total_files,
            COALESCE(SUM(size), 0) as total_size
        FROM content 
        WHERE status != 'deleted'
    """
    
    GET_CONTENT_BY_TYPE_DISTRIBUTION = """
        SELECT content_type, COUNT(*) as count
        FROM content 
        WHERE status != 'deleted'
        GROUP BY content_type
    """
    
    GET_CONTENT_SIZE_BY_TYPE_DISTRIBUTION = """
        SELECT content_type, COALESCE(SUM(size), 0) as total_size
        FROM content 
        WHERE status != 'deleted'
        GROUP BY content_type
    """
    
    GET_RECENT_UPLOAD_COUNT = """
        SELECT COUNT(*) as recent_uploads
        FROM content 
        WHERE status != 'deleted' 
        AND created_at >= $1
    """
    
    # =============================================================================
    # QUOTA MANAGEMENT QUERIES
    # =============================================================================
    
    GET_USER_QUOTA_INFO = """
        SELECT 
            user_id,
            quota_limit,
            quota_used,
            file_count_limit,
            file_count_used
        FROM storage_quotas 
        WHERE user_id = $1
    """
    
    UPDATE_USER_QUOTA_USAGE = """
        UPDATE storage_quotas 
        SET 
            quota_used = quota_used + $1,
            file_count_used = file_count_used + $2
        WHERE user_id = $3
        RETURNING user_id
    """
    
    CREATE_USER_QUOTA_ON_CONFLICT = """
        INSERT INTO storage_quotas (user_id, quota_limit, quota_used, file_count_used)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO UPDATE SET
            quota_used = storage_quotas.quota_used + $3,
            file_count_used = storage_quotas.file_count_used + $4
    """
    
    # =============================================================================
    # STORAGE OPERATIONS LOGGING QUERIES
    # =============================================================================
    
    LOG_STORAGE_OPERATION = """
        INSERT INTO storage_operations (
            id, operation_type, file_path, status, size, 
            duration, error_message, metadata, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    """
    
    GET_RECENT_STORAGE_OPERATIONS = """
        SELECT * FROM storage_operations 
        ORDER BY created_at DESC 
        LIMIT $1
    """
    
    DELETE_OLD_STORAGE_OPERATIONS = """
        DELETE FROM storage_operations WHERE created_at < $1
    """
    
    # =============================================================================
    # ERROR RATE CALCULATION QUERIES
    # =============================================================================
    
    GET_OPERATION_ERROR_STATS = """
        SELECT 
            COUNT(*) as total_ops,
            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_ops
        FROM storage_operations 
        WHERE created_at >= $1
    """