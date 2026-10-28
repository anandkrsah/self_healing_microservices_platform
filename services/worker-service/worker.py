import logging
import random
import time

from prometheus_client import Counter, Gauge, Histogram, start_http_server


# Configure application logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


# Count completed jobs by their result and job type.
JOBS_PROCESSED = Counter(
    "worker_jobs_total",
    "Total number of jobs processed",
    ["status", "type"],
)

# Measure how long each job takes.
JOB_DURATION = Histogram(
    "worker_job_duration_seconds",
    "Time spent processing jobs",
)

# Track the simulated number of jobs waiting to be processed.
QUEUE_SIZE = Gauge(
    "worker_queue_size",
    "Number of jobs waiting in the simulated queue",
)


JOB_TYPES = [
    "email",
    "image_resize",
    "report",
    "data_sync",
]


def process_job(job_id):
    """Simulate processing a single background job."""

    job_type = random.choice(JOB_TYPES)
    processing_time = random.uniform(0.1, 2.0)

    # Simulate an occasional job failure.
    failed = random.random() < 0.05

    logger.info(
        "Starting job_id=%s type=%s",
        job_id,
        job_type,
    )

    start_time = time.perf_counter()

    # Simulate work being performed.
    time.sleep(processing_time)

    elapsed_time = time.perf_counter() - start_time

    JOB_DURATION.observe(elapsed_time)

    if failed:
        JOBS_PROCESSED.labels(
            status="failed",
            type=job_type,
        ).inc()

        logger.error(
            "Job failed job_id=%s type=%s duration=%.2fs",
            job_id,
            job_type,
            elapsed_time,
        )

        return

    JOBS_PROCESSED.labels(
        status="success",
        type=job_type,
    ).inc()

    logger.info(
        "Job completed job_id=%s type=%s duration=%.2fs",
        job_id,
        job_type,
        elapsed_time,
    )


def main():
    """Start the metrics server and worker loop."""

    start_http_server(5002)

    logger.info("Worker started; Prometheus metrics available on port 5002")

    job_id = 1

    while True:
        # This is simulated queue activity, not a real message queue.
        QUEUE_SIZE.set(random.randint(0, 20))

        process_job(job_id)

        job_id += 1

        # Pause before starting the next simulated job.
        time.sleep(10)


if __name__ == "__main__":
    main()