# pylint: disable=missing-module-docstring
import sys
import time
from collections import defaultdict
import threading
import os
import logging
import yaml
import requests


class ConfigException(Exception):
    """
    An exception class that categorizes issues encountered when parsing or validating
    provided configuration
    """


def load_config(file_path: str) -> list[dict]:
    """
    Function to load configuration from the YAML file
    """
    logging.debug("loading configuration")
    config = []
    with open(file_path, "r", encoding="utf8") as file:
        config = yaml.safe_load(file)
    logging.debug("configuration loaded. validating config")

    # perform config validation
    if not isinstance(config, list):
        raise ConfigException("invalid config: provided yaml file is not an array")
    for endpoint in config:
        try:
            _ = endpoint["name"]
        except KeyError as e:
            raise ConfigException(
                "invalid config: an endpoint does not have required 'name' key"
            ) from e
        try:
            _ = endpoint["url"]
        except KeyError as e:
            raise ConfigException(
                f"invalid config: endpoint '{endpoint['name']}' does not have required 'url' key"
            ) from e
    logging.debug("configuration successfully validated")

    return config


def check_health(endpoint: dict) -> str:
    """
    Function to perform health checks
    """
    url = endpoint["url"]
    method = endpoint.get("method", "GET")
    headers = endpoint.get("headers")
    body = endpoint.get("body")

    logging.debug('checking availability of %s', endpoint)
    try:
        response = requests.request(
            method, url, headers=headers, json=body, timeout=0.5
        )
        if 200 <= response.status_code < 300:
            logging.debug('%s tested as UP', endpoint)
            return "UP"
        return "DOWN"
    except requests.exceptions.ReadTimeout:
        logging.debug("timeout during availability check to %s", url)
        return "DOWN"
    except requests.RequestException:
        logging.debug("error requesting url '%s'", url, exc_info=True)
        return "DOWN"


def check_health_loop(config: dict, domain_stats: defaultdict) -> None:
    """
    A loop for performing health checks against the provided configuration
    """
    while True:
        for endpoint in config:
            domain_with_port = endpoint["url"].split("//")[-1].split("/")[0]
            domain = domain_with_port.split(":")[0]
            result = check_health(endpoint)

            domain_stats[domain]["total"] += 1
            if result == "UP":
                domain_stats[domain]["up"] += 1
        time.sleep(15)


def monitor_endpoints(file_path: str) -> None:
    """
    Main function to monitor endpoints
    """
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    logging.info("configuration loaded, beginning endpoint monitoring")
    check_health_thread = threading.Thread(
        target=check_health_loop,
        args=(config, domain_stats),
        daemon=True,
    )
    check_health_thread.start()

    while True:
        time.sleep(15)
        # Log cumulative availability percentages
        for domain, stats in domain_stats.items():
            availability = round(100 * stats["up"] / stats["total"])
            logging.info("%s has %s%% availability percentage", domain, availability)


def get_logging_conf() -> dict:
    """
    Generates a logging configuration dict for the tool
    """
    log_conf = {}
    log_conf["level"] = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_conf["format"] = (
        "[%(asctime)s] %(levelname)s [%(filename)-s%(funcName)s():%(lineno)s]: %(message)s"
    )
    log_conf["handlers"] = [logging.StreamHandler(sys.stdout)]
    log_file = os.environ.get("LOG_FILE", "")
    if log_file:
        log_conf["handlers"].append(logging.FileHandler(log_file))
    return log_conf


# Entry point of the program
if __name__ == "__main__":
    log_config = get_logging_conf()
    logging.basicConfig(**log_config)

    if len(sys.argv) != 2:
        logging.error("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        logging.warning("Monitoring stopped by user.")
        sys.exit(0)
    except ConfigException as e:
        logging.critical("unable to parse provided configuration. %s", e)
        sys.exit(1)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        # generic catch to ensure we always log before the script exits
        logging.exception("unhandled exception while monitoring endpoints")
        sys.exit(1)
    # pylint: enable=broad-exception-caught
