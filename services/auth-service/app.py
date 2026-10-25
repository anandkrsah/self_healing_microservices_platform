import logging
import os
import time

from flask import Flask, jsonify, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

AUTH_ATTEMPTS = Counter(
    "auth_attempts_total",
    "Total authentication attempts",
    ["result"],
)

AUTH_LATENCY = Histogram(
    "auth_latency_seconds",
    "Authentication request latency in seconds",
)

# Local demonstration credentials only.
# Do not use hardcoded tokens for production authentication.
VALID_TOKENS = {
    "user-dev-token": {
        "user": "dev-user",
        "role": "developer",
    },
    "ops-dev-token": {
        "user": "ops-user",
        "role": "operator",
    },
    "admin-dev-token": {
        "user": "admin-user",
        "role": "admin",
    },
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "auth-service",
        "version": os.getenv("IMAGE_TAG", "local"),
    }), 200


@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST,
    }


@app.route("/auth/validate", methods=["POST"])
def validate():
    start = time.perf_counter()

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        AUTH_ATTEMPTS.labels(result="invalid_request").inc()
        return jsonify({
            "valid": False,
            "error": "A valid JSON object is required",
        }), 400

    token = data.get("token")

    if not isinstance(token, str) or not token:
        AUTH_ATTEMPTS.labels(result="invalid_request").inc()
        return jsonify({
            "valid": False,
            "error": "A token is required",
        }), 400

    user_info = VALID_TOKENS.get(token)

    AUTH_LATENCY.observe(time.perf_counter() - start)

    if user_info is None:
        AUTH_ATTEMPTS.labels(result="failure").inc()
        logger.warning("Authentication attempt failed")

        return jsonify({
            "valid": False,
            "error": "Invalid token",
        }), 401

    AUTH_ATTEMPTS.labels(result="success").inc()
    logger.info("Authentication succeeded")

    return jsonify({
        "valid": True,
        "user": user_info["user"],
        "role": user_info["role"],
    }), 200


@app.route("/auth/ping", methods=["GET"])
def ping():
    return jsonify({
        "message": "Authentication service is alive",
        "timestamp": time.time(),
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)