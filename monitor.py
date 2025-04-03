import yaml
import requests
import time
from collections import defaultdict
import threading
import os
import logging

class ConfigException(Exception):
    pass

# Function to load configuration from the YAML file
def load_config(file_path: str) -> list[dict]:
    config = []
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)

    # perform config validation
    if not isinstance(config, list):
        raise ConfigException("invalid config: provided yaml file is not an array")
    for endpoint in config:
        try:
            _ = endpoint['name']
        except KeyError as e:
            raise ConfigException("invalid config: an endpoint does not have required 'name' key") from e
        try:
            _ = endpoint['url']
        except KeyError as e:
            raise ConfigException(f"invalid config: endpoint name '{endpoint['name']}' does not have required 'url' key") from e 

    return config

# Function to perform health checks
def check_health(endpoint: dict) -> str:
    url = endpoint['url']
    method = endpoint.get('method', "GET")
    headers = endpoint.get('headers')
    body = endpoint.get('body')

    try:
        response = requests.request(method, url, headers=headers, json=body, timeout=0.5)
        if 200 <= response.status_code < 300:
            return "UP"
        else:
            return "DOWN"
    except requests.exceptions.ReadTimeout:
        logging.debug(f"timeout during availability check to '{url}'")
        return 'DOWN'
    except requests.RequestException as e:
        logging.debug(f"error requesting url '{url}'", exc_info=True)
        return "DOWN"

def check_health_loop(config: dict, domain_stats: defaultdict) -> None:
    while True:
        for endpoint in config:
            domain_with_port = endpoint["url"].split("//")[-1].split("/")[0]
            domain = domain_with_port.split(":")[0]
            result = check_health(endpoint)

            domain_stats[domain]["total"] += 1
            if result == "UP":
                domain_stats[domain]["up"] += 1
        time.sleep(15)

# Main function to monitor endpoints
def monitor_endpoints(file_path: str) -> None:
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    check_health_thread = threading.Thread(target=check_health_loop, args=(config, domain_stats))
    check_health_thread.start()

    while True:
        time.sleep(15)
        # Log cumulative availability percentages
        for domain, stats in domain_stats.items():
            availability = round(100 * stats["up"] / stats["total"])
            logging.info(f"{domain} has {availability}% availability percentage")

def get_logging_conf() -> dict:
    log_config = {}
    log_config["level"] = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_config["format"] = (
        "[%(asctime)s] %(levelname)s [%(filename)-s%(funcName)s():%(lineno)s]: %(message)s"
    )
    log_config["handlers"] = [logging.StreamHandler(sys.stdout)]
    log_file = os.environ.get("LOG_FILE", "")
    if log_file:
        log_config["handlers"].append(logging.FileHandler(log_file))
    return log_config

# Entry point of the program
if __name__ == "__main__":
    import sys

    log_config = get_logging_conf()
    logging.basicConfig(**log_config)

    if len(sys.argv) != 2:
        logging.error("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        logging.warning("\nMonitoring stopped by user.")
        sys.exit(0)
    except ConfigException as e:
        logging.critical(f"unable to parse provided configuration. {e}")
        sys.exit(1)
    except Exception as e:
        # generic catch to ensure we always log before the script exits
        logging.exception("unhandled exception while monitoring endpoints")
        sys.exit(1)