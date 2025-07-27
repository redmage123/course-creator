#!/usr/bin/env python3
"""
Create analytics tables directly using Docker PostgreSQL connection
"""
import asyncio
import asyncpg
from pathlib import Path

# Docker PostgreSQL connection
DB_URL = "postgresql://postgres:postgres_password@localhost:5433/course_creator"

async def create_analytics_tables():
    """Create analytics tables and other required tables"""
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DB_URL)
        print("✅ Connected to PostgreSQL database")
        
        # First, create the core platform tables if they don't exist
        core_tables_sql = """
        -- Create extension for UUID generation
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Users table (required for foreign keys)
        CREATE TABLE IF NOT EXISTS users (
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
        );
        
        -- Courses table (required for foreign keys)
        CREATE TABLE IF NOT EXISTS courses (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            instructor_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category VARCHAR(100),
            difficulty_level VARCHAR(50) DEFAULT 'beginner',
            estimated_duration INTEGER,
            duration_unit VARCHAR(20) DEFAULT 'weeks',
            price DECIMAL(10,2) DEFAULT 0.00,
            is_published BOOLEAN DEFAULT false,
            thumbnail_url TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Enrollments table (required for analytics)
        CREATE TABLE IF NOT EXISTS enrollments (
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
        );
        """
        
        print("🔄 Creating core platform tables...")
        await conn.execute(core_tables_sql)
        print("✅ Core platform tables created")
        
        print("🔄 Creating analytics tables...")
        
        # Split into individual statements to handle complex SQL
        analytics_statements = [
            # Student Activities table
            """CREATE TABLE IF NOT EXISTS student_activities (
                activity_id VARCHAR PRIMARY KEY,
                student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                activity_type VARCHAR NOT NULL,
                activity_data JSONB DEFAULT '{}',
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                session_id VARCHAR,
                ip_address INET,
                user_agent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )""",
            
            "CREATE INDEX IF NOT EXISTS idx_student_activities_student_course ON student_activities(student_id, course_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_student_activities_type ON student_activities(activity_type, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_student_activities_session ON student_activities(session_id)",
            
            # Lab Usage Metrics table
            """CREATE TABLE IF NOT EXISTS lab_usage_metrics (
                metric_id VARCHAR PRIMARY KEY,
                student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                lab_id VARCHAR NOT NULL,
                session_start TIMESTAMP WITH TIME ZONE NOT NULL,
                session_end TIMESTAMP WITH TIME ZONE,
                duration_minutes INTEGER,
                actions_performed INTEGER DEFAULT 0,
                code_executions INTEGER DEFAULT 0,
                errors_encountered INTEGER DEFAULT 0,
                completion_status VARCHAR DEFAULT 'in_progress',
                final_code TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )""",
            
            "CREATE INDEX IF NOT EXISTS idx_lab_usage_student_course ON lab_usage_metrics(student_id, course_id)",
            "CREATE INDEX IF NOT EXISTS idx_lab_usage_lab_session ON lab_usage_metrics(lab_id, session_start)",
            "CREATE INDEX IF NOT EXISTS idx_lab_usage_status ON lab_usage_metrics(completion_status)",
            
            # Quiz Performance table
            """CREATE TABLE IF NOT EXISTS quiz_performance (
                performance_id VARCHAR PRIMARY KEY,
                student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                quiz_id VARCHAR NOT NULL,
                attempt_number INTEGER DEFAULT 1,
                start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                end_time TIMESTAMP WITH TIME ZONE,
                duration_minutes INTEGER,
                questions_total INTEGER NOT NULL,
                questions_answered INTEGER DEFAULT 0,
                questions_correct INTEGER DEFAULT 0,
                score_percentage DECIMAL(5,2),
                answers JSONB DEFAULT '{}',
                time_per_question JSONB DEFAULT '{}',
                status VARCHAR DEFAULT 'in_progress',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )""",
            
            "CREATE INDEX IF NOT EXISTS idx_quiz_performance_student_course ON quiz_performance(student_id, course_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_performance_quiz ON quiz_performance(quiz_id, start_time)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_performance_score ON quiz_performance(score_percentage)",
            
            # Student Progress table
            """CREATE TABLE IF NOT EXISTS student_progress (
                progress_id VARCHAR PRIMARY KEY,
                student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                content_item_id VARCHAR NOT NULL,
                content_type VARCHAR NOT NULL,
                status VARCHAR DEFAULT 'not_started',
                progress_percentage DECIMAL(5,2) DEFAULT 0.0,
                time_spent_minutes INTEGER DEFAULT 0,
                last_accessed TIMESTAMP WITH TIME ZONE NOT NULL,
                completion_date TIMESTAMP WITH TIME ZONE,
                mastery_score DECIMAL(5,2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )""",
            
            "CREATE INDEX IF NOT EXISTS idx_student_progress_student_course ON student_progress(student_id, course_id)",
            "CREATE INDEX IF NOT EXISTS idx_student_progress_content ON student_progress(content_item_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_student_progress_accessed ON student_progress(last_accessed)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_student_progress_unique ON student_progress(student_id, course_id, content_item_id)",
            
            # Learning Analytics table
            """CREATE TABLE IF NOT EXISTS learning_analytics (
                analytics_id VARCHAR PRIMARY KEY,
                student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                engagement_score DECIMAL(5,2) DEFAULT 0.0,
                progress_velocity DECIMAL(8,2) DEFAULT 0.0,
                lab_proficiency DECIMAL(5,2) DEFAULT 0.0,
                quiz_performance DECIMAL(5,2) DEFAULT 0.0,
                time_on_platform INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                risk_level VARCHAR DEFAULT 'low',
                recommendations JSONB DEFAULT '[]',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )""",
            
            "CREATE INDEX IF NOT EXISTS idx_learning_analytics_student_course ON learning_analytics(student_id, course_id, analysis_date)",
            "CREATE INDEX IF NOT EXISTS idx_learning_analytics_risk ON learning_analytics(risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_learning_analytics_engagement ON learning_analytics(engagement_score)",
        ]
        
        # Execute each statement individually
        for i, statement in enumerate(analytics_statements, 1):
            try:
                await conn.execute(statement)
                print(f"   ✅ Statement {i}/{len(analytics_statements)} executed")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"   ⚠️  Warning on statement {i}: {e}")
        
        # Create trigger function and trigger separately
        print("🔄 Creating trigger function...")
        await conn.execute("""
            CREATE OR REPLACE FUNCTION update_student_progress_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        
        print("🔄 Creating trigger...")
        await conn.execute("""
            DROP TRIGGER IF EXISTS trg_student_progress_updated_at ON student_progress
        """)
        await conn.execute("""
            CREATE TRIGGER trg_student_progress_updated_at
                BEFORE UPDATE ON student_progress
                FOR EACH ROW
                EXECUTE FUNCTION update_student_progress_updated_at()
        """)
        
        print("✅ Analytics tables created")
        
        # Verify tables were created
        result = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = [row['table_name'] for row in result]
        analytics_tables = ['student_activities', 'lab_usage_metrics', 'quiz_performance', 'student_progress', 'learning_analytics']
        core_tables = ['users', 'courses', 'enrollments']
        
        print(f"\n📊 Database verification:")
        print(f"   • Total tables: {len(tables)}")
        print(f"   • All tables: {', '.join(tables)}")
        
        found_analytics = [t for t in tables if t in analytics_tables]
        found_core = [t for t in tables if t in core_tables]
        
        if found_analytics:
            print(f"   • Analytics tables: {', '.join(found_analytics)}")
        if found_core:
            print(f"   • Core tables: {', '.join(found_core)}")
        
        if len(found_analytics) == len(analytics_tables):
            print("✅ All analytics tables created successfully!")
        else:
            missing = set(analytics_tables) - set(found_analytics)
            print(f"⚠️  Missing analytics tables: {missing}")
        
        # Create some sample data for testing
        print("\n🔄 Creating sample data for testing...")
        
        # Create test instructor user
        await conn.execute("""
            INSERT INTO users (id, email, username, full_name, hashed_password, role) 
            VALUES ('550e8400-e29b-41d4-a716-446655440000', 'instructor@example.com', 'instructor', 'Test Instructor', 'hashed_password', 'instructor')
            ON CONFLICT (email) DO NOTHING
        """)
        
        # Create test students
        await conn.execute("""
            INSERT INTO users (id, email, username, full_name, hashed_password, role) 
            VALUES 
                ('550e8400-e29b-41d4-a716-446655440001', 'student1@example.com', 'student1', 'Alice Johnson', 'hashed_password', 'student'),
                ('550e8400-e29b-41d4-a716-446655440002', 'student2@example.com', 'student2', 'Bob Smith', 'hashed_password', 'student'),
                ('550e8400-e29b-41d4-a716-446655440003', 'student3@example.com', 'student3', 'Carol Davis', 'hashed_password', 'student')
            ON CONFLICT (email) DO NOTHING
        """)
        
        # Create test course
        await conn.execute("""
            INSERT INTO courses (id, title, description, instructor_id, category, is_published) 
            VALUES ('550e8400-e29b-41d4-a716-446655441000', 'Introduction to Python Programming', 'A comprehensive course for beginners to learn Python programming', '550e8400-e29b-41d4-a716-446655440000', 'Programming', true)
            ON CONFLICT (id) DO NOTHING
        """)
        
        # Create test enrollments
        await conn.execute("""
            INSERT INTO enrollments (student_id, course_id, status, progress_percentage) 
            VALUES 
                ('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655441000', 'active', 75.0),
                ('550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655441000', 'active', 45.0),
                ('550e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655441000', 'active', 89.0)
            ON CONFLICT (student_id, course_id) DO NOTHING
        """)
        
        print("✅ Sample data created successfully!")
        
        await conn.close()
        print("\n🎉 Database setup completed successfully!")
        print("\n📄 PDF analytics functionality is now ready to use!")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_analytics_tables())