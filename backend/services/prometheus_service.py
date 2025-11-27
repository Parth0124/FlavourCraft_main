"""
Prometheus Metrics Service
Collects and exposes metrics for monitoring and alerting
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from typing import Dict, Optional
import time
from functools import wraps

# Lazy import to avoid circular dependencies
_logger = None


def _get_logger():
    global _logger
    if _logger is None:
        from utils.logger import get_logger
        _logger = get_logger(__name__)
    return _logger


class PrometheusMetrics:
    """Prometheus metrics collector for FlavourCraft"""
    
    def __init__(self):
        """Initialize Prometheus metrics"""
        
        # API Request Metrics
        self.api_requests_total = Counter(
            'flavourcraft_api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status']
        )
        
        self.api_request_duration = Histogram(
            'flavourcraft_api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
        )
        
        # Ingredient Detection Metrics
        self.ingredient_detections_total = Counter(
            'flavourcraft_ingredient_detections_total',
            'Total number of ingredient detections',
            ['model_name', 'status']
        )
        
        self.ingredient_detection_duration = Histogram(
            'flavourcraft_ingredient_detection_duration_seconds',
            'Ingredient detection duration in seconds',
            ['model_name'],
            buckets=(0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0)
        )
        
        self.ingredients_detected_count = Histogram(
            'flavourcraft_ingredients_detected_count',
            'Number of ingredients detected per request',
            ['model_name'],
            buckets=(0, 1, 2, 3, 5, 8, 10, 15, 20)
        )
        
        self.ingredient_confidence_score = Histogram(
            'flavourcraft_ingredient_confidence_score',
            'Confidence scores for detected ingredients',
            ['model_name'],
            buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
        )
        
        # Recipe Generation Metrics
        self.recipe_generations_total = Counter(
            'flavourcraft_recipe_generations_total',
            'Total number of recipe generations',
            ['model', 'status']
        )
        
        self.recipe_generation_duration = Histogram(
            'flavourcraft_recipe_generation_duration_seconds',
            'Recipe generation duration in seconds',
            ['model'],
            buckets=(1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0, 60.0)
        )
        
        self.recipe_complexity_distribution = Counter(
            'flavourcraft_recipe_complexity_distribution',
            'Distribution of recipe complexity levels',
            ['complexity']
        )
        
        # Model Performance Metrics
        self.model_prediction_errors = Counter(
            'flavourcraft_model_prediction_errors_total',
            'Total number of model prediction errors',
            ['model_name', 'error_type']
        )
        
        self.openai_api_calls = Counter(
            'flavourcraft_openai_api_calls_total',
            'Total number of OpenAI API calls',
            ['operation', 'status']
        )
        
        self.openai_api_latency = Histogram(
            'flavourcraft_openai_api_latency_seconds',
            'OpenAI API call latency',
            ['operation'],
            buckets=(0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0)
        )
        
        self.openai_tokens_used = Counter(
            'flavourcraft_openai_tokens_used_total',
            'Total OpenAI tokens used',
            ['operation']
        )
        
        self.openai_cost_estimate = Counter(
            'flavourcraft_openai_cost_estimate_total',
            'Estimated OpenAI API costs',
            ['operation']
        )
        
        # Data Quality Metrics
        self.image_upload_size = Histogram(
            'flavourcraft_image_upload_size_bytes',
            'Size of uploaded images in bytes',
            buckets=(10000, 50000, 100000, 500000, 1000000, 5000000, 10000000)
        )
        
        self.image_processing_errors = Counter(
            'flavourcraft_image_processing_errors_total',
            'Total number of image processing errors',
            ['error_type']
        )
        
        # User Activity Metrics
        self.active_users = Gauge(
            'flavourcraft_active_users',
            'Number of currently active users'
        )
        
        self.user_registrations_total = Counter(
            'flavourcraft_user_registrations_total',
            'Total number of user registrations'
        )
        
        self.user_logins_total = Counter(
            'flavourcraft_user_logins_total',
            'Total number of user logins',
            ['status']
        )
        
        # Database Metrics
        self.database_operations_total = Counter(
            'flavourcraft_database_operations_total',
            'Total number of database operations',
            ['operation', 'collection', 'status']
        )
        
        self.database_operation_duration = Histogram(
            'flavourcraft_database_operation_duration_seconds',
            'Database operation duration in seconds',
            ['operation', 'collection'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
        )
        
        # System Health Metrics
        self.system_health = Gauge(
            'flavourcraft_system_health',
            'System health status (1 = healthy, 0 = unhealthy)'
        )
        
        self.system_info = Info(
            'flavourcraft_system',
            'System information'
        )
        
        # Model Drift Metrics
        self.data_drift_score = Gauge(
            'flavourcraft_data_drift_score',
            'Data drift score',
            ['feature']
        )
        
        self.model_performance_score = Gauge(
            'flavourcraft_model_performance_score',
            'Model performance score',
            ['model_name', 'metric']
        )
        
        self.drift_events_total = Counter(
            'flavourcraft_drift_events_total',
            'Total drift events detected',
            ['model_name', 'drift_type', 'severity']
        )
        
        self._initialized = True
        print("[Prometheus] Metrics initialized successfully")
    
    def track_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """Track API request metrics"""
        self.api_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def track_ingredient_detection(
        self,
        model_name: str,
        num_ingredients: int,
        confidence_score: float,
        processing_time: float,
        success: bool
    ):
        """
        Track ingredient detection metrics
        
        Args:
            model_name: Name of the detection model (e.g., 'clip_ingredient_detector', 'openai_vision')
            num_ingredients: Number of ingredients detected
            confidence_score: Average confidence score
            processing_time: Detection duration in seconds
            success: Whether detection was successful
        """
        status = "success" if success else "failure"
        
        self.ingredient_detections_total.labels(model_name=model_name, status=status).inc()
        self.ingredient_detection_duration.labels(model_name=model_name).observe(processing_time)
        self.ingredients_detected_count.labels(model_name=model_name).observe(num_ingredients)
        
        if confidence_score > 0:
            self.ingredient_confidence_score.labels(model_name=model_name).observe(confidence_score)
        
        _get_logger().debug(f"[Prometheus] Tracked ingredient detection: model={model_name}, ingredients={num_ingredients}, confidence={confidence_score:.2f}")
    
    def track_recipe_generation(
        self,
        model: str,
        status: str,
        duration: float,
        complexity: str
    ):
        """Track recipe generation metrics"""
        self.recipe_generations_total.labels(model=model, status=status).inc()
        self.recipe_generation_duration.labels(model=model).observe(duration)
        
        if complexity and complexity != "unknown":
            self.recipe_complexity_distribution.labels(complexity=complexity).inc()
        
        _get_logger().debug(f"[Prometheus] Tracked recipe generation: model={model}, status={status}, duration={duration:.2f}s")
    
    def track_openai_api_call(
        self,
        operation: str = None,
        status: str = None,
        latency: float = None,
        # Alternative parameter names for backward compatibility
        endpoint: str = None,
        tokens_used: int = None,
        cost_estimate: float = None,
        success: bool = None
    ):
        """
        Track OpenAI API call metrics
        
        Supports two calling conventions:
        1. New: operation, status, latency
        2. Legacy: endpoint, tokens_used, cost_estimate, success
        """
        # Handle backward compatibility
        op = operation or endpoint or "unknown"
        stat = status or ("success" if success else "failure" if success is not None else "unknown")
        lat = latency or 0.0
        
        self.openai_api_calls.labels(operation=op, status=stat).inc()
        
        if lat > 0:
            self.openai_api_latency.labels(operation=op).observe(lat)
        
        if tokens_used and tokens_used > 0:
            self.openai_tokens_used.labels(operation=op).inc(tokens_used)
        
        if cost_estimate and cost_estimate > 0:
            self.openai_cost_estimate.labels(operation=op).inc(cost_estimate)
        
        _get_logger().debug(f"[Prometheus] Tracked OpenAI API call: operation={op}, status={stat}")
    
    def track_model_error(self, model_name: str, error_type: str):
        """Track model prediction errors"""
        self.model_prediction_errors.labels(model_name=model_name, error_type=error_type).inc()
        _get_logger().debug(f"[Prometheus] Tracked model error: model={model_name}, error_type={error_type}")
    
    def track_image_upload(self, size_bytes: int):
        """Track image upload metrics"""
        self.image_upload_size.observe(size_bytes)
    
    def track_image_processing_error(self, error_type: str):
        """Track image processing errors"""
        self.image_processing_errors.labels(error_type=error_type).inc()
    
    def track_user_activity(self, action: str, status: Optional[str] = None):
        """Track user activity metrics"""
        if action == "registration":
            self.user_registrations_total.inc()
        elif action == "login" and status:
            self.user_logins_total.labels(status=status).inc()
    
    def set_active_users(self, count: int):
        """Set the number of active users"""
        self.active_users.set(count)
    
    def track_database_operation(
        self,
        operation: str,
        collection: str,
        status: str,
        duration: float
    ):
        """Track database operation metrics"""
        self.database_operations_total.labels(
            operation=operation,
            collection=collection,
            status=status
        ).inc()
        self.database_operation_duration.labels(
            operation=operation,
            collection=collection
        ).observe(duration)
    
    def set_system_health(self, is_healthy: bool):
        """Set system health status"""
        self.system_health.set(1 if is_healthy else 0)
    
    def set_system_info(self, info: Dict[str, str]):
        """Set system information"""
        self.system_info.info(info)
    
    def set_data_drift_score(self, feature: str, score: float):
        """Set data drift score for a feature"""
        self.data_drift_score.labels(feature=feature).set(score)
    
    def set_model_performance_score(self, model_name: str, metric: str, score: float):
        """Set model performance score"""
        self.model_performance_score.labels(model_name=model_name, metric=metric).set(score)
    
    def track_drift_event(self, model_name: str, drift_type: str, severity: str):
        """Track drift event"""
        self.drift_events_total.labels(
            model_name=model_name,
            drift_type=drift_type,
            severity=severity
        ).inc()
    
    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus format"""
        return generate_latest(REGISTRY)


def track_execution_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to track function execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                _get_logger().debug(f"{func.__name__} took {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                _get_logger().error(f"{func.__name__} failed after {duration:.2f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                _get_logger().debug(f"{func.__name__} took {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                _get_logger().error(f"{func.__name__} failed after {duration:.2f}s: {e}")
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global metrics instance
prometheus_metrics = PrometheusMetrics()