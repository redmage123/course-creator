#!/usr/bin/env python3
"""
Database setup script for Course Creator platform - Fixed for asyncpg
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Use course_user for application operations
APP_URL = "postgresql+asyncpg://course_user@localhost:5432/course_creator"
ADMIN_URL = "postgresql+asyncpg://course_user@localhost:5432/postgres"

async def create_database():
    """Create the main database if it doesn't exist"""
    engine = create_async_engine(ADMIN_URL)
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname='course_creator'")
            )
            exists = result.fetchone()
            
            if not exists:
                await conn.execute(text("CREATE DATABASE course_creator"))
                print("✅ Created course_creator database")
            else:
                print("✅ Database course_creator already exists")
    except Exception as e:
        print(f"⚠️  Database creation info: {e}")
    finally:
        await engine.dispose()

async def execute_sql_statements(conn, statements, description):
    """Execute a list of SQL statements individually"""
    executed = 0
    for i, stmt in enumerate(statements):
        if stmt.strip() and not stmt.strip().startswith('--'):
            try:
                await conn.execute(text(stmt))
                executed += 1
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"⚠️  Warning executing statement {i+1}: {e}")
    
    print(f"✅ {description}: {executed} statements executed")
    return executed

async def create_tables_from_schema():
    """Create tables using individual SQL statements"""
    
    engine = create_async_engine(APP_URL, echo=False)
    
    # Split schema into individual statements
    schema_statements = [
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"",
        
        """CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(100) NOT NULL UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            is_verified BOOLEAN DEFAULT false,
            role VARCHAR(50) DEFAULT 'student',
            avatar_url TEXT,
            bio TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP WITH TIME ZONE
        )""",
        
        """CREATE TABLE IF NOT EXISTS courses (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(100),
            difficulty_level VARCHAR(50) DEFAULT 'beginner',
            estimated_duration INTEGER,
            price DECIMAL(10,2) DEFAULT 0.00,
            is_published BOOLEAN DEFAULT false,
            thumbnail_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS content (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            content_type VARCHAR(100) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size BIGINT,
            mime_type VARCHAR(100),
            duration INTEGER,
            thumbnail_url TEXT,
            processing_status VARCHAR(50) DEFAULT 'pending',
            uploaded_by UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS enrollments (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            enrollment_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'active',
            progress_percentage DECIMAL(5,2) DEFAULT 0.00,
            last_accessed TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            certificate_issued BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, course_id)
        )""",
        
        """CREATE TABLE IF NOT EXISTS lessons (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            content TEXT,
            lesson_order INTEGER NOT NULL,
            duration_minutes INTEGER DEFAULT 0,
            is_published BOOLEAN DEFAULT false,
            lesson_type VARCHAR(50) DEFAULT 'video',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS quizzes (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            time_limit INTEGER,
            passing_score DECIMAL(5,2) DEFAULT 70.00,
            max_attempts INTEGER DEFAULT 3,
            is_published BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS refresh_tokens (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS lesson_content (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            lesson_id UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
            content_id UUID NOT NULL REFERENCES content(id) ON DELETE CASCADE,
            order_index INTEGER DEFAULT 0,
            is_primary BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lesson_id, content_id)
        )""",
        
        """CREATE TABLE IF NOT EXISTS content_versions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            content_id UUID NOT NULL REFERENCES content(id) ON DELETE CASCADE,
            version_number INTEGER NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            change_notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS lesson_progress (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
            lesson_id UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
            status VARCHAR(50) DEFAULT 'not_started',
            progress_percentage DECIMAL(5,2) DEFAULT 0.00,
            time_spent_minutes INTEGER DEFAULT 0,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            last_position INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(enrollment_id, lesson_id)
        )""",
        
        """CREATE TABLE IF NOT EXISTS certificates (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            certificate_url TEXT,
            issued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            verification_code VARCHAR(100) NOT NULL UNIQUE,
            is_verified BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS learning_paths (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            target_completion_date TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS learning_path_courses (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
            course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            order_index INTEGER NOT NULL,
            is_required BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(learning_path_id, course_id)
        )""",
        
        """CREATE TABLE IF NOT EXISTS quiz_questions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            question_type VARCHAR(50) NOT NULL,
            correct_answer TEXT,
            points DECIMAL(5,2) DEFAULT 1.00,
            order_index INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS quiz_attempts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
            student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            score DECIMAL(5,2),
            passed BOOLEAN DEFAULT false,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP WITH TIME ZONE,
            answers JSONB
        )"""
    ]
    
    # Index statements
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses(instructor_id)",
        "CREATE INDEX IF NOT EXISTS idx_courses_category ON courses(category)",
        "CREATE INDEX IF NOT EXISTS idx_courses_published ON courses(is_published)",
        "CREATE INDEX IF NOT EXISTS idx_lessons_course ON lessons(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_lessons_order ON lessons(course_id, lesson_order)",
        "CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_enrollments_status ON enrollments(status)",
        "CREATE INDEX IF NOT EXISTS idx_lesson_progress_enrollment ON lesson_progress(enrollment_id)",
        "CREATE INDEX IF NOT EXISTS idx_lesson_progress_lesson ON lesson_progress(lesson_id)",
        "CREATE INDEX IF NOT EXISTS idx_content_uploaded_by ON content(uploaded_by)",
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_certificates_student ON certificates(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz ON quiz_attempts(quiz_id)",
        "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student ON quiz_attempts(student_id)"
    ]
    
    # Function and trigger statements
    function_statements = [
        """CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql'"""
    ]
    
    trigger_statements = [
        "DROP TRIGGER IF EXISTS update_users_updated_at ON users",
        "CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
        "DROP TRIGGER IF EXISTS update_courses_updated_at ON courses",
        "CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
        "DROP TRIGGER IF EXISTS update_lessons_updated_at ON lessons",
        "CREATE TRIGGER update_lessons_updated_at BEFORE UPDATE ON lessons FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
        "DROP TRIGGER IF EXISTS update_content_updated_at ON content",
        "CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
        "DROP TRIGGER IF EXISTS update_enrollments_updated_at ON enrollments",
        "CREATE TRIGGER update_enrollments_updated_at BEFORE UPDATE ON enrollments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
        "DROP TRIGGER IF EXISTS update_lesson_progress_updated_at ON lesson_progress",
        "CREATE TRIGGER update_lesson_progress_updated_at BEFORE UPDATE ON lesson_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
        "DROP TRIGGER IF EXISTS update_learning_paths_updated_at ON learning_paths",
        "CREATE TRIGGER update_learning_paths_updated_at BEFORE UPDATE ON learning_paths FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()",
        "DROP TRIGGER IF EXISTS update_quizzes_updated_at ON quizzes",
        "CREATE TRIGGER update_quizzes_updated_at BEFORE UPDATE ON quizzes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    ]
    
    try:
        async with engine.begin() as conn:
            print("📋 Creating database schema...")
            
            # Execute schema creation
            await execute_sql_statements(conn, schema_statements, "Created tables")
            
            # Execute indexes
            await execute_sql_statements(conn, index_statements, "Created indexes")
            
            # Execute functions
            await execute_sql_statements(conn, function_statements, "Created functions")
            
            # Execute triggers
            await execute_sql_statements(conn, trigger_statements, "Created triggers")
            
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        raise
    finally:
        await engine.dispose()

async def verify_tables():
    """Verify that tables were created successfully"""
    engine = create_async_engine(APP_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Count tables
            result = await conn.execute(text("""
                SELECT count(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """))
            count = result.fetchone()[0]
            
            # List tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print(f"📊 Database verification:")
            print(f"   • Total tables: {count}")
            print(f"   • Tables created: {', '.join(tables)}")
            
            # Test a simple insert/select
            await conn.execute(text("""
                INSERT INTO users (email, username, full_name, hashed_password, role) 
                VALUES ('test@example.com', 'testuser', 'Test User', 'hashed_password', 'student')
                ON CONFLICT (email) DO NOTHING
            """))
            
            result = await conn.execute(text("SELECT count(*) FROM users WHERE email = 'test@example.com'"))
            user_count = result.fetchone()[0]
            
            if user_count > 0:
                print("✅ Database is working correctly - test user created/verified")
            else:
                print("⚠️  Warning: Could not verify database functionality")
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        raise
    finally:
        await engine.dispose()

async def create_tables():
    """Main function to create all tables and schema"""
    
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        # Try to import models first (but don't fail if they don't exist)
        models_loaded = []
        
        try:
            from shared.database.base import Base, engine
            
            # Try to import service models
            try:
                from services.course_management.database.models import Course, Lesson
                models_loaded.append("course management")
            except ImportError:
                pass
            
            try:
                from services.user_management.database.models import User, RefreshToken
                models_loaded.append("user management")
            except ImportError:
                pass
            
            try:
                from services.enrollment.database.models import Enrollment, LessonProgress, Certificate, LearningPath
                models_loaded.append("enrollment")
            except ImportError:
                pass
            
            if models_loaded:
                print(f"✅ Loaded models from: {', '.join(models_loaded)}")
                
                # Create all tables from models
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    print("✅ Created all database tables from models")
                    return
                    
        except ImportError:
            pass
    
    except Exception as e:
        print(f"⚠️  Could not use model-based creation: {e}")
    
    print("⚠️  No service models found. Using SQL schema instead.")
    return await create_tables_from_schema()

async def main():
    print("🗄️  Setting up Course Creator database...")
    
    try:
        await create_database()
        await create_tables()
        await verify_tables()
        print("🎉 Database setup completed successfully!")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
