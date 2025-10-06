# config.py
from dataclasses import dataclass
from typing import Optional, List
from hydra.core.config_store import ConfigStore

@dataclass
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str
    database: str
    pool_size: int
    ssl_mode: str

@dataclass
class RedisConfig:
    host: str
    port: int
    password: Optional[str]
    db: int
    ssl: bool

@dataclass
class ServiceConfig:
    host: str
    port: int
    timeout: int
    retry_attempts: int
    health_check_path: str

@dataclass
class DependentServices:
    course_management: ServiceConfig
    course_generator: ServiceConfig
    content_storage: ServiceConfig

@dataclass
class Security:
    jwt_secret: str
    api_key: str
    token_expiry: int
    allowed_origins: List[str]

@dataclass
class Monitoring:
    log_level: str
    enable_tracing: bool
    metrics_port: int
    health_check_interval: int

@dataclass
class AppConfig:
    service_name: str
    environment: str
    debug: bool
    database: DatabaseConfig
    redis: RedisConfig
    dependent_services: DependentServices
    security: Security
    monitoring: Monitoring

cs = ConfigStore.instance()
cs.store(name="config", node=AppConfig)