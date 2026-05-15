import socket
import threading
import time
import json
import os
from flask import Flask, render_template, jsonify
from datetime import datetime

# global dict to store all nodes info
# key = node_id, value = info dict
nodes = {}
lock = threading.Lock()

# config
UDP_PORT = 9999
WEB_PORT = 8080
TIMEOUT = 15   # if no heartbeat in 15s, mark as DEAD
CHECK_INTERVAL = 3

# log file
LOG_FILE = "monitor.log"

app = Flask(__name__)


def write_log(msg):
    # save events to log file so we can check later
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[" + t + "] " + msg
    print(line)
    try:
        f = open(LOG_FILE, "a")
        f.write(line + "\n")
        f.close()
    except:
        pass


def receive_heartbeats():
    # listen UDP socket for heartbeats from all nodes
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', UDP_PORT))
    print("listening for heartbeats on UDP port " + str(UDP_PORT))

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            msg = json.loads(data.decode())
            nid = msg['node_id']

            with lock:
                # if this is a new node, log it
                is_new = nid not in nodes
                was_dead = (not is_new) and nodes[nid]['status'] == 'DEAD'

                nodes[nid] = {
                    'node_id': nid,
                    'ip': addr[0],
                    'port': addr[1],
                    'cpu': msg.get('cpu', 0),
                    'memory': msg.get('memory', 0),
                    'disk': msg.get('disk', 0),
                    'last_seen': time.time(),
                    'status': 'ALIVE',
                    'joined_at': nodes[nid]['joined_at'] if not is_new else time.time()
                }

                if is_new:
                    write_log("NEW node joined: " + nid + " from " + addr[0])
                if was_dead:
                    write_log("node " + nid + " is BACK ONLINE")

        except Exception as e:
            # bad message or something, just skip
            print("error receiving:", e)


def check_dead_nodes():
    # background thread, check every few seconds if some node is dead
    while True:
        time.sleep(CHECK_INTERVAL)
        now = time.time()
        with lock:
            for nid in nodes:
                gap = now - nodes[nid]['last_seen']
                # if too long no heartbeat, mark dead
                if gap > TIMEOUT and nodes[nid]['status'] == 'ALIVE':
                    nodes[nid]['status'] = 'DEAD'
                    write_log("!! node " + nid + " is DEAD (no hb for " + str(int(gap)) + "s)")


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/nodes')
def api_nodes():
    # return all nodes status as json
    result = []
    with lock:
        for nid in nodes:
            n = dict(nodes[nid])
            n['last_seen_ago'] = round(time.time() - n['last_seen'], 1)
            n['uptime'] = int(time.time() - n['joined_at'])
            result.append(n)
    # sort by id to make order stable on dashboard
    result.sort(key=lambda x: x['node_id'])
    return jsonify(result)


@app.route('/api/stats')
def api_stats():
    with lock:
        total = len(nodes)
        alive = 0
        for nid in nodes:
            if nodes[nid]['status'] == 'ALIVE':
                alive = alive + 1
        dead = total - alive
    return jsonify({
        'total': total,
        'alive': alive,
        'dead': dead
    })


@app.route('/api/logs')
def api_logs():
    # read last 30 lines of log file
    lines = []
    try:
        f = open(LOG_FILE, "r")
        all_lines = f.readlines()
        f.close()
        lines = all_lines[-30:]
        lines.reverse()
    except:
        lines = []
    return jsonify({'logs': lines})


if __name__ == '__main__':
    write_log("=== Monitor starting ===")

    # start heartbeat receiver thread
    t1 = threading.Thread(target=receive_heartbeats)
    t1.daemon = True
    t1.start()

    # start the dead-check thread
    t2 = threading.Thread(target=check_dead_nodes)
    t2.daemon = True
    t2.start()

    print("dashboard at http://localhost:" + str(WEB_PORT))
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
