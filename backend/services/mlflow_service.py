"""
MLflow Integration Service
Handles experiment tracking, model logging, and metrics management
"""
import mlflow
from mlflow.tracking import MlflowClient
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import numpy as np
import os

# Lazy imports to avoid circular dependencies
_logger = None
_settings = None


def _get_logger():
    global _logger
    if _logger is None:
        from utils.logger import get_logger
        _logger = get_logger(__name__)
    return _logger


def _get_settings():
    global _settings
    if _settings is None:
        from mlops_config import get_mlops_settings
        _settings = get_mlops_settings()
    return _settings


class MLflowManager:
    """Manager for MLflow experiment tracking and model management"""
    
    def __init__(self):
        """Initialize MLflow manager"""
        self.initialized = False
        self.experiment_id = None
        self.active_runs = {}
        self._connection_attempted = False
        
        # Try to initialize
        self._initialize_mlflow()
    
    def _initialize_mlflow(self):
        """Initialize MLflow with proper error handling"""
        if self._connection_attempted:
            return self.initialized
        
        self._connection_attempted = True
        settings = _get_settings()
        
        try:
            # Set tracking URI
            tracking_uri = settings.MLFLOW_TRACKING_URI
            mlflow.set_tracking_uri(tracking_uri)
            print(f"[MLflow] Tracking URI set to: {tracking_uri}")
            
            # Try to create/get experiment
            try:
                experiment = mlflow.get_experiment_by_name(settings.MLFLOW_EXPERIMENT_NAME)
                if experiment is None:
                    self.experiment_id = mlflow.create_experiment(
                        settings.MLFLOW_EXPERIMENT_NAME,
                        artifact_location=settings.MLFLOW_ARTIFACT_LOCATION
                    )
                    print(f"[MLflow] Created new experiment: {settings.MLFLOW_EXPERIMENT_NAME}")
                else:
                    self.experiment_id = experiment.experiment_id
                    print(f"[MLflow] Using existing experiment: {settings.MLFLOW_EXPERIMENT_NAME}")
                
                mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)
                self.initialized = True
                print(f"[MLflow] Initialized successfully with experiment ID: {self.experiment_id}")
                
            except Exception as e:
                print(f"[MLflow] Could not set experiment (server may not be running): {str(e)}")
                print("[MLflow] Will retry connection on first log attempt")
                
        except Exception as e:
            print(f"[MLflow] Initialization failed (will retry on first use): {str(e)}")
        
        return self.initialized
    
    def _ensure_initialized(self) -> bool:
        """Ensure MLflow is initialized before operations"""
        if not self.initialized:
            self._connection_attempted = False
            self._initialize_mlflow()
        return self.initialized
    
    def start_run(self, run_name: Optional[str] = None) -> Optional[str]:
        """Start a new MLflow run"""
        try:
            if not self._ensure_initialized():
                return None
            
            run = mlflow.start_run(run_name=run_name)
            _get_logger().info(f"[MLflow] Started run: {run.info.run_id}")
            return run.info.run_id
        except Exception as e:
            _get_logger().error(f"[MLflow] Error starting run: {e}")
            return None
    
    def end_run(self):
        """End the current MLflow run"""
        try:
            mlflow.end_run()
            _get_logger().debug("[MLflow] Ended run")
        except Exception as e:
            _get_logger().error(f"[MLflow] Error ending run: {e}")
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters to MLflow"""
        try:
            # Convert all values to strings (MLflow requirement)
            safe_params = {}
            for k, v in params.items():
                try:
                    safe_params[k] = str(v)[:250]  # MLflow has 250 char limit
                except:
                    safe_params[k] = "unknown"
            mlflow.log_params(safe_params)
            _get_logger().debug(f"[MLflow] Logged parameters: {list(params.keys())}")
        except Exception as e:
            _get_logger().error(f"[MLflow] Error logging parameters: {e}")
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics to MLflow"""
        try:
            # Ensure all values are floats
            safe_metrics = {}
            for k, v in metrics.items():
                try:
                    safe_metrics[k] = float(v)
                except (ValueError, TypeError):
                    _get_logger().warning(f"[MLflow] Skipping non-numeric metric {k}: {v}")
            
            if safe_metrics:
                mlflow.log_metrics(safe_metrics, step=step)
                _get_logger().debug(f"[MLflow] Logged metrics: {list(safe_metrics.keys())}")
        except Exception as e:
            _get_logger().error(f"[MLflow] Error logging metrics: {e}")
    
    def log_artifact(self, artifact_path: str, artifact_name: Optional[str] = None):
        """Log an artifact to MLflow"""
        try:
            if os.path.exists(artifact_path):
                mlflow.log_artifact(artifact_path, artifact_name)
                _get_logger().debug(f"[MLflow] Logged artifact: {artifact_path}")
            else:
                _get_logger().warning(f"[MLflow] Artifact path does not exist: {artifact_path}")
        except Exception as e:
            _get_logger().error(f"[MLflow] Error logging artifact: {e}")
    
    def log_dict(self, dictionary: Dict, artifact_file: str):
        """Log a dictionary as JSON artifact"""
        try:
            # Convert datetime objects and numpy types to serializable format
            def serialize(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return str(obj)
            
            serializable_dict = json.loads(json.dumps(dictionary, default=serialize))
            mlflow.log_dict(serializable_dict, artifact_file)
            _get_logger().debug(f"[MLflow] Logged dictionary to: {artifact_file}")
        except Exception as e:
            _get_logger().error(f"[MLflow] Error logging dictionary: {e}")
    
    def log_ingredient_detection(
        self,
        ingredients: List[str],
        confidence_scores: Dict[str, float],
        detection_method: str,
        processing_time: float,
        image_metadata: Dict[str, Any]
    ):
        """Log ingredient detection experiment"""
        if not self._ensure_initialized():
            _get_logger().debug("[MLflow] Not initialized, skipping ingredient detection log")
            return
        
        try:
            run_name = f"ingredient_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with mlflow.start_run(run_name=run_name):
                # Log parameters
                params = {
                    "detection_method": detection_method,
                    "num_ingredients": len(ingredients),
                    "image_size": str(image_metadata.get("size", "unknown")),
                    "image_format": str(image_metadata.get("format", "unknown")),
                    "model": str(image_metadata.get("model", "unknown"))
                }
                self.log_params(params)
                
                # Log metrics
                scores = list(confidence_scores.values()) if confidence_scores else [0]
                avg_confidence = float(np.mean(scores)) if scores else 0.0
                max_confidence = float(max(scores)) if scores else 0.0
                min_confidence = float(min(scores)) if scores else 0.0
                
                metrics = {
                    "processing_time_seconds": processing_time,
                    "avg_confidence_score": avg_confidence,
                    "max_confidence_score": max_confidence,
                    "min_confidence_score": min_confidence,
                    "num_ingredients_detected": float(len(ingredients))
                }
                self.log_metrics(metrics)
                
                # Log detected ingredients as artifact
                detection_data = {
                    "ingredients": ingredients,
                    "confidence_scores": confidence_scores,
                    "timestamp": datetime.now().isoformat(),
                    "detection_method": detection_method
                }
                self.log_dict(detection_data, "ingredient_detection_results.json")
                
                # Log tags
                mlflow.set_tags({
                    "model_type": "ingredient_detection",
                    "detection_method": detection_method,
                    "status": "success" if len(ingredients) > 0 else "failed"
                })
                
                _get_logger().info(f"[MLflow] Logged ingredient detection: {len(ingredients)} ingredients, method={detection_method}")
                
        except Exception as e:
            _get_logger().error(f"[MLflow] Error logging ingredient detection: {e}")
    
    def log_recipe_generation(
        self,
        recipe_title: str,
        ingredients_used: List[str],
        generation_model: str,
        generation_time: float,
        recipe_complexity: str,
        user_satisfaction: Optional[float] = None
    ):
        """Log recipe generation experiment"""
        if not self._ensure_initialized():
            _get_logger().debug("[MLflow] Not initialized, skipping recipe generation log")
            return
        
        try:
            run_name = f"recipe_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with mlflow.start_run(run_name=run_name):
                # Log parameters
                params = {
                    "generation_model": generation_model,
                    "num_ingredients": len(ingredients_used),
                    "recipe_complexity": recipe_complexity,
                    "recipe_title": recipe_title[:100]  # Truncate for param limit
                }
                self.log_params(params)
                
                # Log metrics
                metrics = {
                    "generation_time_seconds": generation_time,
                    "num_ingredients_used": float(len(ingredients_used))
                }
                
                if user_satisfaction is not None:
                    metrics["user_satisfaction_score"] = user_satisfaction
                
                self.log_metrics(metrics)
                
                # Log recipe data as artifact
                recipe_data = {
                    "recipe_title": recipe_title,
                    "ingredients": ingredients_used,
                    "complexity": recipe_complexity,
                    "timestamp": datetime.now().isoformat(),
                    "model": generation_model
                }
                self.log_dict(recipe_data, "recipe_generation_results.json")
                
                # Log tags
                mlflow.set_tags({
                    "model_type": "recipe_generation",
                    "generation_model": generation_model,
                    "recipe_complexity": recipe_complexity
                })
                
                _get_logger().info(f"[MLflow] Logged recipe generation: '{recipe_title}', model={generation_model}")
                
        except Exception as e:
            _get_logger().error(f"[MLflow] Error logging recipe generation: {e}")
    
    def log_model_performance(
        self,
        model_name: str,
        metrics: Dict[str, float],
        model_version: Optional[str] = None
    ):
        """Log overall model performance metrics"""
        if not self._ensure_initialized():
            return
        
        try:
            run_name = f"model_performance_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with mlflow.start_run(run_name=run_name):
                params = {
                    "model_name": model_name,
                    "model_version": model_version or "latest"
                }
                self.log_params(params)
                self.log_metrics(metrics)
                
                mlflow.set_tags({
                    "model_name": model_name,
                    "evaluation_type": "performance_monitoring"
                })
                
                _get_logger().info(f"[MLflow] Logged model performance for: {model_name}")
                
        except Exception as e:
            _get_logger().error(f"[MLflow] Error logging model performance: {e}")
    
    def get_best_run(self, metric_name: str = "avg_confidence_score") -> Optional[Dict]:
        """Get the best run based on a specific metric"""
        if not self._ensure_initialized():
            return None
        
        try:
            settings = _get_settings()
            experiment = mlflow.get_experiment_by_name(settings.MLFLOW_EXPERIMENT_NAME)
            if not experiment:
                return None
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=[f"metrics.{metric_name} DESC"],
                max_results=1
            )
            
            if not runs.empty:
                best_run = runs.iloc[0].to_dict()
                _get_logger().info(f"[MLflow] Found best run with {metric_name}: {best_run.get(f'metrics.{metric_name}')}")
                return best_run
            
            return None
        except Exception as e:
            _get_logger().error(f"[MLflow] Error getting best run: {e}")
            return None
    
    def compare_models(
        self,
        model_names: List[str],
        metric_name: str = "processing_time_seconds"
    ) -> Dict[str, Any]:
        """Compare multiple models based on a metric"""
        if not self._ensure_initialized():
            return {}
        
        try:
            settings = _get_settings()
            experiment = mlflow.get_experiment_by_name(settings.MLFLOW_EXPERIMENT_NAME)
            if not experiment:
                return {}
            
            comparison_results = {}
            
            for model_name in model_names:
                runs = mlflow.search_runs(
                    experiment_ids=[experiment.experiment_id],
                    filter_string=f"tags.model_name = '{model_name}'",
                    order_by=[f"metrics.{metric_name} ASC"]
                )
                
                if not runs.empty:
                    avg_metric = runs[f"metrics.{metric_name}"].mean()
                    comparison_results[model_name] = {
                        "avg_metric": float(avg_metric),
                        "num_runs": len(runs)
                    }
            
            _get_logger().info(f"[MLflow] Compared {len(model_names)} models on {metric_name}")
            return comparison_results
        except Exception as e:
            _get_logger().error(f"[MLflow] Error comparing models: {e}")
            return {}
    
    def get_experiment_summary(self) -> Dict[str, Any]:
        """Get summary of the current experiment"""
        if not self._ensure_initialized():
            return {"error": "MLflow not initialized"}
        
        try:
            settings = _get_settings()
            experiment = mlflow.get_experiment_by_name(settings.MLFLOW_EXPERIMENT_NAME)
            if not experiment:
                return {"error": "Experiment not found"}
            
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                max_results=1000
            )
            
            return {
                "experiment_name": settings.MLFLOW_EXPERIMENT_NAME,
                "experiment_id": experiment.experiment_id,
                "total_runs": len(runs),
                "artifact_location": experiment.artifact_location,
                "lifecycle_stage": experiment.lifecycle_stage
            }
        except Exception as e:
            _get_logger().error(f"[MLflow] Error getting experiment summary: {e}")
            return {"error": str(e)}


# Global MLflow manager instance
mlflow_manager = MLflowManager()