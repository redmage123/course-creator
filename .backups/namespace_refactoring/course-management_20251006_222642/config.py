from dataclasses import dataclass
from typing import List, Optional
from omegaconf import MISSING
from hydra.core.config_store import ConfigStore

@dataclass
class LoggingConfig:
    level: str
    format: str
    file: str

@dataclass
class DatabaseConfig:
    type: str
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
    pool_timeout: int
    ssl_mode: str
    connection_retry_attempts: int
    connection_retry_delay: int

@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str
    ssl: bool
    timeout: int
    retry_attempts: int
    pool_size: int

@dataclass
class ServiceConfig:
    url: str
    timeout: int
    retry_attempts: int

@dataclass
class ServicesConfig:
    user_service: ServiceConfig
    notification_service: ServiceConfig
    content_service: ServiceConfig

@dataclass
class ApiGatewayConfig:
    url: str
    timeout: int

@dataclass
class JWTConfig:
    secret_key: str
    algorithm: str
    token_expiry: int

@dataclass
class ApiKeysConfig:
    user_service: str
    notification_service: str
    content_service: str

@dataclass
class CorsConfig:
    allowed_origins: List[str]
    allowed_methods: List[str]
    allowed_headers: List[str]

@dataclass
class SecurityConfig:
    jwt: JWTConfig
    api_keys: ApiKeysConfig
    cors: CorsConfig

@dataclass
class ServiceDiscoveryConfig:
    enabled: bool
    consul_host: str
    consul_port: int
    service_check_interval: int
    health_check_endpoint: str

@dataclass
class AppConfig:
    name: str
    version: str
    host: str
    port: int
    debug: bool
    logging: LoggingConfig
    database: DatabaseConfig
    redis: RedisConfig
    services: ServicesConfig
    api_gateway: ApiGatewayConfig
    security: SecurityConfig
    service_discovery: ServiceDiscoveryConfig

cs = ConfigStore.instance()
cs.store(name="config", node=AppConfig)