"""
Content Queries DAO - Centralized SQL Query Management for Content Operations

BUSINESS REQUIREMENT:
All SQL queries for content metadata operations centralized in one locations following
DAO (Data Access Object) pattern for better maintainability and separation of concerns.

TECHNICAL IMPLEMENTATION:
Static class containing all SQL queries as string constants, eliminating
inline SQL in repository classes and providing single source of truth
for content database schema interactions.

QUERY CATEGORIES:
- Content CRUD Operations: Create, read, update, delete content records
- Search Operations: Advanced search with multiple filter criteria
- Metadata Operations: Content metadata and classification management
- Analytics Operations: Content usage statistics and reporting
"""

class ContentQueries:
    """
    Centralized SQL queries for content operations following DAO pattern.
    All queries are static constants for consistency and maintainability.
    """
    
    # =============================================================================
    # CONTENT CRUD OPERATIONS
    # =============================================================================
    
    CREATE_CONTENT = """
        INSERT INTO content_storage (
            id, filename, display_name, description, content_type, 
            tags, storage_path, is_public, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id, created_at
    """
    
    GET_CONTENT_BY_ID = """
        SELECT * FROM content_storage 
        WHERE id = $1 AND status != $2
    """
    
    GET_CONTENT_BY_FILENAME = """
        SELECT * FROM content_storage 
        WHERE filename = $1 AND uploaded_by = $2 AND status != $3
    """
    
    GET_CONTENT_BY_FILENAME_ONLY = """
        SELECT * FROM content_storage 
        WHERE filename = $1 AND status != $2
    """
    
    UPDATE_CONTENT_METADATA = """
        UPDATE content_storage 
        SET display_name = $2, description = $3, tags = $4, 
            is_public = $5, updated_at = $6
        WHERE id = $1 AND status != $7
        RETURNING updated_at
    """
    
    SOFT_DELETE_CONTENT = """
        UPDATE content_storage 
        SET status = $2, updated_at = $3, deleted_at = $3
        WHERE id = $1 AND status != $2
        RETURNING deleted_at
    """
    
    HARD_DELETE_CONTENT = """
        DELETE FROM content_storage 
        WHERE id = $1 AND status = $2
        RETURNING id, filename, storage_path
    """
    
    # =============================================================================
    # CONTENT SEARCH AND DISCOVERY
    # =============================================================================
    
    SEARCH_CONTENT_BASE = """
        SELECT id, filename, display_name, description, content_type,
               tags, storage_path, is_public, created_at, updated_at,
               uploaded_by, file_size, access_count
        FROM content_storage 
        WHERE status != $1
    """
    
    SEARCH_BY_CONTENT_TYPE = """
        SELECT id, filename, display_name, description, content_type,
               tags, storage_path, is_public, created_at, updated_at,
               uploaded_by, file_size, access_count
        FROM content_storage 
        WHERE status != $1 AND content_type = $2
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
    """
    
    SEARCH_BY_TAGS = """
        SELECT id, filename, display_name, description, content_type,
               tags, storage_path, is_public, created_at, updated_at,
               uploaded_by, file_size, access_count
        FROM content_storage 
        WHERE status != $1 AND tags && $2
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
    """
    
    SEARCH_BY_USER = """
        SELECT id, filename, display_name, description, content_type,
               tags, storage_path, is_public, created_at, updated_at,
               uploaded_by, file_size, access_count
        FROM content_storage 
        WHERE status != $1 AND uploaded_by = $2
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
    """
    
    FULL_TEXT_SEARCH = """
        SELECT id, filename, display_name, description, content_type,
               tags, storage_path, is_public, created_at, updated_at,
               uploaded_by, file_size, access_count,
               ts_rank(to_tsvector('english', display_name || ' ' || description), 
                      plainto_tsquery('english', $2)) as rank
        FROM content_storage 
        WHERE status != $1 
        AND (to_tsvector('english', display_name || ' ' || description) @@ plainto_tsquery('english', $2))
        ORDER BY rank DESC, created_at DESC
        LIMIT $3 OFFSET $4
    """
    
    # =============================================================================
    # CONTENT ANALYTICS AND STATISTICS
    # =============================================================================
    
    GET_CONTENT_USAGE_STATS = """
        SELECT 
            COUNT(*) as total_content,
            COUNT(CASE WHEN is_public = true THEN 1 END) as public_content,
            COUNT(CASE WHEN is_public = false THEN 1 END) as private_content,
            SUM(file_size) as total_size_bytes,
            AVG(file_size) as avg_file_size,
            SUM(access_count) as total_access_count,
            MAX(created_at) as last_upload,
            MIN(created_at) as first_upload
        FROM content_storage 
        WHERE status != $1
    """
    
    GET_CONTENT_BY_TYPE_STATS = """
        SELECT 
            content_type,
            COUNT(*) as content_count,
            SUM(file_size) as total_size,
            AVG(access_count) as avg_access_count,
            MAX(created_at) as latest_content
        FROM content_storage 
        WHERE status != $1
        GROUP BY content_type
        ORDER BY content_count DESC
    """
    
    GET_POPULAR_CONTENT = """
        SELECT id, filename, display_name, content_type,
               access_count, created_at, uploaded_by
        FROM content_storage 
        WHERE status != $1 AND is_public = true
        ORDER BY access_count DESC, created_at DESC
        LIMIT $2
    """
    
    GET_RECENT_CONTENT = """
        SELECT id, filename, display_name, content_type,
               created_at, uploaded_by, file_size
        FROM content_storage 
        WHERE status != $1 
        AND created_at > $2
        ORDER BY created_at DESC
        LIMIT $3
    """
    
    # =============================================================================
    # ACCESS TRACKING AND MONITORING
    # =============================================================================
    
    INCREMENT_ACCESS_COUNT = """
        UPDATE content_storage 
        SET access_count = access_count + 1, last_accessed_at = $2
        WHERE id = $1 AND status != $3
        RETURNING access_count, last_accessed_at
    """
    
    LOG_CONTENT_ACCESS = """
        INSERT INTO content_access_log (
            content_id, user_id, access_type, ip_address, user_agent, accessed_at
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, accessed_at
    """
    
    GET_ACCESS_STATISTICS = """
        SELECT 
            content_id,
            COUNT(*) as total_accesses,
            COUNT(DISTINCT user_id) as unique_users,
            MAX(accessed_at) as last_access,
            MIN(accessed_at) as first_access
        FROM content_access_log 
        WHERE accessed_at > $1
        GROUP BY content_id
        ORDER BY total_accesses DESC
        LIMIT $2
    """
    
    # =============================================================================
    # CONTENT MAINTENANCE AND CLEANUP
    # =============================================================================
    
    GET_ORPHANED_CONTENT = """
        SELECT id, filename, storage_path, deleted_at, file_size
        FROM content_storage 
        WHERE status = $1 
        AND deleted_at < $2
        ORDER BY deleted_at ASC
        LIMIT $3
    """
    
    GET_UNUSED_CONTENT = """
        SELECT id, filename, storage_path, created_at, access_count
        FROM content_storage 
        WHERE status != $1 
        AND access_count = 0 
        AND created_at < $2
        ORDER BY created_at ASC
        LIMIT $3
    """
    
    GET_LARGE_CONTENT_FILES = """
        SELECT id, filename, storage_path, file_size, created_at
        FROM content_storage 
        WHERE status != $1 AND file_size > $2
        ORDER BY file_size DESC
        LIMIT $3
    """
    
    # =============================================================================
    # CONTENT LISTING AND PAGINATION
    # =============================================================================
    
    LIST_CONTENT_BY_USER = """
        SELECT * FROM content_storage 
        WHERE uploaded_by = $1 AND status != $2 
        ORDER BY created_at DESC 
        LIMIT $3 OFFSET $4
    """
    
    LIST_ALL_CONTENT = """
        SELECT * FROM content_storage 
        WHERE status != $1 
        ORDER BY created_at DESC 
        LIMIT $2 OFFSET $3
    """
    
    COUNT_CONTENT_BY_USER = """
        SELECT COUNT(*) as count FROM content_storage 
        WHERE uploaded_by = $1 AND status != $2
    """
    
    COUNT_ALL_CONTENT = """
        SELECT COUNT(*) as count FROM content_storage 
        WHERE status != $1
    """
    
    # =============================================================================
    # CONTENT UPDATE OPERATIONS
    # =============================================================================
    
    UPDATE_CONTENT_PARTIAL = """
        UPDATE content_storage 
        SET {update_fields}, updated_at = ${param_count}
        WHERE id = ${content_id_param}
        RETURNING *
    """
    
    SOFT_DELETE_CONTENT_SIMPLE = """
        UPDATE content_storage 
        SET status = $1, updated_at = $2 
        WHERE id = $3 AND status != $1
        RETURNING id
    """
    
    HARD_DELETE_CONTENT_SIMPLE = """
        DELETE FROM content_storage WHERE id = $1 RETURNING id
    """
    
    UPDATE_ACCESS_COUNT = """
        UPDATE content_storage 
        SET access_count = access_count + 1, last_accessed = $1, updated_at = $1
        WHERE id = $2
        RETURNING id
    """
    
    # =============================================================================
    # CONTENT STATISTICS QUERIES
    # =============================================================================
    
    GET_CONTENT_TOTAL_STATS = """
        SELECT 
            COUNT(*) as total_files,
            COALESCE(SUM(size), 0) as total_size,
            COALESCE(AVG(size), 0) as average_file_size
        FROM content_storage 
        WHERE status != $1
    """
    
    GET_CONTENT_TOTAL_STATS_BY_USER = """
        SELECT 
            COUNT(*) as total_files,
            COALESCE(SUM(size), 0) as total_size,
            COALESCE(AVG(size), 0) as average_file_size
        FROM content_storage 
        WHERE status != $1 AND uploaded_by = $2
    """
    
    GET_CONTENT_BY_TYPE_COUNTS = """
        SELECT content_type, COUNT(*) as count
        FROM content_storage 
        WHERE status != $1
        GROUP BY content_type
    """
    
    GET_CONTENT_BY_TYPE_COUNTS_BY_USER = """
        SELECT content_type, COUNT(*) as count
        FROM content_storage 
        WHERE status != $1 AND uploaded_by = $2
        GROUP BY content_type
    """
    
    GET_CONTENT_BY_CATEGORY_COUNTS = """
        SELECT content_category, COUNT(*) as count
        FROM content_storage 
        WHERE status != $1
        GROUP BY content_category
    """
    
    GET_CONTENT_BY_CATEGORY_COUNTS_BY_USER = """
        SELECT content_category, COUNT(*) as count
        FROM content_storage 
        WHERE status != $1 AND uploaded_by = $2
        GROUP BY content_category
    """
    
    GET_MOST_ACCESSED_CONTENT = """
        SELECT filename, access_count, last_accessed
        FROM content_storage 
        WHERE status != $1
        ORDER BY access_count DESC, last_accessed DESC
        LIMIT 10
    """
    
    GET_MOST_ACCESSED_CONTENT_BY_USER = """
        SELECT filename, access_count, last_accessed
        FROM content_storage 
        WHERE status != $1 AND uploaded_by = $2
        ORDER BY access_count DESC, last_accessed DESC
        LIMIT 10
    """