import json
import time
import re
import subprocess
import configargparse
import logging
from prometheus_client import start_http_server, Gauge



metrics = {}
date_gauge = Gauge("cephfs_top_timestamp", "Timestamp of the data")
strings_keys = ["mount_root", "mount_point@host/addr"]
strings_keys_pattern = '|'.join(map(re.escape, strings_keys))

def parse_arguments():
    parser = configargparse.ArgumentParser(description="Cephfs Top Exporter parameters.")
    
    parser.add_argument("--cluster", env_var="CEPH_CLUSTER", help="Ceph cluster to connect.")
    parser.add_argument("--id", env_var="CEPHFS_TOP_USER_NAME", default="fstop", help="Ceph user to use to connection (default: fstop)")
    parser.add_argument("--conffile", env_var="CEPHFS_TOP_CONFFILE", default="/etc/ceph/ceph.conf", help="Path to cluster configuration file")
    parser.add_argument("--selftest", env_var="CEPHFS_TOP_SELFTEST", action="store_true", help="Run in selftest mode")        
    parser.add_argument("--dumpfs", env_var="CEPHFS_TOP_DUMPFS", help="Dump the metrics of the given fs to stdout (default: dump all filesystems)")
    parser.add_argument("--jsondump", env_var="CEPHFS_TOP_JSONDUMP", help="Only used to make export tests from json collected from production deployments")
    parser.add_argument("--port", env_var="CEPHFS_TOP_EXPORTER_PORT", default="8000", help="Port to publish prometheus metrics (default: 8000).")
    parser.add_argument("--trace_level", env_var="CEPHFS_TOP_EXPORTER_TRACE_LEVEL", default="INFO", help="Trace level (default: INFO).")

    args = parser.parse_args()    

    return args

def get_cephfstop_json_data(file_path = ''):
    data = None
    try:        
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:     
        logger.error(f"File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:        
        logger.error(f"File '{file_path}' contains a not valid JSON content.")
        return None
    except PermissionError:        
        logger.error(f"I can't access the file '{file_path}'.")
        return None
    except Exception as e:        
        logger.error(f"Unexpect error opening file '{file_path}': {e}")
        return None

def process_cephfs_top_parameters(args):
    cephfs_stop_cmd_parameters = ["/usr/bin/cephfs-top"]
    
    if args.cluster:
       cephfs_stop_cmd_parameters.append(" --cluster")
       cephfs_stop_cmd_parameters.append(" " + args.cluster)
    if args.id:
        cephfs_stop_cmd_parameters.append(" --id ")
        cephfs_stop_cmd_parameters.append(" " + args.id)        
    if args.conffile:
        cephfs_stop_cmd_parameters.append(" --conffile ")
        cephfs_stop_cmd_parameters.append(" " + args.conffile)
    if args.selftest:
        cephfs_stop_cmd_parameters.append(" --selftest")        
    if args.dumpfs:
        cephfs_stop_cmd_parameters.append(" --dumpfs ")
        cephfs_stop_cmd_parameters.append(" " + args.dumpfs)        
    else:
        cephfs_stop_cmd_parameters.append(" --dump")

    return cephfs_stop_cmd_parameters

def get_cephfstop_data(cephfs_top_cmd_parameters):
    data = None
    try:
        logger.debug('Calling cephfs-top program with the following parameters: ' + ''.join(map(str, cephfs_top_cmd_parameters)))        
        cephfs_top_cmd_parameters=["/usr/bin/cephfs-top", "--id", "fstop", "--conffile", "/etc/ceph/ceph.conf", "--dump"]
        result = subprocess.run(cephfs_top_cmd_parameters, capture_output=True, text=True, timeout=10)
        data = json.loads(result.stdout)
    except Exception as e:
        logger.error(f"# Error executing cephfs-top program: {e}")
    return data

def parse_value(value):    
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str) and value.isnumeric():
            return float(value)
    except ValueError:
        pass    
    return None

def sanitize_metric_name(name):    
    name = name.replace("/", "_slash_").replace("@", "_at_").replace(".", "_").replace(" ", "_").lower()    
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_')
    return name

def configure_logger(logger_name="CephFS_Top_Exporter", level=logging.INFO, log_file="CephFS_Top_Exporter.log"):
    format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(format)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def get_trace_level_based_on_str(strTraceLevel):    
    if strTraceLevel.upper() == "DEBUG":
        trace_level = logging.DEBUG
    elif strTraceLevel.upper() == "ERROR":       
        trace_level = logging.ERROR
    else:
        trace_level = logging.INFO
    return trace_level


def process_metrics(data, prefix=""):
    if data is None:
        return
    
    date_gauge.set(time.mktime(time.strptime(data["date"], "%a %b %d %H:%M:%S %Y")))
    
    for metric_name, metric_value in data['client_count'].items():
        metric_name = sanitize_metric_name(f"{prefix}{metric_name}")
        if metric_name not in metrics:
            logger.debug("New metric detected: " + metric_name)
            metrics[metric_name] = Gauge(metric_name, f"{metric_name} metric refer to the global client_count section of cephfs-top utility.")        
        metric_value_parsed= parse_value(metric_value)                                        
        if metric_value_parsed is not None:
          metrics[metric_name].set(metric_value_parsed)
    for cephfs_name, client_performance_data in data['filesystems'].items():
        for client_id, performance_data in client_performance_data.items():
               mount_root=performance_data["mount_root"]
               mount_point_host_addr=performance_data["mount_point@host/addr"]
               for metric_name, metric_value in performance_data.items():                    
                    if not re.search(metric_name, strings_keys_pattern):
                        prometheus_metric_name = sanitize_metric_name(f"{prefix}{metric_name}")
                        if prometheus_metric_name not in metrics:
                            logger.debug("New metric detected: " + metric_name)
                            metrics[prometheus_metric_name] = Gauge(prometheus_metric_name, f"{prometheus_metric_name} metric refer to cephfs-top for more information.", ['cephfs_name', 'client_id', 'mount_root','mount_point_host_addr'])
                        metric_value_parsed= parse_value(metric_value)                                        
                        if metric_value_parsed is not None:
                            metrics[prometheus_metric_name].labels(cephfs_name=cephfs_name, client_id=client_id,mount_root=mount_root,mount_point_host_addr=mount_point_host_addr).set(metric_value_parsed)

def update_metrics(cephfs_stop_cmd_parameters, json_file):
    if not json_file:
       logger.debug("Calling get_cephfstop_data with the following parameters: " + ''.join(map(str, cephfs_stop_cmd_parameters)))
       data = get_cephfstop_data(cephfs_stop_cmd_parameters)
    else:
       logger.debug("Calling get_cephfstop_json_data with the following parameters: " + json_file)
       data = get_cephfstop_json_data(json_file)
    process_metrics(data, "cephfs_top_")

def main():
    args = parse_arguments()
    http_port = args.port

    json_file = ""
    if args.jsondump :
        json_file = args.jsondump

    cephf_stop_cmd_parameters= process_cephfs_top_parameters(args)    

    trace_level = logging.INFO 
    if args.trace_level:
       trace_level= get_trace_level_based_on_str(args.trace_level)

    global logger 
    logger = configure_logger(level= trace_level)    
    logger.info("Start http server at port " + http_port)
    start_http_server(port=int(http_port))
    while True:
        logger.debug("Updating metrics with the following parameters, cephfstop_cmd_parameters=" +  ''.join(map(str, cephf_stop_cmd_parameters)) + " json_file=" + json_file)
        update_metrics(cephf_stop_cmd_parameters, json_file)
        time.sleep(10)  

if __name__ == "__main__":
    main()