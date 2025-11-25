"""
Model Monitoring Service
Handles model drift detection, performance monitoring, and data quality checks
"""
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import deque, defaultdict

# Lazy imports to avoid circular dependencies
_logger = None
_settings = None
_prometheus_metrics = None
_mlflow_manager = None


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


def _get_prometheus():
    global _prometheus_metrics
    if _prometheus_metrics is None:
        try:
            from services.prometheus_service import prometheus_metrics
            _prometheus_metrics = prometheus_metrics
        except Exception as e:
            _get_logger().warning(f"Could not load prometheus_metrics: {e}")
    return _prometheus_metrics


def _get_mlflow():
    global _mlflow_manager
    if _mlflow_manager is None:
        try:
            from services.mlflow_service import mlflow_manager
            _mlflow_manager = mlflow_manager
        except Exception as e:
            _get_logger().warning(f"Could not load mlflow_manager: {e}")
    return _mlflow_manager


class ModelMonitor:
    """Monitor model performance and detect drift"""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize model monitor
        
        Args:
            window_size: Size of the sliding window for monitoring
        """
        self.window_size = window_size
        
        # Store recent predictions and metrics
        self.prediction_history = defaultdict(lambda: deque(maxlen=window_size))
        self.confidence_history = defaultdict(lambda: deque(maxlen=window_size))
        self.latency_history = defaultdict(lambda: deque(maxlen=window_size))
        
        # Store baseline statistics
        self.baseline_stats = {}
        
        # Store detected drift events
        self.drift_events = []
        
        print(f"[ModelMonitor] Initialized with window size: {window_size}")
    
    def record_prediction(
        self,
        model_name: str,
        prediction: Any = None,
        confidence: float = None,
        latency: float = None,
        input_features: Optional[Dict] = None,
        # Support dict format for backward compatibility
        prediction_data: Optional[Dict] = None
    ):
        """
        Record a prediction for monitoring
        
        Supports two calling conventions:
        1. Explicit: model_name, prediction, confidence, latency, input_features
        2. Dict format: model_name, prediction_data={'confidence': x, 'latency': y}
        """
        timestamp = datetime.now()
        
        # Handle dict format (backward compatibility)
        if prediction_data is not None:
            confidence = prediction_data.get('confidence', confidence)
            latency = prediction_data.get('latency', latency)
            prediction = prediction_data.get('prediction', prediction)
        
        # Default values if not provided
        confidence = confidence if confidence is not None else 0.0
        latency = latency if latency is not None else 0.0
        
        # Store prediction data
        prediction_record = {
            "timestamp": timestamp,
            "prediction": prediction,
            "confidence": confidence,
            "latency": latency,
            "input_features": input_features
        }
        
        self.prediction_history[model_name].append(prediction_record)
        self.confidence_history[model_name].append(confidence)
        self.latency_history[model_name].append(latency)
        
        # Update Prometheus metrics
        try:
            prometheus = _get_prometheus()
            if prometheus:
                prometheus.set_model_performance_score(
                    model_name=model_name,
                    metric="avg_confidence",
                    score=float(np.mean(list(self.confidence_history[model_name])))
                )
                prometheus.set_model_performance_score(
                    model_name=model_name,
                    metric="avg_latency",
                    score=float(np.mean(list(self.latency_history[model_name])))
                )
        except Exception as e:
            _get_logger().debug(f"Could not update Prometheus metrics: {e}")
        
        _get_logger().debug(f"[ModelMonitor] Recorded prediction for {model_name}: confidence={confidence:.4f}, latency={latency:.4f}s")
    
    def set_baseline(self, model_name: str, baseline_data: Dict[str, Any]):
        """
        Set baseline statistics for drift detection
        
        Args:
            model_name: Name of the model
            baseline_data: Baseline statistics
        """
        settings = _get_settings()
        
        self.baseline_stats[model_name] = {
            "confidence_mean": baseline_data.get("confidence_mean", settings.BASELINE_CONFIDENCE_MEAN),
            "confidence_std": baseline_data.get("confidence_std", settings.BASELINE_CONFIDENCE_STD),
            "latency_mean": baseline_data.get("latency_mean", settings.BASELINE_LATENCY_MEAN),
            "latency_std": baseline_data.get("latency_std", settings.BASELINE_LATENCY_STD),
            "prediction_distribution": baseline_data.get("prediction_distribution", {}),
            "timestamp": datetime.now()
        }
        
        _get_logger().info(f"[ModelMonitor] Set baseline for {model_name}: confidence_mean={self.baseline_stats[model_name]['confidence_mean']:.2f}")
    
    def check_drift(
        self,
        model_name: str,
        current_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Quick drift check based on current metrics (for use in inference pipeline)
        
        This method is called during inference to quickly check if current
        metrics deviate significantly from baseline.
        
        Args:
            model_name: Name of the model
            current_metrics: Current metrics to check (e.g., {'confidence': 0.8, 'latency': 2.5})
            
        Returns:
            Dictionary containing drift detection results
        """
        settings = _get_settings()
        
        # Auto-initialize baseline if not set
        if model_name not in self.baseline_stats:
            self.set_baseline(model_name, {})
            _get_logger().info(f"[ModelMonitor] Auto-initialized baseline for {model_name}")
        
        baseline = self.baseline_stats[model_name]
        drift_detected = False
        drift_score = 0.0
        drift_details = {}
        
        if current_metrics:
            # Check confidence drift
            if 'confidence' in current_metrics:
                current_conf = current_metrics['confidence']
                baseline_mean = baseline['confidence_mean']
                baseline_std = baseline['confidence_std']
                
                conf_diff = abs(current_conf - baseline_mean) / (baseline_std + 1e-10)
                drift_details['confidence_deviation'] = float(conf_diff)
                drift_score = max(drift_score, conf_diff)
            
            # Check latency drift
            if 'latency' in current_metrics:
                current_lat = current_metrics['latency']
                baseline_lat_mean = baseline['latency_mean']
                baseline_lat_std = baseline['latency_std']
                
                lat_diff = abs(current_lat - baseline_lat_mean) / (baseline_lat_std + 1e-10)
                drift_details['latency_deviation'] = float(lat_diff)
                drift_score = max(drift_score, lat_diff)
        
        drift_detected = drift_score > settings.DRIFT_DETECTION_THRESHOLD
        
        # Track drift event if detected
        if drift_detected:
            try:
                prometheus = _get_prometheus()
                if prometheus:
                    prometheus.set_data_drift_score(
                        feature=f"{model_name}_quick_check",
                        score=drift_score
                    )
                    prometheus.track_drift_event(
                        model_name=model_name,
                        drift_type="quick_check",
                        severity="high" if drift_score > 0.3 else "medium"
                    )
            except Exception as e:
                _get_logger().debug(f"Could not update Prometheus drift metrics: {e}")
        
        return {
            "drift_detected": drift_detected,
            "drift_score": float(drift_score),
            "drift_type": "quick_check",
            "details": drift_details,
            "threshold": settings.DRIFT_DETECTION_THRESHOLD,
            "timestamp": datetime.now().isoformat()
        }
    
    def detect_drift(
        self,
        model_name: str,
        drift_type: str = "confidence"
    ) -> Dict[str, Any]:
        """
        Detect drift in model predictions using historical data
        
        Args:
            model_name: Name of the model
            drift_type: Type of drift to detect (confidence/latency)
            
        Returns:
            Dictionary containing drift detection results
        """
        settings = _get_settings()
        
        if model_name not in self.baseline_stats:
            _get_logger().warning(f"No baseline set for {model_name}, cannot detect drift")
            return {"drift_detected": False, "reason": "no_baseline"}
        
        if model_name not in self.prediction_history or len(self.prediction_history[model_name]) < 30:
            _get_logger().warning(f"Insufficient data for drift detection on {model_name}")
            return {"drift_detected": False, "reason": "insufficient_data"}
        
        baseline = self.baseline_stats[model_name]
        drift_detected = False
        drift_score = 0.0
        drift_details = {}
        
        if drift_type == "confidence":
            recent_confidences = list(self.confidence_history[model_name])[-100:]
            
            current_mean = float(np.mean(recent_confidences))
            current_std = float(np.std(recent_confidences))
            baseline_mean = baseline["confidence_mean"]
            baseline_std = baseline["confidence_std"]
            
            mean_diff = abs(current_mean - baseline_mean) / (baseline_std + 1e-10)
            std_diff = abs(current_std - baseline_std) / (baseline_std + 1e-10)
            drift_score = (mean_diff + std_diff) / 2
            
            drift_detected = drift_score > settings.DRIFT_DETECTION_THRESHOLD
            
            drift_details = {
                "current_mean": current_mean,
                "baseline_mean": float(baseline_mean),
                "current_std": current_std,
                "baseline_std": float(baseline_std),
                "mean_diff": float(mean_diff),
                "std_diff": float(std_diff)
            }
            
        elif drift_type == "latency":
            recent_latencies = list(self.latency_history[model_name])[-100:]
            
            current_mean = float(np.mean(recent_latencies))
            baseline_mean = baseline["latency_mean"]
            baseline_std = baseline["latency_std"]
            
            drift_score = abs(current_mean - baseline_mean) / (baseline_std + 1e-10)
            drift_detected = drift_score > settings.DRIFT_DETECTION_THRESHOLD
            
            drift_details = {
                "current_mean_latency": current_mean,
                "baseline_mean_latency": float(baseline_mean),
                "latency_increase_pct": float(((current_mean - baseline_mean) / baseline_mean) * 100) if baseline_mean > 0 else 0
            }
        
        # Update Prometheus metric
        try:
            prometheus = _get_prometheus()
            if prometheus:
                prometheus.set_data_drift_score(
                    feature=f"{model_name}_{drift_type}",
                    score=float(drift_score)
                )
        except Exception as e:
            _get_logger().debug(f"Could not update Prometheus drift score: {e}")
        
        if drift_detected:
            severity = "high" if drift_score > 0.3 else "medium"
            drift_event = {
                "model_name": model_name,
                "drift_type": drift_type,
                "drift_score": float(drift_score),
                "drift_details": drift_details,
                "timestamp": datetime.now(),
                "severity": severity
            }
            
            self.drift_events.append(drift_event)
            
            # Track in Prometheus
            try:
                prometheus = _get_prometheus()
                if prometheus:
                    prometheus.track_drift_event(
                        model_name=model_name,
                        drift_type=drift_type,
                        severity=severity
                    )
            except Exception as e:
                _get_logger().debug(f"Could not track drift event in Prometheus: {e}")
            
            # Log to MLflow
            try:
                mlflow = _get_mlflow()
                if mlflow:
                    mlflow.log_metrics({
                        f"{model_name}_drift_score": drift_score,
                        f"{model_name}_drift_detected": 1.0
                    })
            except Exception as e:
                _get_logger().debug(f"Could not log drift to MLflow: {e}")
            
            _get_logger().warning(f"[ModelMonitor] Drift detected for {model_name} ({drift_type}): score={drift_score:.4f}")
        
        return {
            "drift_detected": drift_detected,
            "drift_score": float(drift_score),
            "drift_type": drift_type,
            "details": drift_details,
            "threshold": settings.DRIFT_DETECTION_THRESHOLD,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_model_performance_summary(self, model_name: str) -> Dict[str, Any]:
        """Get performance summary for a model"""
        if model_name not in self.prediction_history:
            return {"error": "No data available for model", "model_name": model_name}
        
        recent_predictions = list(self.prediction_history[model_name])[-100:]
        
        if not recent_predictions:
            return {"error": "No recent predictions", "model_name": model_name}
        
        confidences = [p["confidence"] for p in recent_predictions if p["confidence"] is not None]
        latencies = [p["latency"] for p in recent_predictions if p["latency"] is not None]
        
        summary = {
            "model_name": model_name,
            "total_predictions": len(self.prediction_history[model_name]),
            "recent_predictions": len(recent_predictions),
            "timestamp": datetime.now().isoformat()
        }
        
        if confidences:
            summary["confidence"] = {
                "mean": float(np.mean(confidences)),
                "std": float(np.std(confidences)),
                "min": float(np.min(confidences)),
                "max": float(np.max(confidences)),
                "percentile_50": float(np.percentile(confidences, 50)),
                "percentile_95": float(np.percentile(confidences, 95))
            }
        
        if latencies:
            summary["latency"] = {
                "mean": float(np.mean(latencies)),
                "std": float(np.std(latencies)),
                "min": float(np.min(latencies)),
                "max": float(np.max(latencies)),
                "percentile_50": float(np.percentile(latencies, 50)),
                "percentile_95": float(np.percentile(latencies, 95))
            }
        
        return summary
    
    def get_drift_events(
        self,
        model_name: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict]:
        """Get recent drift events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_events = []
        for event in self.drift_events:
            event_time = event["timestamp"]
            if event_time > cutoff_time:
                if model_name is None or event["model_name"] == model_name:
                    # Serialize datetime for JSON
                    event_copy = {
                        **event,
                        "timestamp": event_time.isoformat() if isinstance(event_time, datetime) else event_time
                    }
                    filtered_events.append(event_copy)
        
        return filtered_events
    
    def check_data_quality(self, data: List[Dict]) -> Dict[str, Any]:
        """Check data quality metrics"""
        if not data:
            return {"error": "No data provided"}
        
        quality_report = {
            "total_samples": len(data),
            "timestamp": datetime.now().isoformat()
        }
        
        # Check for missing values
        if isinstance(data[0], dict):
            missing_counts = defaultdict(int)
            for item in data:
                for key, value in item.items():
                    if value is None or value == "":
                        missing_counts[key] += 1
            
            quality_report["missing_values"] = dict(missing_counts)
            quality_report["missing_rate"] = {
                k: v / len(data) for k, v in missing_counts.items()
            }
        
        # Check for outliers in numerical fields
        numerical_outliers = {}
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, (int, float)):
                        if key not in numerical_outliers:
                            numerical_outliers[key] = []
                        numerical_outliers[key].append(value)
        
        outlier_summary = {}
        for key, values in numerical_outliers.items():
            if len(values) > 10:
                q1 = np.percentile(values, 25)
                q3 = np.percentile(values, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = [v for v in values if v < lower_bound or v > upper_bound]
                outlier_summary[key] = {
                    "count": len(outliers),
                    "percentage": (len(outliers) / len(values)) * 100
                }
        
        quality_report["outliers"] = outlier_summary
        
        return quality_report
    
    def generate_monitoring_report(self, models: List[str]) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "models": {},
            "summary": {
                "total_models": len(models),
                "models_with_data": 0,
                "models_with_drift": 0
            }
        }
        
        for model_name in models:
            model_report = {
                "performance_summary": self.get_model_performance_summary(model_name),
                "recent_drift_events": self.get_drift_events(model_name=model_name, hours=24),
                "drift_checks": {}
            }
            
            # Only run drift detection if we have data
            if "error" not in model_report["performance_summary"]:
                report["summary"]["models_with_data"] += 1
                model_report["drift_checks"] = {
                    "confidence": self.detect_drift(model_name, "confidence"),
                    "latency": self.detect_drift(model_name, "latency")
                }
                
                if (model_report["drift_checks"]["confidence"].get("drift_detected") or 
                    model_report["drift_checks"]["latency"].get("drift_detected")):
                    report["summary"]["models_with_drift"] += 1
            
            report["models"][model_name] = model_report
        
        _get_logger().info(f"[ModelMonitor] Generated monitoring report for {len(models)} models")
        return report
    
    def get_all_baselines(self) -> Dict[str, Dict]:
        """Get all baseline configurations"""
        return {
            model: {
                **baseline,
                "timestamp": baseline["timestamp"].isoformat() if isinstance(baseline["timestamp"], datetime) else baseline["timestamp"]
            }
            for model, baseline in self.baseline_stats.items()
        }


# Global model monitor instance
model_monitor = ModelMonitor()