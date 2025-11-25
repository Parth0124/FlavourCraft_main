"""
MLOps Configuration for FlavourCraft
Centralized configuration for experiment tracking, monitoring, and observability
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class MLOpsSettings(BaseSettings):
    """MLOps configuration settings"""
    
    # MLflow Configuration
    MLFLOW_TRACKING_URI: str = "http://localhost:5001"
    MLFLOW_EXPERIMENT_NAME: str = "flavourcraft-recipe-generation"
    MLFLOW_ARTIFACT_LOCATION: str = "./mlruns"
    
    # Prometheus Configuration
    PROMETHEUS_PORT: int = 8001
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_MULTIPROCESS_DIR: str = "/tmp/prometheus_multiproc"
    
    # Model Monitoring Configuration
    ENABLE_DRIFT_DETECTION: bool = True
    DRIFT_DETECTION_THRESHOLD: float = 0.15
    DRIFT_WINDOW_SIZE: int = 1000
    PREDICTION_LOGGING_ENABLED: bool = True
    
    # Performance Thresholds
    INGREDIENT_DETECTION_LATENCY_THRESHOLD: float = 5.0
    RECIPE_GENERATION_LATENCY_THRESHOLD: float = 10.0
    MIN_CONFIDENCE_THRESHOLD: float = 0.40
    LATENCY_ALERT_THRESHOLD: float = 5.0
    ERROR_RATE_ALERT_THRESHOLD: float = 0.1
    CONFIDENCE_ALERT_THRESHOLD: float = 0.3
    
    # Baseline Configuration (defaults for drift detection)
    BASELINE_CONFIDENCE_MEAN: float = 0.70
    BASELINE_CONFIDENCE_STD: float = 0.15
    BASELINE_LATENCY_MEAN: float = 2.0
    BASELINE_LATENCY_STD: float = 0.5
    
    # Monitoring Intervals
    METRICS_COLLECTION_INTERVAL: int = 60
    DRIFT_CHECK_INTERVAL: int = 300
    PERFORMANCE_LOG_INTERVAL: int = 100
    
    # Data Quality
    MAX_INGREDIENT_COUNT: int = 50
    MIN_INGREDIENT_COUNT: int = 1
    
    # Logging
    STRUCTURED_LOGGING_ENABLED: bool = True
    LOG_PREDICTIONS: bool = True
    LOG_ERRORS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_mlops_settings() -> MLOpsSettings:
    """Get cached MLOps settings instance"""
    return MLOpsSettings()