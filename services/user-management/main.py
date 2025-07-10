#!/usr/bin/env python3
"""
User Management Service - Fixed Hydra Configuration
"""
from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import hydra
from omegaconf import DictConfig
import uvicorn
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import databases
import sqlalchemy
import sqlalchemy.dialects.postgresql
import uuid

# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    username: Optional[str] = None

class User(UserBase):
    id: str
    username: str
    is_active: bool
    role: str = "student"  # student, instructor, admin
    roles: List[str] = []  # For backward compatibility

class Token(BaseModel):
    access_token: str
    token_type: str

class Role(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

class AdminUserCreate(UserCreate):
    role: str = "student"

class UserSession(BaseModel):
    id: str
    user_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    last_accessed_at: datetime

@hydra.main(config_path="conf", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    # Setup logging
    logging.basicConfig(
        level=cfg.log.level,
        format=cfg.log.format
    )
    logger = logging.getLogger(__name__)
    
    # Database setup
    database = databases.Database(cfg.database.url)
    
    # Define user table for queries
    users_table = sqlalchemy.Table(
        'users',
        sqlalchemy.MetaData(),
        sqlalchemy.Column('id', sqlalchemy.dialects.postgresql.UUID, primary_key=True, server_default=sqlalchemy.text('uuid_generate_v4()')),
        sqlalchemy.Column('email', sqlalchemy.String(255), unique=True, nullable=False),
        sqlalchemy.Column('username', sqlalchemy.String(100), unique=True, nullable=False),
        sqlalchemy.Column('full_name', sqlalchemy.String(255), nullable=False),
        sqlalchemy.Column('hashed_password', sqlalchemy.String(255), nullable=False),
        sqlalchemy.Column('is_active', sqlalchemy.Boolean, default=True),
        sqlalchemy.Column('is_verified', sqlalchemy.Boolean, default=False),
        sqlalchemy.Column('role', sqlalchemy.String(50), default='student'),
        sqlalchemy.Column('avatar_url', sqlalchemy.Text),
        sqlalchemy.Column('bio', sqlalchemy.Text),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.text('CURRENT_TIMESTAMP')),
        sqlalchemy.Column('updated_at', sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.text('CURRENT_TIMESTAMP')),
        sqlalchemy.Column('last_login', sqlalchemy.DateTime(timezone=True))
    )
    
    # Define user sessions table
    user_sessions_table = sqlalchemy.Table(
        'user_sessions',
        sqlalchemy.MetaData(),
        sqlalchemy.Column('id', sqlalchemy.dialects.postgresql.UUID, primary_key=True, server_default=sqlalchemy.text('uuid_generate_v4()')),
        sqlalchemy.Column('user_id', sqlalchemy.dialects.postgresql.UUID, sqlalchemy.ForeignKey('users.id'), nullable=False),
        sqlalchemy.Column('token_hash', sqlalchemy.String(255), unique=True, nullable=False),
        sqlalchemy.Column('ip_address', sqlalchemy.String(45)),
        sqlalchemy.Column('user_agent', sqlalchemy.String(255)),
        sqlalchemy.Column('expires_at', sqlalchemy.DateTime(timezone=True), nullable=False),
        sqlalchemy.Column('created_at', sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.text('CURRENT_TIMESTAMP')),
        sqlalchemy.Column('last_accessed_at', sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.text('CURRENT_TIMESTAMP'))
    )
    
    # Security
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
    
    # FastAPI app
    app = FastAPI(
        title="User Management Service",
        description="API for managing users and authentication",
        version="1.0.0"
    )
    
    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Session management functions
    async def create_user_session(user_id: str, token: str, ip_address: str = None, user_agent: str = None):
        """Create a new user session in the database"""
        session_id = str(uuid.uuid4())
        token_hash = pwd_context.hash(token)
        expires_at = datetime.utcnow() + timedelta(minutes=cfg.jwt.token_expiry)
        
        # Clean up old sessions for this user (keep only last 3 sessions)
        await cleanup_old_sessions(user_id, max_sessions=3)
        
        query = user_sessions_table.insert().values(
            id=session_id,
            user_id=user_id,
            token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        await database.execute(query)
        return session_id
    
    async def validate_session(token: str, user_id: str):
        """Validate if session exists and is not expired"""
        query = user_sessions_table.select().where(
            sqlalchemy.and_(
                user_sessions_table.c.user_id == user_id,
                user_sessions_table.c.expires_at > datetime.utcnow()
            )
        )
        sessions = await database.fetch_all(query)
        
        # Check if token matches any active session
        for session in sessions:
            if pwd_context.verify(token, session["token_hash"]):
                # Update last accessed time
                update_query = user_sessions_table.update().where(
                    user_sessions_table.c.id == session["id"]
                ).values(last_accessed_at=datetime.utcnow())
                await database.execute(update_query)
                return True
        return False
    
    async def cleanup_old_sessions(user_id: str, max_sessions: int = 3):
        """Keep only the most recent sessions for a user"""
        query = sqlalchemy.text("""
            DELETE FROM user_sessions 
            WHERE user_id = :user_id 
            AND id NOT IN (
                SELECT id FROM user_sessions 
                WHERE user_id = :user_id 
                ORDER BY created_at DESC 
                LIMIT :max_sessions
            )
        """)
        await database.execute(query, {"user_id": user_id, "max_sessions": max_sessions})
    
    async def invalidate_session(token: str, user_id: str):
        """Invalidate a specific session"""
        query = user_sessions_table.select().where(
            user_sessions_table.c.user_id == user_id
        )
        sessions = await database.fetch_all(query)
        
        for session in sessions:
            if pwd_context.verify(token, session["token_hash"]):
                delete_query = user_sessions_table.delete().where(
                    user_sessions_table.c.id == session["id"]
                )
                await database.execute(delete_query)
                return True
        return False
    
    async def cleanup_expired_sessions():
        """Remove all expired sessions from database"""
        query = user_sessions_table.delete().where(
            user_sessions_table.c.expires_at < datetime.utcnow()
        )
        result = await database.execute(query)
        return result

    # Dependencies
    async def get_current_user(token: str = Depends(oauth2_scheme), request: Request = None):
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, 
                cfg.jwt.secret_key, 
                algorithms=[cfg.jwt.algorithm]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        # Validate session exists and is not expired
        session_valid = await validate_session(token, user_id)
        if not session_valid:
            raise HTTPException(
                status_code=401,
                detail="Session expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        query = users_table.select().where(users_table.c.id == user_id)
        user = await database.fetch_one(query)
        if user is None:
            raise credentials_exception
        
        # Convert UUID to string for Pydantic model
        user_data = dict(user)
        user_data['id'] = str(user_data['id'])
        user_data['roles'] = [user_data.get('role', 'student')]  # Convert role to roles list
        
        return User(**user_data)
    
    # Role checking functions
    async def require_admin(current_user: User = Depends(get_current_user)):
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required"
            )
        return current_user

    async def require_instructor_or_admin(current_user: User = Depends(get_current_user)):
        if current_user.role not in ["instructor", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Instructor or Admin privileges required"
            )
        return current_user
    
    # Startup/shutdown events
    @app.on_event("startup")
    async def startup():
        logger.info("Starting up service...")
        await database.connect()
    
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Shutting down service...")
        await database.disconnect()
    
    # Routes
    @app.get("/")
    async def root():
        return {"message": "User Management Service"}
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow()
        }
    
    @app.post("/auth/login", response_model=Token)
    async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
        logger.info(f"Login attempt for user: {form_data.username}")
        
        # Find user by email
        query = users_table.select().where(users_table.c.email == form_data.username)
        user = await database.fetch_one(query)
        
        if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )

        access_token = jwt.encode(
            {"sub": str(user["id"]), "exp": datetime.utcnow() + timedelta(minutes=cfg.jwt.token_expiry)},
            cfg.jwt.secret_key,
            algorithm=cfg.jwt.algorithm
        )
        
        # Create session in database
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("User-Agent") if request else None
        session_id = await create_user_session(str(user["id"]), access_token, ip_address, user_agent)
        
        # Update last login time
        update_query = users_table.update().where(
            users_table.c.id == user["id"]
        ).values(last_login=datetime.utcnow())
        await database.execute(update_query)
        
        logger.info(f"User {user['email']} logged in successfully. Session ID: {session_id}")
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    @app.post("/auth/logout")
    async def logout(current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
        """Logout user and invalidate session"""
        logger.info(f"User {current_user.email} logging out")
        
        # Invalidate the current session
        success = await invalidate_session(token, current_user.id)
        
        if success:
            logger.info(f"Session invalidated for user {current_user.email}")
            return {"message": "Successfully logged out"}
        else:
            logger.warning(f"Failed to invalidate session for user {current_user.email}")
            return {"message": "Logout completed"}
    
    @app.get("/auth/sessions")
    async def get_user_sessions(current_user: User = Depends(get_current_user)):
        """Get all active sessions for the current user"""
        query = user_sessions_table.select().where(
            sqlalchemy.and_(
                user_sessions_table.c.user_id == current_user.id,
                user_sessions_table.c.expires_at > datetime.utcnow()
            )
        ).order_by(user_sessions_table.c.created_at.desc())
        
        sessions = await database.fetch_all(query)
        
        session_list = []
        for session in sessions:
            session_data = {
                "id": str(session["id"]),
                "ip_address": session["ip_address"],
                "user_agent": session["user_agent"],
                "created_at": session["created_at"],
                "last_accessed_at": session["last_accessed_at"],
                "expires_at": session["expires_at"]
            }
            session_list.append(session_data)
        
        return {"sessions": session_list}
    
    @app.delete("/auth/sessions/{session_id}")
    async def revoke_session(session_id: str, current_user: User = Depends(get_current_user)):
        """Revoke a specific session"""
        query = user_sessions_table.delete().where(
            sqlalchemy.and_(
                user_sessions_table.c.id == session_id,
                user_sessions_table.c.user_id == current_user.id
            )
        )
        
        result = await database.execute(query)
        if result:
            logger.info(f"Session {session_id} revoked for user {current_user.email}")
            return {"message": "Session revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    
    @app.post("/auth/cleanup-sessions")
    async def cleanup_sessions_endpoint(current_user: User = Depends(require_admin)):
        """Admin endpoint to cleanup expired sessions"""
        result = await cleanup_expired_sessions()
        return {"message": f"Cleaned up expired sessions", "rows_affected": result}
    
    @app.post("/auth/register", response_model=User)
    async def register(user: UserCreate):
        logger.info(f"Registration attempt for email: {user.email}")
        
        # Check if user exists
        existing_query = users_table.select().where(users_table.c.email == user.email)
        existing_user = await database.fetch_one(existing_query)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        hashed_password = pwd_context.hash(user.password)
        
        # Use provided username or create from email
        username = user.username or user.email.split('@')[0]
        
        # Check if username already exists
        existing_username_query = users_table.select().where(users_table.c.username == username)
        existing_username = await database.fetch_one(existing_username_query)
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Insert new user
        insert_query = users_table.insert().values(
            email=user.email,
            username=username,
            full_name=user.full_name or "",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
            role='instructor'
        )
        
        try:
            result = await database.execute(insert_query)
            # Get the created user
            new_user_query = users_table.select().where(users_table.c.email == user.email)
            new_user = await database.fetch_one(new_user_query)
            
            # Convert UUID to string for Pydantic model
            user_data = dict(new_user)
            user_data['id'] = str(user_data['id'])
            user_data['roles'] = [user_data.get('role', 'student')]  # Convert role to roles list
            
            return User(**user_data)
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(status_code=400, detail="Registration failed")
    
    @app.get("/users/profile")
    async def get_user_profile(current_user: User = Depends(get_current_user)):
        logger.info(f"Profile request for user ID: {current_user.id}")
        return {"message": "User profile", "user": current_user}
    
    @app.get("/roles")
    async def get_roles():
        return [
            {"id": 1, "name": "admin", "description": "Administrator"},
            {"id": 2, "name": "instructor", "description": "Course Instructor"},
            {"id": 3, "name": "student", "description": "Student"}
        ]

    @app.get("/users/by-email/{email}")
    async def get_user_by_email(email: str):
        """Get user by email address"""
        try:
            async with database.transaction():
                user = await database.fetch_one(
                    "SELECT id, email, username, full_name, role FROM users WHERE email = :email",
                    {"email": email}
                )
                
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return {
                    "id": str(user["id"]),
                    "email": user["email"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"]
                }
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user")

    # Admin endpoints
    @app.get("/admin/users", response_model=List[User])
    async def admin_get_all_users(admin_user: User = Depends(require_admin)):
        logger.info(f"Admin {admin_user.id} requesting all users")
        
        query = users_table.select()
        users = await database.fetch_all(query)
        
        user_list = []
        for user in users:
            user_data = dict(user)
            user_data['id'] = str(user_data['id'])
            user_data['roles'] = [user_data.get('role', 'student')]
            user_list.append(User(**user_data))
        
        return user_list

    @app.post("/admin/users", response_model=User)
    async def admin_create_user(user: AdminUserCreate, admin_user: User = Depends(require_admin)):
        logger.info(f"Admin {admin_user.id} creating user: {user.email}")
        
        # Check if user exists
        existing_query = users_table.select().where(users_table.c.email == user.email)
        existing_user = await database.fetch_one(existing_query)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        hashed_password = pwd_context.hash(user.password)
        username = user.email.split('@')[0]
        
        # Insert new user with specified role
        insert_query = users_table.insert().values(
            email=user.email,
            username=username,
            full_name=user.full_name or "",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,  # Admin-created users are pre-verified
            role=user.role
        )
        
        try:
            result = await database.execute(insert_query)
            new_user_query = users_table.select().where(users_table.c.email == user.email)
            new_user = await database.fetch_one(new_user_query)
            
            user_data = dict(new_user)
            user_data['id'] = str(user_data['id'])
            user_data['roles'] = [user_data.get('role', 'student')]
            
            return User(**user_data)
        except Exception as e:
            logger.error(f"Admin user creation error: {e}")
            raise HTTPException(status_code=400, detail="User creation failed")

    @app.put("/admin/users/{user_id}", response_model=User)
    async def admin_update_user(user_id: str, user_update: UserUpdate, admin_user: User = Depends(require_admin)):
        logger.info(f"Admin {admin_user.id} updating user: {user_id}")
        
        # Check if user exists
        query = users_table.select().where(users_table.c.id == user_id)
        existing_user = await database.fetch_one(query)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update data
        update_data = {}
        if user_update.email is not None:
            update_data['email'] = user_update.email
        if user_update.full_name is not None:
            update_data['full_name'] = user_update.full_name
        if user_update.is_active is not None:
            update_data['is_active'] = user_update.is_active
        if user_update.role is not None:
            update_data['role'] = user_update.role
        
        if update_data:
            update_query = users_table.update().where(users_table.c.id == user_id).values(**update_data)
            await database.execute(update_query)
        
        # Get updated user
        updated_user = await database.fetch_one(users_table.select().where(users_table.c.id == user_id))
        
        user_data = dict(updated_user)
        user_data['id'] = str(user_data['id'])
        user_data['roles'] = [user_data.get('role', 'student')]
        
        return User(**user_data)

    @app.delete("/admin/users/{user_id}")
    async def admin_delete_user(user_id: str, admin_user: User = Depends(require_admin)):
        logger.info(f"Admin {admin_user.id} deleting user: {user_id}")
        
        # Check if user exists
        query = users_table.select().where(users_table.c.id == user_id)
        existing_user = await database.fetch_one(query)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Don't allow admin to delete themselves
        if user_id == admin_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Delete user
        delete_query = users_table.delete().where(users_table.c.id == user_id)
        await database.execute(delete_query)
        
        return {"message": "User deleted successfully"}

    @app.get("/admin/users/{user_id}", response_model=User)
    async def admin_get_user(user_id: str, admin_user: User = Depends(require_admin)):
        logger.info(f"Admin {admin_user.id} requesting user: {user_id}")
        
        query = users_table.select().where(users_table.c.id == user_id)
        user = await database.fetch_one(query)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = dict(user)
        user_data['id'] = str(user_data['id'])
        user_data['roles'] = [user_data.get('role', 'student')]
        
        return User(**user_data)

    @app.get("/admin/stats")
    async def admin_get_stats(admin_user: User = Depends(require_admin)):
        logger.info(f"Admin {admin_user.id} requesting system stats")
        
        # Get user counts by role
        total_users = await database.fetch_val("SELECT COUNT(*) FROM users")
        admin_count = await database.fetch_val("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        instructor_count = await database.fetch_val("SELECT COUNT(*) FROM users WHERE role = 'instructor'")
        student_count = await database.fetch_val("SELECT COUNT(*) FROM users WHERE role = 'student'")
        active_users = await database.fetch_val("SELECT COUNT(*) FROM users WHERE is_active = true")
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "users_by_role": {
                "admin": admin_count,
                "instructor": instructor_count,
                "student": student_count
            }
        }
    
    # Error handling
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Start the server
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, reload=cfg.server.reload)

if __name__ == "__main__":
    main()