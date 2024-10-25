import logging
from typing import List, Dict, Any

class FileImporter:
    def __init__(self, params: dict, log_level=logging.INFO):
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)
        self._path = params['path']

    def fetch_dashboards(self) -> List[Dict[str, Any]]:
        try:
            with open(self._path, 'r') as f:
                lines = f.readlines()

            data = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parsed_line = self.parse_line_protocol(line)
                    if parsed_line:
                        data.append(parsed_line)

            return [{"raw_data": data}]
        except Exception as e:
            self._logger.error(f"Failed to read file: {self._path}, error: {str(e)}")
            return []

    def parse_line_protocol(self, line: str) -> Dict[str, Any]:
        try:
            if line.startswith('CREATE DATABASE'):
                return None  # Skip CREATE DATABASE lines

            measurement_and_tags, fields_and_timestamp = line.split(' ', 1)

            measurement_parts = measurement_and_tags.split(',')
            measurement = measurement_parts[0]
            tags = {}
            for part in measurement_parts[1:]:
                key, value = part.split('=')
                tags[key] = value

            fields_and_timestamp_parts = fields_and_timestamp.rsplit(' ', 1)
            fields = {}
            for field in fields_and_timestamp_parts[0].split(','):
                key, value = field.split('=', 1)
                if value.startswith('"') and value.endswith('"'):
                    fields[key] = value.strip('"')
                elif '.' in value:
                    fields[key] = float(value)
                else:
                    fields[key] = int(value)

            timestamp = int(fields_and_timestamp_parts[1])

            return {
                "measurement": measurement,
                "tags": tags,
                "fields": fields,
                "timestamp": timestamp
            }
        except Exception as e:
            self._logger.warning(f"Failed to parse line: {line}. Error: {str(e)}")
            return None
