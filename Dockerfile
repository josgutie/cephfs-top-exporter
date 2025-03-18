FROM quay.io/centos/centos:stream9


# Instalar dependencias del sistema
RUN  dnf config-manager --set-enabled crb \
    && dnf -y install centos-release-ceph-squid.noarch epel-release  \ 
    && dnf -y install python3 python3-pip cephfs-top \
    && dnf clean all

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir prometheus_client ConfigArgParse

RUN mkdir -p /opt/cephfs-top-exporter
WORKDIR /opt/cephfs-top-exporter
COPY src/cephfs-top-exporter.py /opt/cephfs-top-exporter/cephfs-top-exporter.py
RUN chmod +x /opt/cephfs-top-exporter/cephfs-top-exporter.py

# Exponer el puerto en el que correrá la aplicación
EXPOSE 8000

# Definir el comando de ejecución (ajustar según la aplicación)
CMD ["python3", "/opt/cephfs-top-exporter/cephfs-top-exporter.py"]
