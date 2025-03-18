# CephFS Top Exporter

This project is a **CephFS Top Exporter** that collects performance metrics from the Ceph file system and exposes them to Prometheus for monitoring. The exporter interacts with the `cephfs-top` utility, parses its output, and converts relevant data into Prometheus metrics. 

## Features
- Enable CephFS stats https://docs.ceph.com/en/reef/cephfs/cephfs-top/
- Collects real-time CephFS performance metrics.
- Exposes the metrics through an HTTP server on a configurable port (default: `8000`).
- Supports JSON-based data input for testing or export purposes.

## Prerequisites

Before using the exporter, ensure the following dependencies are installed:


- Python 3.x
- Prometheus Python Client
- CEPH libraries and `cephfs-top` installed on the system.

## Installation in a client host

### 1. Install Dependencies on CentOS Stream 9 and CEPH squid release
  
   ```bash
   dnf config-manager --set-enabled crb
   dnf -y install centos-release-ceph-squid.noarch epel-release
   dnf -y install python3 python3-pip cephfs-top     
   pip3 install --no-cache-dir prometheus_client ConfigArgParse

### 2. Install the python script

   ```bash
   mkdir -p /opt/cephfs-top-exporter/
   cd /opt/cephfs-top-exporter/
   curl https://raw.githubusercontent.com/josgutie/cephfs-top-exporter/refs/heads/main/src/cephfs-top-exporter.py
   chmod u+x cephfs-top-exporter.py

### 3. Configure the CephFS top utility

#### Follow the instructions stated in the following link [CephFS Top Utility](https://docs.ceph.com/en/reef/cephfs/cephfs-top/)

### 4. Configure a systemd daemon to run the cephfs-top-exporter
   ```bash   
    cat /etc/systemd/system/cephfs_top_exporter.service
    [Unit]
    Description=CephFS Top Prometheus Exporter
    After=network.target
    
    [Service]
    ExecStart=/usr/bin/python3 /opt/cephfs-top-exporter/cephfs-top-exporter.py
    WorkingDirectory=/opt/cephfs-top-exporter        
    Restart=always    
    [Install]
    WantedBy=multi-user.target

### 5. Add a Prometheus scraper job
   ```bash   
    grep -A7 cephfs-top-exporter /etc/prometheus/prometheus.yml
    - job_name: 'cephfs-top-exporter'
      static_configs:
      - targets:
        - '{server_ip}:{port, default=8000}'
      labels:
        cluster: '{id_cluster}'
    honor_labels: true    

## Running as a container
### 1. Clone the repository project and build the image
   ```bash
   git clone https://github.com/josgutie/cephfs-top-exporter.git
   podman build . -t cephfs-top-exporter:v1.0

### 2. Copy the configuration files needed by the cephfs-top client 
   - The files needed are:
     - ceph.conf
     - ceph.client.fstop.keyring
   - For more details review the following link [CephFS Top Utility](https://docs.ceph.com/en/reef/cephfs/cephfs-top/)

### 3. Run the image
   ```bash
   podman run -d --name cephfs-top-exporter -p 8000:8000 -v ./ceph.conf:/etc/ceph/ceph.conf:Z -v /etc/ceph/ceph.client.fstop.keyring:/etc/ceph/ceph.client.fstop.keyring:Z localhost/cephfs-top-exporter:v1.0   
#### Check that is exporting data
   curl http://localhost:8000 | grep cephfs_top

## TODO

- Deploy in kubernetes to provide CephFS client/host performance metrics in external CEPH deployments.