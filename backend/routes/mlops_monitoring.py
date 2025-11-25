"""
MLOps Monitoring Routes
Provides endpoints for Prometheus metrics, model monitoring, and observability dashboards
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse
from typing import List, Optional
from datetime import datetime

from services.prometheus_service import prometheus_metrics
from services.model_monitoring_service import model_monitor
from services.mlflow_service import mlflow_manager
from mlops_config import get_mlops_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_mlops_settings()

router = APIRouter(prefix="/mlops", tags=["MLOps Monitoring"])


# ============================================================================
# PROMETHEUS METRICS ENDPOINT
# ============================================================================

@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    This endpoint exposes all application metrics in Prometheus format.
    Configure Prometheus to scrape this endpoint.
    
    Example prometheus.yml config:
    ```yaml
    scrape_configs:
      - job_name: 'flavourcraft'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/mlops/metrics'
    ```
    """
    try:
        metrics = prometheus_metrics.get_metrics()
        return Response(
            content=metrics,
            media_type="text/plain; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL MONITORING ENDPOINTS
# ============================================================================

@router.get("/models/summary")
async def get_models_summary():
    """
    Get summary of all monitored models
    
    Returns performance metrics and drift status for all models.
    """
    models = [
        "clip_ingredient_detector",
        "openai_vision",
        "openai_recipe_generator",
        "ingredient_detection_pipeline"
    ]
    
    try:
        report = model_monitor.generate_monitoring_report(models)
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        logger.error(f"Error generating models summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}/performance")
async def get_model_performance(model_name: str):
    """
    Get performance metrics for a specific model
    
    Args:
        model_name: Name of the model to query
    """
    try:
        summary = model_monitor.get_model_performance_summary(model_name)
        return {
            "status": "success",
            "model_name": model_name,
            "performance": summary
        }
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}/drift")
async def check_model_drift(
    model_name: str,
    drift_type: str = "confidence"
):
    """
    Check for drift in a specific model
    
    Args:
        model_name: Name of the model to check
        drift_type: Type of drift to check (confidence/latency)
    """
    try:
        drift_result = model_monitor.detect_drift(model_name, drift_type)
        return {
            "status": "success",
            "model_name": model_name,
            "drift_result": drift_result
        }
    except Exception as e:
        logger.error(f"Error checking model drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drift/events")
async def get_drift_events(
    model_name: Optional[str] = None,
    hours: int = 24
):
    """
    Get recent drift events
    
    Args:
        model_name: Optional filter by model name
        hours: Number of hours to look back (default: 24)
    """
    try:
        events = model_monitor.get_drift_events(model_name=model_name, hours=hours)
        return {
            "status": "success",
            "total_events": len(events),
            "hours": hours,
            "model_filter": model_name,
            "events": events
        }
    except Exception as e:
        logger.error(f"Error getting drift events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_name}/baseline")
async def set_model_baseline(
    model_name: str,
    confidence_mean: float = 0.70,
    confidence_std: float = 0.15,
    latency_mean: float = 2.0,
    latency_std: float = 0.5
):
    """
    Set baseline statistics for a model
    
    This is used for drift detection. Set the expected performance
    characteristics for a model under normal conditions.
    """
    try:
        baseline_data = {
            "confidence_mean": confidence_mean,
            "confidence_std": confidence_std,
            "latency_mean": latency_mean,
            "latency_std": latency_std
        }
        
        model_monitor.set_baseline(model_name, baseline_data)
        
        return {
            "status": "success",
            "message": f"Baseline set for {model_name}",
            "baseline": baseline_data
        }
    except Exception as e:
        logger.error(f"Error setting baseline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/baselines")
async def get_all_baselines():
    """Get all model baselines"""
    try:
        baselines = model_monitor.get_all_baselines()
        return {
            "status": "success",
            "baselines": baselines
        }
    except Exception as e:
        logger.error(f"Error getting baselines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MLFLOW ENDPOINTS
# ============================================================================

@router.get("/mlflow/summary")
async def get_mlflow_summary():
    """
    Get MLflow experiment summary
    
    Returns information about the MLflow experiment including
    total runs and configuration.
    """
    try:
        summary = mlflow_manager.get_experiment_summary()
        return {
            "status": "success",
            "mlflow": summary
        }
    except Exception as e:
        logger.error(f"Error getting MLflow summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mlflow/best-run")
async def get_best_mlflow_run(metric_name: str = "avg_confidence_score"):
    """
    Get the best MLflow run based on a metric
    
    Args:
        metric_name: Metric to optimize (default: avg_confidence_score)
    """
    try:
        best_run = mlflow_manager.get_best_run(metric_name)
        if best_run:
            return {
                "status": "success",
                "metric": metric_name,
                "best_run": best_run
            }
        else:
            return {
                "status": "success",
                "message": "No runs found"
            }
    except Exception as e:
        logger.error(f"Error getting best run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mlflow/compare")
async def compare_models(
    models: str = "clip_ingredient_detector,openai_vision",
    metric: str = "processing_time_seconds"
):
    """
    Compare multiple models
    
    Args:
        models: Comma-separated list of model names
        metric: Metric to compare
    """
    try:
        model_list = [m.strip() for m in models.split(",")]
        comparison = mlflow_manager.compare_models(model_list, metric)
        return {
            "status": "success",
            "metric": metric,
            "comparison": comparison
        }
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SYSTEM HEALTH & STATUS
# ============================================================================

@router.get("/health")
async def mlops_health_check():
    """
    MLOps system health check
    
    Returns the status of all MLOps components.
    """
    try:
        # Check Prometheus
        prometheus_status = "healthy"
        try:
            prometheus_metrics.get_metrics()
        except Exception as e:
            prometheus_status = f"error: {str(e)}"
        
        # Check MLflow
        mlflow_status = "healthy"
        try:
            mlflow_manager.get_experiment_summary()
        except Exception as e:
            mlflow_status = f"error: {str(e)}"
        
        # Check Model Monitor
        monitor_status = "healthy"
        try:
            model_monitor.get_all_baselines()
        except Exception as e:
            monitor_status = f"error: {str(e)}"
        
        all_healthy = all(
            status == "healthy" 
            for status in [prometheus_status, mlflow_status, monitor_status]
        )
        
        # Update Prometheus health metric
        prometheus_metrics.set_system_health(all_healthy)
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "prometheus": prometheus_status,
                "mlflow": mlflow_status,
                "model_monitor": monitor_status
            },
            "config": {
                "mlflow_tracking_uri": settings.MLFLOW_TRACKING_URI,
                "drift_detection_enabled": settings.ENABLE_DRIFT_DETECTION,
                "drift_threshold": settings.DRIFT_DETECTION_THRESHOLD
            }
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_mlops_config():
    """
    Get current MLOps configuration
    """
    return {
        "mlflow": {
            "tracking_uri": settings.MLFLOW_TRACKING_URI,
            "experiment_name": settings.MLFLOW_EXPERIMENT_NAME
        },
        "prometheus": {
            "enabled": settings.PROMETHEUS_ENABLED,
            "port": settings.PROMETHEUS_PORT
        },
        "monitoring": {
            "drift_detection_enabled": settings.ENABLE_DRIFT_DETECTION,
            "drift_threshold": settings.DRIFT_DETECTION_THRESHOLD,
            "window_size": settings.DRIFT_WINDOW_SIZE
        },
        "thresholds": {
            "latency_alert": settings.LATENCY_ALERT_THRESHOLD,
            "error_rate_alert": settings.ERROR_RATE_ALERT_THRESHOLD,
            "confidence_alert": settings.CONFIDENCE_ALERT_THRESHOLD
        }
    }


# ============================================================================
# INITIALIZATION ENDPOINT
# ============================================================================

@router.post("/initialize")
async def initialize_mlops():
    """
    Initialize MLOps baselines and settings
    
    This endpoint sets up default baselines for all models.
    Call this once when starting a new deployment.
    """
    try:
        # Initialize baselines for all models
        models_config = {
            "clip_ingredient_detector": {
                "confidence_mean": 0.65,
                "confidence_std": 0.15,
                "latency_mean": 1.8,
                "latency_std": 0.5
            },
            "openai_vision": {
                "confidence_mean": 0.85,
                "confidence_std": 0.10,
                "latency_mean": 2.5,
                "latency_std": 0.8
            },
            "openai_recipe_generator": {
                "confidence_mean": 0.85,
                "confidence_std": 0.10,
                "latency_mean": 3.0,
                "latency_std": 1.0
            },
            "ingredient_detection_pipeline": {
                "confidence_mean": 0.70,
                "confidence_std": 0.15,
                "latency_mean": 2.5,
                "latency_std": 0.8
            }
        }
        
        for model_name, config in models_config.items():
            model_monitor.set_baseline(model_name, config)
        
        # Set system info
        prometheus_metrics.set_system_info({
            "version": "1.0.0",
            "environment": "production",
            "mlflow_experiment": settings.MLFLOW_EXPERIMENT_NAME
        })
        
        prometheus_metrics.set_system_health(True)
        
        logger.info("MLOps system initialized successfully")
        
        return {
            "status": "success",
            "message": "MLOps system initialized",
            "models_configured": list(models_config.keys()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error initializing MLOps: {e}")
        raise HTTPException(status_code=500, detail=str(e))