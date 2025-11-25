"""
MLOps System Initialization and Demo Script

This script initializes baselines and generates sample data for demonstration.
Run this script to set up the MLOps system and verify everything is working.

Usage:
    python scripts/init__mlops.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.model_monitoring_service import model_monitor
from services.mlflow_service import mlflow_manager
from services.prometheus_service import prometheus_metrics
from utils.logger import get_logger

logger = get_logger(__name__)


async def initialize_baselines():
    """Initialize baseline statistics for all models"""
    logger.info("🚀 Initializing MLOps baselines...")
    
    # CLIP Ingredient Detector Baseline
    model_monitor.set_baseline("clip_ingredient_detector", {
        "confidence_mean": 0.65,
        "confidence_std": 0.15,
        "latency_mean": 1.8,
        "latency_std": 0.5,
        "prediction_distribution": {}
    })
    logger.info("✅ Set baseline for CLIP ingredient detector")
    
    # OpenAI Vision Ingredient Detector Baseline
    model_monitor.set_baseline("openai_vision", {
        "confidence_mean": 0.85,
        "confidence_std": 0.10,
        "latency_mean": 2.5,
        "latency_std": 0.8,
        "prediction_distribution": {}
    })
    logger.info("✅ Set baseline for OpenAI Vision ingredient detector")
    
    # OpenAI Recipe Generator Baseline
    model_monitor.set_baseline("openai_recipe_generator", {
        "confidence_mean": 0.85,
        "confidence_std": 0.10,
        "latency_mean": 3.0,
        "latency_std": 1.0,
        "prediction_distribution": {}
    })
    logger.info("✅ Set baseline for OpenAI recipe generator")
    
    # Ingredient Detection Pipeline Baseline
    model_monitor.set_baseline("ingredient_detection_pipeline", {
        "confidence_mean": 0.70,
        "confidence_std": 0.15,
        "latency_mean": 2.5,
        "latency_std": 0.8,
        "prediction_distribution": {}
    })
    logger.info("✅ Set baseline for ingredient detection pipeline")
    
    logger.info("🎉 All baselines initialized successfully!")


async def generate_sample_metrics():
    """Generate sample metrics for demonstration"""
    logger.info("📊 Generating sample metrics for demo...")
    
    import random
    
    # Simulate some ingredient detections
    for i in range(20):
        confidence = random.uniform(0.5, 0.9)
        latency = random.uniform(1.0, 3.0)
        num_ingredients = random.randint(2, 8)
        
        # Record in model monitor
        model_monitor.record_prediction(
            model_name="clip_ingredient_detector",
            prediction=f"sample_ingredients_{i}",
            confidence=confidence,
            latency=latency,
            input_features={"num_ingredients": num_ingredients}
        )
        
        # Track in Prometheus
        prometheus_metrics.track_ingredient_detection(
            model_name="clip_ingredient_detector",
            num_ingredients=num_ingredients,
            confidence_score=confidence,
            processing_time=latency,
            success=True
        )
        
        # Log to MLflow
        mlflow_manager.log_ingredient_detection(
            ingredients=[f"ingredient_{j}" for j in range(num_ingredients)],
            confidence_scores={f"ingredient_{j}": confidence for j in range(num_ingredients)},
            detection_method="local_clip",
            processing_time=latency,
            image_metadata={"size": 1024000, "format": "jpeg", "model": "clip-vit-base-patch32"}
        )
        
        await asyncio.sleep(0.1)
    
    logger.info("✅ Generated 20 ingredient detection samples")
    
    # Simulate some recipe generations
    for i in range(15):
        latency = random.uniform(2.0, 5.0)
        num_ingredients = random.randint(3, 10)
        complexity = random.choice(["easy", "medium", "hard"])
        
        # Record in model monitor
        model_monitor.record_prediction(
            model_name="openai_recipe_generator",
            prediction=f"Sample Recipe {i}",
            confidence=0.85,
            latency=latency,
            input_features={"num_ingredients": num_ingredients}
        )
        
        # Track in Prometheus
        prometheus_metrics.track_recipe_generation(
            model="openai",
            status="success",
            duration=latency,
            complexity=complexity
        )
        
        # Log to MLflow
        mlflow_manager.log_recipe_generation(
            recipe_title=f"Sample Recipe {i}",
            ingredients_used=[f"ing_{j}" for j in range(num_ingredients)],
            generation_model="openai_gpt",
            generation_time=latency,
            recipe_complexity=complexity
        )
        
        await asyncio.sleep(0.1)
    
    logger.info("✅ Generated 15 recipe generation samples")
    
    logger.info("🎉 Sample metrics generated successfully!")


async def check_drift():
    """Check for drift in models"""
    logger.info("🔍 Checking for drift...")
    
    models = [
        "clip_ingredient_detector",
        "openai_recipe_generator",
        "ingredient_detection_pipeline"
    ]
    
    for model in models:
        confidence_drift = model_monitor.detect_drift(model, "confidence")
        latency_drift = model_monitor.detect_drift(model, "latency")
        
        logger.info(f"\n📊 {model}:")
        logger.info(f"   Confidence drift: {confidence_drift.get('drift_detected', False)}")
        if confidence_drift.get('drift_detected'):
            logger.info(f"   Drift score: {confidence_drift['drift_score']:.4f}")
        
        logger.info(f"   Latency drift: {latency_drift.get('drift_detected', False)}")
        if latency_drift.get('drift_detected'):
            logger.info(f"   Drift score: {latency_drift['drift_score']:.4f}")
    
    logger.info("\n✅ Drift check complete!")


async def generate_performance_report():
    """Generate comprehensive performance report"""
    logger.info("📈 Generating performance report...")
    
    models = [
        "clip_ingredient_detector",
        "openai_recipe_generator",
        "ingredient_detection_pipeline"
    ]
    
    report = model_monitor.generate_monitoring_report(models)
    
    logger.info("\n" + "="*60)
    logger.info("PERFORMANCE REPORT")
    logger.info("="*60)
    
    for model_name, model_data in report.get("models", {}).items():
        logger.info(f"\n📊 {model_name.upper()}")
        logger.info("-" * 60)
        
        perf = model_data.get("performance_summary", {})
        if "error" not in perf:
            logger.info(f"Total Predictions: {perf.get('total_predictions', 0)}")
            
            if "confidence" in perf:
                conf = perf["confidence"]
                logger.info(f"Confidence - Mean: {conf['mean']:.4f}, Std: {conf['std']:.4f}")
            
            if "latency" in perf:
                lat = perf["latency"]
                logger.info(f"Latency - Mean: {lat['mean']:.4f}s, P95: {lat['percentile_95']:.4f}s")
        else:
            logger.info(f"   {perf.get('error')}")
        
        drift_events = model_data.get("recent_drift_events", [])
        logger.info(f"Drift Events (24h): {len(drift_events)}")
    
    logger.info("\n" + "="*60)
    logger.info("✅ Report complete!")


async def verify_prometheus():
    """Verify Prometheus metrics are working"""
    logger.info("🔧 Verifying Prometheus metrics...")
    
    try:
        metrics = prometheus_metrics.get_metrics()
        metric_count = len(metrics.decode('utf-8').split('\n'))
        logger.info(f"✅ Prometheus metrics available ({metric_count} lines)")
    except Exception as e:
        logger.error(f"❌ Prometheus metrics error: {e}")


async def verify_mlflow():
    """Verify MLflow connection"""
    logger.info("🔧 Verifying MLflow connection...")
    
    try:
        summary = mlflow_manager.get_experiment_summary()
        if "error" not in summary:
            logger.info(f"✅ MLflow connected - Experiment: {summary.get('experiment_name')}")
            logger.info(f"   Total runs: {summary.get('total_runs', 0)}")
        else:
            logger.warning(f"⚠️  MLflow: {summary.get('error')}")
    except Exception as e:
        logger.error(f"❌ MLflow error: {e}")


async def main():
    """Main initialization and demo function"""
    logger.info("🎯 Starting FlavourCraft MLOps Initialization")
    logger.info("="*70)
    
    try:
        # Step 0: Verify services
        await verify_prometheus()
        await verify_mlflow()
        logger.info("\n")
        
        # Step 1: Initialize baselines
        await initialize_baselines()
        logger.info("\n")
        
        # Step 2: Generate sample metrics
        await generate_sample_metrics()
        logger.info("\n")
        
        # Step 3: Check for drift
        await check_drift()
        logger.info("\n")
        
        # Step 4: Generate performance report
        await generate_performance_report()
        
        logger.info("\n" + "="*70)
        logger.info("🎉 MLOps initialization complete!")
        logger.info("\n📊 You can now:")
        logger.info("   1. View MLflow experiments: http://localhost:5001")
        logger.info("   2. Check Prometheus metrics: http://localhost:8000/mlops/metrics")
        logger.info("   3. Access API dashboards: http://localhost:8000/docs")
        logger.info("   4. Check MLOps health: http://localhost:8000/mlops/health")
        logger.info("="*70)
        
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())