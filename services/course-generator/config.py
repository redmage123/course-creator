from dataclasses import dataclass
from typing import Optional
from hydra.core.config_store import ConfigStore
from omegaconf import MISSING


@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int
    pool_timeout: int
    ssl_mode: str


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str
    ssl: bool
    timeout: int


@dataclass
class CourseManagementClientConfig:
    base_url: str
    timeout: int
    retry_count: int
    api_key: str


@dataclass
class ServiceClientsConfig:
    course_management: CourseManagementClientConfig


@dataclass
class SecurityConfig:
    api_key: str
    jwt_secret: str
    token_expiry: int


@dataclass
class ServiceDiscoveryConfig:
    enabled: bool
    registration_url: str


@dataclass
class MonitoringConfig:
    health_check_interval: int
    metrics_port: int
    service_discovery: ServiceDiscoveryConfig


@dataclass
class LoggingConfig:
    level: str
    format: str
    file_path: str
    retention_days: int


@dataclass
class ServiceConfig:
    name: str
    version: str
    host: str
    port: int
    debug: bool


@dataclass
class CourseGeneratorConfig:
    service: ServiceConfig
    database: DatabaseConfig
    redis: RedisConfig
    service_clients: ServiceClientsConfig
    security: SecurityConfig
    monitoring: MonitoringConfig
    logging: LoggingConfig


cs = ConfigStore.instance()
cs.store(name="course_generator_config", node=CourseGeneratorConfig)


def register_configs() -> None:
    """Register configurations with Hydra's config store."""
    cs.store(
        name="course_generator_config",
        node=CourseGeneratorConfig
    )