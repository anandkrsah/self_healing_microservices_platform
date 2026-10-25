import logging
import os
import time

from flask import Flask, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency in seconds",
    ["endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "api_active_requests",
    "Number of API requests currently being processed",
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "api-service",
        "version": os.getenv("IMAGE_TAG", "local"),
    }), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }


@app.route("/api/data", methods=["GET"])
def get_data():
    start = time.time()
    ACTIVE_REQUESTS.inc()

    try:
        logger.info("GET /api/data called")

        REQUEST_COUNT.labels(
            method="GET",
            endpoint="/api/data",
            status="200",
        ).inc()

        REQUEST_LATENCY.labels(
            endpoint="/api/data"
        ).observe(time.time() - start)

        return jsonify({
            "message": "Hello from API service",
            "timestamp": time.time(),
        }), 200

    finally:
        ACTIVE_REQUESTS.dec()


@app.route("/api/items", methods=["GET"])
def get_items():
    items = [
        {"id": 1, "name": "Docker Container", "category": "infra"},
        {"id": 2, "name": "Ansible Role", "category": "automation"},
        {"id": 3, "name": "Grafana Panel", "category": "monitoring"},
        {"id": 4, "name": "GitHub Action", "category": "ci-cd"},
    ]

    REQUEST_COUNT.labels(
        method="GET",
        endpoint="/api/items",
        status="200",
    ).inc()

    return jsonify({
        "items": items,
        "count": len(items),
    }), 200


@app.route("/api/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "A valid JSON body is required"}), 400

    REQUEST_COUNT.labels(
        method="POST",
        endpoint="/api/echo",
        status="200",
    ).inc()

    return jsonify({"echo": data}), 200


@app.route("/api/error-test", methods=["GET"])
def error_test():
    REQUEST_COUNT.labels(
        method="GET",
        endpoint="/api/error-test",
        status="500",
    ).inc()

    logger.error("Intentional test error triggered")

    return jsonify({"error": "test error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)