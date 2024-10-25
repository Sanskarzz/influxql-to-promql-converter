import logging
import time
import yaml
import requests
import snappy
import struct
from typing import Dict, Any
from prometheus_client import CollectorRegistry, Gauge

# Import your FileImporter
from importer.file_importer import FileImporter

logger = logging.getLogger(__name__)

def format_for_prometheus(data_list):
    registry = CollectorRegistry()
    metrics = {}

    for data in data_list:
        measurement = data['measurement']
        for field, value in data['fields'].items():
            if isinstance(value, (int, float)):
                metric_name = f"{measurement}_{field}"
                if metric_name not in metrics:
                    metrics[metric_name] = Gauge(
                        metric_name,
                        'Imported from InfluxDB',
                        labelnames=list(data['tags'].keys()),
                        registry=registry
                    )

                metrics[metric_name].labels(**data['tags']).set(value)

    return registry

def encode_varint(value):
    """Encode an integer as a varint."""
    encoded = []
    while value > 0x7f:
        encoded.append((value & 0x7f) | 0x80)
        value >>= 7
    encoded.append(value & 0x7f)
    return bytes(encoded)

def encode_string(field_number, value):
    encoded = encode_varint(field_number << 3 | 2)  # wire type 2 (length-delimited)
    encoded += encode_varint(len(value))
    encoded += value.encode('utf-8')
    return encoded

def create_write_request(registry):
    timeseries_list = []
    current_time = int(time.time() * 1000)  # Use the same timestamp for all samples

    for metric in registry.collect():
        for sample in metric.samples:
            ts_data = b""

            # Add labels
            for k, v in sample.labels.items():
                ts_data += encode_string(1, k)
                ts_data += encode_string(2, v)

            # Add metric name as a label
            ts_data += encode_string(1, "__name__")
            ts_data += encode_string(2, sample.name)

            # Add sample
            ts_data += encode_varint(3 << 3 | 1)  # field 3, wire type 1 (64-bit)
            ts_data += struct.pack('<d', sample.value)
            ts_data += encode_varint(4 << 3 | 1)  # field 4, wire type 1 (64-bit)
            ts_data += struct.pack('<q', current_time)

            timeseries_list.append(ts_data)

    # Encode the write request
    data = b""
    for ts_data in timeseries_list:
        data += encode_varint(1 << 3 | 2)  # field 1, wire type 2 (length-delimited)
        data += encode_varint(len(ts_data))
        data += ts_data

    return data

def send_to_prometheus(registry, endpoint):
    try:
        data = create_write_request(registry)
        compressed_data = snappy.compress(data)

        # Print a sample of the compressed data (first 100 bytes)
        print("Sample of compressed data:", compressed_data[:100])

        headers = {
            'Content-Type': 'application/x-protobuf',
            'Content-Encoding': 'snappy',
            'X-Prometheus-Remote-Write-Version': '0.1.0'
        }
        response = requests.post(endpoint, data=compressed_data, headers=headers)

        if response.status_code == 200:
            logger.info("Data sent successfully to Prometheus")
        else:
            logger.error(f"Error sending data to Prometheus: HTTP {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"Error sending data to Prometheus: {str(e)}")

def run():
    logging.basicConfig(level=logging.INFO)

    with open("config.yaml", 'r') as stream:
        config = yaml.safe_load(stream)

    file_importer = FileImporter(config['importer']['file'])
    data_list = file_importer.fetch_dashboards()[0]['raw_data']

    logger.info(f"Imported {len(data_list)} data points")

    if data_list:
        registry = format_for_prometheus(data_list)

        prometheus_endpoint = config['exporter'].get('prometheus', {}).get('endpoint')
        if prometheus_endpoint:
            send_to_prometheus(registry, prometheus_endpoint)
        else:
            logger.warning("Prometheus endpoint not specified in config. Skipping data export.")
    else:
        logger.warning("No data imported. Skipping data export.")

    logger.info(f"Finished running in --- {time.time() - start_time} seconds ---")

if __name__ == '__main__':
    start_time = time.time()
    run()
