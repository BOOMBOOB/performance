from prometheus_client import start_http_server
from bin.service_start import workflow
import time


if __name__ == '__main__':
    start_http_server(9091)
    workflow()

    i = 1
    while i < 300:
        i += 1
        time.sleep(1)
