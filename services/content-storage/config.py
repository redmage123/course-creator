# config.py
from dataclasses import dataclass
from typing import Optional, Dict, List
from hydra.core.config_store import ConfigStore
from omegaconf import MISSING

@dataclass
class DatabaseConfig:
    host: str = MISSING
    port: int = MISSING
    username: str = MISSING
    password: str = MISSING
    database: str = MISSING
    pool_size: int = 10
    max_overflow: int = 20
    connection_timeout: int = 30

@dataclass
class RedisConfig:
    host: str = MISSING
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    timeout: int = 5

@dataclass
class ServiceConfig:
    host: str = MISSING
    port: int = MISSING
    base_url: str = MISSING
    timeout: int = 30
    retry_attempts: int = 3
    health_check_endpoint: str = "/health"

@dataclass
class DependentServices:
    course_management: ServiceConfig = ServiceConfig()
    course_generator: ServiceConfig = ServiceConfig()

@dataclass
class Security:
    api_key: str = MISSING
    secret_key: str = MISSING
    jwt_secret: str = MISSING
    token_expiry: int = 3600

@dataclass
class Monitoring:
    enabled: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    log_level: str = "INFO"

@dataclass
class ContentStorageConfig:
    # Service identification
    service_name: str = "content-storage"
    version: str = "1.0.0"
    environment: str = MISSING  # dev, staging, prod

    # Core configurations
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    dependent_services: DependentServices = DependentServices()
    security: Security = Security()
    monitoring: Monitoring = Monitoring()

    # Service-specific settings
    max_content_size_mb: int = 100
    supported_formats: List[str] = MISSING
    cache_ttl: int = 3600
    upload_folder: str = "/tmp/content-storage"

# Register the config schema
cs = ConfigStore.instance()
cs.store(name="content_storage_config", node=ContentStorageConfig)

# Default configuration values for different environments
@dataclass
class DefaultConfig:
    # Default configuration that applies to all environments
    defaults: List[str] = MISSING

# Example usage with YAML config files:
"""
# config/config.yaml
defaults:
  - environment: dev
  - _self_

# config/environment/dev.yaml
database:
  host: localhost
  port: 5432
  username: dev_user
  password: dev_pass
  database: content_storage_dev

redis:
  host: localhost
  port: 6379
  password: null

dependent_services:
  course_management:
    host: localhost
    port: 8001
    base_url: http://localhost:8001/api/v1
  course_generator:
    host: localhost
    port: 8002
    base_url: http://localhost:8002/api/v1

security:
  api_key: dev_api_key
  secret_key: dev_secret_key
  jwt_secret: dev_jwt_secret

supported_formats:
  - pdf
  - doc
  - docx
  - txt

# config/environment/prod.yaml
database:
  host: production-db.example.com
  port: 5432
  username: ${oc.env:DB_USER}
  password: ${oc.env:DB_PASS}
  database: content_storage_prod

redis:
  host: production-redis.example.com
  port: 6379
  password: ${oc.env:REDIS_PASS}
  ssl: true

dependent_services:
  course_management:
    host: course-management.example.com
    port: 443
    base_url: https://course-management.example.com/api/v1
  course_generator:
    host: course-generator.example.com
    port: 443
    base_url: https://course-generator.example.com/api/v1

security:
  api_key: ${oc.env:API_KEY}
  secret_key: ${oc.env:SECRET_KEY}
  jwt_secret: ${oc.env:JWT_SECRET}

debug: false
"""

# Example usage in application:
"""
import hydra
from omegaconf import DictConfig

@hydra.main(config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    print(cfg.database.host)
    print(cfg.dependent_services.course_management.base_url)

if __name__ == "__main__":
    main()
"""