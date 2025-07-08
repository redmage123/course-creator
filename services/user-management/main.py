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

# Pydantic models
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    roles: List[str] = []

class Token(BaseModel):
    access_token: str
    token_type: str

class Role(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

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
    
    # Dependencies
    async def get_current_user(token: str = Depends(oauth2_scheme)):
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
            
        query = users_table.select().where(users_table.c.id == user_id)
        user = await database.fetch_one(query)
        if user is None:
            raise credentials_exception
        return User(**user)
    
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
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
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
            {"sub": str(user["id"]), "exp": datetime.utcnow() + timedelta(minutes=30)},
            cfg.jwt.secret_key,
            algorithm=cfg.jwt.algorithm
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    
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
        
        # Create username from email if not provided
        username = user.email.split('@')[0]
        
        # Insert new user
        insert_query = users_table.insert().values(
            email=user.email,
            username=username,
            full_name=user.full_name or "",
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
            role='student'
        )
        
        try:
            result = await database.execute(insert_query)
            # Get the created user
            new_user_query = users_table.select().where(users_table.c.email == user.email)
            new_user = await database.fetch_one(new_user_query)
            return User(**new_user)
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise HTTPException(status_code=400, detail="Registration failed")
    
    @app.get("/users/profile")
    async def get_user_profile(current_user: User = Depends(get_current_user)):
        logger.info(f"Profile request for user ID: {current_user.id}")
        return {"message": "User profile", "user": current_user}
    
    @app.get("/roles")
    async def get_roles():
        return [{"id": 1, "name": "admin", "description": "Administrator"}]
    
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