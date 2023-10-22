import json
import os
import sys
from pathlib import Path

from loguru import logger as loguru_logger

from .config import settings


class Logger:
    def __init__(self):
        self.logger = loguru_logger
        self.logger.remove(0)
        self.patching()

    def serialize(self, record):
        pid = os.getpid()
        subset = {
            "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S"),
            "pid": record["process"].id,
            "message": record["message"],
            "level": record["level"].name,
            "file": record["file"].name,
            "context": record["extra"],
        }
        return json.dumps(subset)

    def patching(self):
        def patcher(record):
            record["extra"]["serialized"] = self.serialize(record)

        self.logger = self.logger.patch(patcher)

    def setup_logger(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Logs will always be saved in JSON format in the log file
        self.logger.add(
            f"{log_dir}/app.log",
            level="INFO",
            format="{extra[serialized]}",
        )
        error_log = f"{log_dir}/errors.log"
        self.logger.add(error_log, level="ERROR", format="{extra[serialized]}")

        # Adjust console log format based on the mode
        if settings.DEBUG == "True":
            self.logger.add(
                sys.stderr,
                format="<green>[MIRO API] {process}</green> - {time:DD/MM/YYYY, HH:mm:ss A} - <level>{level}</level> "
                "- <cyan>[{extra[context]}]</cyan> {message}",
            )
        else:
            self.logger.add(sys.stderr, format="{extra[serialized]}")

    def configure(self):
        self.setup_logger()

    def get_context_logger(self, context):
        return self.logger.bind(context=context)


logger = Logger()
logger.configure()
