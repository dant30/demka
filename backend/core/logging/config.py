"""Reusable LOGGING dict; import into Django settings."""
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} | {levelname:8} | {name} | cid={correlation_id} | {message}",
            "style": "{",
        },
    },
    "filters": {"correlation_id": {"()": "core.logging.correlation.CorrelationIdFilter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["correlation_id"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps":   {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "core":   {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}