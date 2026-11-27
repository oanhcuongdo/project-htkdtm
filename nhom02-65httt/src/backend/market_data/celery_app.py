import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("smart_pricing_market_data", broker=REDIS_URL, backend=REDIS_URL,
                    include=["market_data.tasks"])
celery_app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="Asia/Ho_Chi_Minh", enable_utc=True,
    beat_schedule={
        "validate-competitor-dataset-daily": {
            "task": "market_data.tasks.validate_dataset_task", "schedule": 86400.0,
        },
        "normalize-competitor-snapshot-daily": {
            "task": "market_data.tasks.normalize_snapshot_task", "schedule": 86400.0,
        },
    },
)
