Step 1: Install InfluxDB version 1.8

```bash
# Add the InfluxData repository
wget https://dl.influxdata.com/influxdb/releases/influxdb_1.8.10_amd64.deb

sudo dpkg -i influxdb_1.8.10_amd64.deb

sudo apt-get install -f

influxd version

# Start InfluxDB service
sudo systemctl start influxdb
sudo systemctl enable influxdb
```

Step 2: Set up sample data in InfluxDB

```bash
# Download sample data
wget https://s3.amazonaws.com/noaa.water-database/NOAA_data.txt

# Import data into InfluxDB
influx -import -path=NOAA_data.txt -precision=s -database=NOAA_water_database
```

Verify the data import by querying the database:
```bash
influx
```
Then, in the InfluxDB shell:
```bash
USE NOAA_water_database
SHOW MEASUREMENTS
SELECT * FROM h2o_feet LIMIT 5
```

Step 3: Install grafana

Install Grafana on your Ubuntu EC2 instance:
```
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
```

Start and enable Grafana service:
```
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

Access Grafana web interface by navigating to `http://localhost:3000` in your web browser.

Add InfluxDB as a data source:

- Click on the gear icon (⚙️) in the sidebar to open the Configuration menu.
- Select "Data Sources".
- Click "Add data source".
- Choose "InfluxDB".
- Set the following:
  - Name: NOAA InfluxDB (or any name you prefer)
  - URL: `http://localhost:8086` (assuming InfluxDB is on the same machine)
  - Database: NOAA_water_database
  - User & Password (if you set up authentication for InfluxDB)
- Click "Save & Test" to ensure the connection works.

Create a new dashboard:

- Click the "+" icon in the sidebar and select "Dashboard".
- Click "Add new panel".

Configure the panel:

- In the Query section, select your InfluxDB data source.
- Use the query builder or switch to text mode and enter a query, e.g.:
  ```
  SELECT "water_level" FROM "h2o_feet" WHERE $timeFilter LIMIT 1000
  ```
- Adjust the panel settings, title, and visualization type as desired.
- Click "Apply" to add the panel to your dashboard.

Save your dashboard by clicking the apply icon at the top of the screen.


Step 4: Install Prometheus

Update System Packages
```
sudo apt update
```

Create a System User for Prometheus
```
sudo groupadd --system prometheus
sudo useradd -s /sbin/nologin --system -g prometheus prometheus
```

Create Directories for Prometheus
```bash
sudo mkdir /etc/prometheus
sudo mkdir /var/lib/prometheus
```

Download Prometheus and Extract Files
```
wget https://github.com/prometheus/prometheus/releases/download/v2.43.0/prometheus-2.43.0.linux-amd64.tar.gz
tar vxf prometheus*.tar.gz
```

Navigate to the Prometheus Directory
```bash
cd prometheus*/
```

Move the Binary Files & Set Owner
```bash
sudo mv prometheus /usr/local/bin
sudo mv promtool /usr/local/bin
sudo chown prometheus:prometheus /usr/local/bin/prometheus
sudo chown prometheus:prometheus /usr/local/bin/promtool
```

Move the Configuration Files & Set Owner
```bash
sudo mv consoles /etc/prometheus
sudo mv console_libraries /etc/prometheus
sudo mv prometheus.yml /etc/prometheus
sudo chown prometheus:prometheus /etc/prometheus
sudo chown -R prometheus:prometheus /etc/prometheus/consoles
sudo chown -R prometheus:prometheus /etc/prometheus/console_libraries
sudo chown -R prometheus:prometheus /var/lib/prometheus
```

The prometheus.yml file is the main Prometheus configuration file.
```bash
sudo nano /etc/prometheus/prometheus.yml
```

Create Prometheus Systemd Service
```bash
sudo nano /etc/systemd/system/prometheus.service
```

```bash
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --enable-feature=remote-write-receiver

[Install]
WantedBy=multi-user.target
```

Reload Systemd
```bash
sudo systemctl daemon-reload
```
Start Prometheus

```bash
sudo systemctl daemon-reload
sudo systemctl start prometheus
sudo systemctl enable prometheus
```

Access Prometheus Web Interface
```
sudo ufw allow 9090/tcp
```
With Prometheus running successfully, you can access it via your web browser using localhost:9090


Step 7: Install and configure in influxql-to-promql-converter

clone the repository :
```bash
git clone https://github.com/logzio/influxql-to-promql-converter
cd influxql-to-promql-converter
```

Install the required dependencies if you haven't already:
```
pip install -r requirements.txt
```

Use the `influx_inspect` tool to export data from InfluxDB in line protocol format. The command will look like this:
```
influx_inspect export -datadir /var/lib/influxdb/data -waldir /var/lib/influxdb/wal -database NOAA_water_database -measurement h2o_feet -out influx_data.lp
```
