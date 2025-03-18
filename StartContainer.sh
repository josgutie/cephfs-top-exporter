podman run -p 8000:8000 -v /home/josgutie/Development/cephfs-top-exporter/ceph.conf:/etc/ceph/ceph.conf:Z -v /home/josgutie/Development/cephfs-top-exporter/ceph.client.fstop.keyring:/etc/ceph/ceph.client.fstop.keyring:Z -v /home/josgutie/Development/cephfs-top-exporter/cephfstop_20250127_ieec2ocs1n001.json:/tmp/cephfstop_20250127_ieec2ocs1n001.json:Z -e CEPHFS_TOP_JSONDUMP=/tmp/cephfstop_20250127_ieec2ocs1n001.json -e CEPHFS_TOP_EXPORTER_TRACE_LEVEL=INFO localhost/cephfs-top-exporter:1.0


podman run -it -p 8000:8000 -v /home/josgutie/Development/cephfs-top-exporter/ceph.conf:/etc/ceph/ceph.conf:Z -v /home/josgutie/Development/cephfs-top-exporter/ceph.client.fstop.keyring:/etc/ceph/ceph.client.fstop.keyring:Z -e CEPHFS_TOP_EXPORTER_TRACE_LEVEL=DEBUG localhost/cephfs-top-exporter:1.0



podman run --name cephfs-top-exporter -p 8000:8000 -v /etc/ceph/ceph.conf:/etc/ceph/ceph.conf:Z -v /etc/ceph/ceph.client.fstop.keyring:/etc/ceph/ceph.client.fstop.keyring:Z -v /root/cephfstop_20250127_ieec2ocs1n001.json:/root/cephfstop_20250127_ieec2ocs1n001.json:Z -e CEPHFS_TOP_EXPORTER_TRACE_LEVEL=INFO -e CEPHFS_TOP_JSONDUMP=/root/cephfstop_20250127_ieec2ocs1n001.json localhost/cephfs-top-exporter:v1.0
