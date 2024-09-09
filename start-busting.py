#!/usr/bin/env python3
import json
import logging
import sys
from typing import cast

import requests
from rich.console import Console
from rich.logging import RichHandler

loggingConsole = Console(stderr=True)
loggingHandler = RichHandler(console=loggingConsole)
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[loggingHandler]
)
log = logging.getLogger("rich")


if __name__ == "__main__":
    log.info("Get entries from JSONPlaceholder")
    try:
        limit = int(sys.argv[-1])
    except:
        limit = 1
        log.info(
            "No iteration limit specified on command line (the last positional argument), using the default: running only once"
        )
    for loop in range(0, limit):
        resp = requests.get("https://jsonplaceholder.typicode.com/photos")
        prefix = f"Processing iteration {loop}..."
        with loggingConsole.status(prefix) as status:
            for entry in resp.json():
                status.update(status=f"{prefix} ID: {entry['id']}")
                log.info(entry)
