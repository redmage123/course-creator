"""
Backup Queries DAO - Backup and Recovery SQL Operations

BUSINESS REQUIREMENT:
Centralized SQL queries for backup and recovery operations following DAO pattern.
Supports automated backup scheduling, disaster recovery, and data integrity validation.

TECHNICAL IMPLEMENTATION:
All backup-related SQL queries isolated from business logic for better
maintainability, testing, and database schema management.

BACKUP FEATURES:
- Automated backup scheduling and execution
- Backup verification and integrity checking
- Recovery point management and retention policies
- Disaster recovery planning and execution
"""

class BackupQueries:
    """
    Centralized SQL queries for backup and recovery operations.
    Supports comprehensive backup lifecycle management.
    """
    
    # =============================================================================
    # BACKUP OPERATION QUERIES
    # =============================================================================
    
    CREATE_BACKUP_RECORD = """
        INSERT INTO backup_operations (
            backup_id, backup_type, status, started_at, file_count, 
            total_size_bytes, backup_path, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING backup_id, started_at
    """
    
    UPDATE_BACKUP_STATUS = """
        UPDATE backup_operations 
        SET status = $2, completed_at = $3, file_count = $4, 
            total_size_bytes = $5, error_message = $6
        WHERE backup_id = $1
        RETURNING completed_at
    """
    
    GET_BACKUP_STATUS = """
        SELECT backup_id, backup_type, status, started_at, completed_at,
               file_count, total_size_bytes, backup_path, error_message, metadata
        FROM backup_operations 
        WHERE backup_id = $1
    """
    
    GET_LAST_SUCCESSFUL_BACKUP = """
        SELECT MAX(completed_at) as last_backup
        FROM backup_operations 
        WHERE status = 'completed' AND backup_type = $1
    """
    
    LIST_RECENT_BACKUPS = """
        SELECT backup_id, backup_type, status, started_at, completed_at,
               file_count, total_size_bytes, backup_path
        FROM backup_operations 
        WHERE started_at > $1
        ORDER BY started_at DESC
        LIMIT $2
    """
    
    # =============================================================================
    # RECOVERY OPERATION QUERIES
    # =============================================================================
    
    CREATE_RECOVERY_RECORD = """
        INSERT INTO recovery_operations (
            recovery_id, backup_id, recovery_type, status, started_at, 
            target_path, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING recovery_id, started_at
    """
    
    UPDATE_RECOVERY_STATUS = """
        UPDATE recovery_operations 
        SET status = $2, completed_at = $3, files_recovered = $4, 
            error_message = $5
        WHERE recovery_id = $1
        RETURNING completed_at
    """
    
    GET_RECOVERY_STATUS = """
        SELECT recovery_id, backup_id, recovery_type, status, started_at,
               completed_at, files_recovered, target_path, error_message
        FROM recovery_operations 
        WHERE recovery_id = $1
    """
    
    # =============================================================================
    # BACKUP VERIFICATION QUERIES
    # =============================================================================
    
    CREATE_VERIFICATION_RECORD = """
        INSERT INTO backup_verifications (
            verification_id, backup_id, status, started_at, 
            files_verified, integrity_passed, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING verification_id, started_at
    """
    
    UPDATE_VERIFICATION_STATUS = """
        UPDATE backup_verifications 
        SET status = $2, completed_at = $3, files_verified = $4,
            integrity_passed = $5, error_message = $6
        WHERE verification_id = $1
        RETURNING completed_at
    """
    
    GET_BACKUP_INTEGRITY_STATUS = """
        SELECT backup_id, integrity_passed, files_verified, completed_at
        FROM backup_verifications 
        WHERE backup_id = $1 AND status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 1
    """
    
    # =============================================================================
    # RETENTION AND CLEANUP QUERIES
    # =============================================================================
    
    GET_EXPIRED_BACKUPS = """
        SELECT backup_id, backup_path, completed_at, total_size_bytes
        FROM backup_operations 
        WHERE status = 'completed' 
        AND completed_at < $1
        AND backup_type = $2
        ORDER BY completed_at ASC
        LIMIT $3
    """
    
    MARK_BACKUP_FOR_DELETION = """
        UPDATE backup_operations 
        SET status = 'marked_for_deletion', deletion_scheduled_at = $2
        WHERE backup_id = $1 AND status = 'completed'
        RETURNING deletion_scheduled_at
    """
    
    DELETE_BACKUP_RECORD = """
        DELETE FROM backup_operations 
        WHERE backup_id = $1 AND status = 'marked_for_deletion'
        RETURNING backup_id, backup_path
    """
    
    # =============================================================================
    # BACKUP ANALYTICS QUERIES
    # =============================================================================
    
    GET_BACKUP_STATISTICS = """
        SELECT 
            backup_type,
            COUNT(*) as total_backups,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_backups,
            AVG(total_size_bytes) as avg_backup_size,
            MAX(completed_at) as last_backup,
            MIN(started_at) as first_backup
        FROM backup_operations 
        WHERE started_at > $1
        GROUP BY backup_type
        ORDER BY backup_type
    """
    
    GET_BACKUP_PERFORMANCE_METRICS = """
        SELECT 
            DATE(started_at) as backup_date,
            COUNT(*) as daily_backups,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
            SUM(total_size_bytes) as total_data_backed_up
        FROM backup_operations 
        WHERE status = 'completed' 
        AND started_at > $1
        GROUP BY DATE(started_at)
        ORDER BY backup_date DESC
        LIMIT $2
    """