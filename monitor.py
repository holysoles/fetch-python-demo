import yaml
import requests
import time
from collections import defaultdict
import threading

# Function to load configuration from the YAML file
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Function to perform health checks
def check_health(endpoint):
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
    except requests.RequestException:
        return "DOWN"

def check_health_loop(config: dict, domain_stats: defaultdict):
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
def monitor_endpoints(file_path):
    config = load_config(file_path)
    domain_stats = defaultdict(lambda: {"up": 0, "total": 0})

    check_health_thread = threading.Thread(target=check_health_loop, args=(config, domain_stats))
    check_health_thread.start()

    while True:
        time.sleep(15)
        # Log cumulative availability percentages
        for domain, stats in domain_stats.items():
            availability = round(100 * stats["up"] / stats["total"])
            print(f"{domain} has {availability}% availability percentage")

        print("---")

# Entry point of the program
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")