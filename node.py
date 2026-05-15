import socket
import json
import time
import psutil
import sys
import random
import argparse
import os

# default config
MONITOR_IP = '127.0.0.1'
MONITOR_PORT = 9999
INTERVAL = 5     # send heartbeat every 5 sec


def get_stats():
    # get current system info using psutil
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    try:
        disk = psutil.disk_usage('/').percent
    except:
        disk = 0
    return cpu, mem, disk


def main():
    # parse cmd line args
    parser = argparse.ArgumentParser(description="Node Health Reporter")
    parser.add_argument('--id', type=str, default=None, help='node id (auto random if not set)')
    parser.add_argument('--monitor', type=str, default=MONITOR_IP, help='monitor server ip')
    parser.add_argument('--port', type=int, default=MONITOR_PORT, help='monitor udp port')
    parser.add_argument('--interval', type=int, default=INTERVAL, help='hb interval (sec)')
    parser.add_argument('--fail-after', type=int, default=0, help='simulate failure after N seconds (0=disable)')
    args = parser.parse_args()

    # if no id provided, make a random one
    if args.id:
        node_id = args.id
    else:
        node_id = "node-" + str(random.randint(100, 999))

    print("== Node started ==")
    print("id:", node_id)
    print("monitor:", args.monitor + ":" + str(args.port))
    print("interval:", args.interval, "sec")
    if args.fail_after > 0:
        print("!! will simulate failure after", args.fail_after, "sec")
    print("-" * 30)

    # create udp socket (one is enough for all sends)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    start_time = time.time()
    count = 0

    while True:
        # check failure simulation
        if args.fail_after > 0:
            running = time.time() - start_time
            if running >= args.fail_after:
                print("=== simulating crash now, bye ===")
                sys.exit(0)

        try:
            cpu, mem, disk = get_stats()
            msg = {
                'node_id': node_id,
                'cpu': cpu,
                'memory': mem,
                'disk': disk,
                'timestamp': time.time(),
                'pid': os.getpid()
            }
            data = json.dumps(msg).encode()
            sock.sendto(data, (args.monitor, args.port))
            count = count + 1
            print("[" + str(count) + "] sent hb -> cpu=" + str(cpu) + "% mem=" + str(mem) + "% disk=" + str(disk) + "%")
        except Exception as e:
            # something wrong but keep running
            print("send error:", e)

        time.sleep(args.interval)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nnode stopped by user")
