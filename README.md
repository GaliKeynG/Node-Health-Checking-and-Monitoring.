# Node Health Checking and Monitoring

Distributed System course project.

A small distributed system that checks if nodes are alive or dead, and shows everything on a live web dashboard.

## What it does

A simple distributed monitoring system. There is one **Monitor** server and many **Node** workers. Every node sends heartbeat messages (with cpu / memory / disk info) to the monitor. If the monitor does not receive any heartbeat from a node for a while, it marks that node as DEAD. You can see everything in real-time on a web dashboard.

## Architecture

!\[System Architecture](architecture.png)

The system has three kinds of parts: many **Worker Nodes**, one **Monitor Server**, and a **Web Dashboard**.

Each worker node reads its own CPU, memory and disk usage with `psutil`, puts it into a small JSON message, and sends it to the monitor over **UDP** every 5 seconds. This message is the heartbeat.

The monitor runs three things at the same time (three threads):

* **Heartbeat Receiver** — listens on UDP port `9999`. When a heartbeat arrives, it saves the node's info into a shared dictionary called `nodes`, and updates the node's `last\\\_seen` time to now.
* **Failure Detector** — wakes up every 3 seconds and checks every node. If a node has not sent a heartbeat for more than **15 seconds**, it marks that node as `DEAD`.
* **Flask Web Server** — runs on port `8080` and serves the dashboard plus a few API routes (`/api/nodes`, `/api/stats`, `/api/logs`).

All three threads use the same `nodes` data, so it is protected by a **Lock** to avoid race conditions.

The dashboard is a web page in the browser. It asks the monitor for the latest data every 2 seconds (HTTP polling) and redraws the table, so you can watch nodes turn from green (ALIVE) to red (DEAD) in real time.

### Heartbeat message format

The heartbeat is JSON, sent over UDP:

```json
{
  "node\\\_id": "node-1",
  "cpu": 25.3,
  "memory": 41.2,
  "disk": 60.1,
  "timestamp": 1730000000.12,
  "pid": 12345
}
```

## Failure Detection Workflow

This is the most important part of the project. The picture below shows what happens when a node crashes and then comes back.

!\[Failure Detection Workflow](failure\_detection\_workflow.png)

The idea is simple. A crashed node cannot send a message to say it crashed. So the monitor does not wait for one. It just notices that the heartbeats stopped.

|Step|What happens|
|-|-|
|1|Each node sends a heartbeat every 5 seconds.|
|2|The monitor records the time it last heard from each node (`last\\\_seen`).|
|3|A background thread checks every 3 seconds.|
|4|If `now − last\\\_seen > 15s`, the node becomes **DEAD**.|
|5|If a dead node sends a heartbeat again, it goes back to **ALIVE** automatically.|

The 15-second timeout is about three missed heartbeats. It gives a small safety margin, so a normal network delay does not mark a node dead by mistake.

## Files

|File|What it is|
|-|-|
|`monitor.py`|The central monitor server (UDP receiver + failure detector + Flask).|
|`node.py`|The worker node program that sends heartbeats.|
|`templates/dashboard.html`|The web dashboard page.|
|`requirements.txt`|Python libraries needed.|
|`architecture.png`|The architecture diagram.|
|`failure\\\_detection\\\_workflow.png`|The failure detection workflow diagram.|
|`monitor.log`|Created when running, stores events.|

## How to run

1. Install the dependencies:

```
pip install -r requirements.txt
```

2. Start the monitor (in one terminal):

```
python monitor.py
```

Then open http://localhost:8080 in your browser to see the dashboard.

3. Start some nodes (each in its own terminal):

```
python node.py --id node-1
python node.py --id node-2
python node.py --id node-3
```

You can also run nodes on a different machine. Just pass the monitor's IP:

```
python node.py --id node-4 --monitor 192.168.1.10
```

## Testing failure detection

Just kill a node with Ctrl+C. After about 15 seconds the dashboard marks it DEAD. If you start it again, it comes back to ALIVE.

You can also simulate a crash with `--fail-after`:

```
python node.py --id node-test --fail-after 20
```

This node runs for 20 seconds and then exits by itself. It is good for a demo, because you do not have to touch anything.

## Notes / things I learned

* UDP is good for heartbeats because we do not really care if one packet is lost. We just need most of them to arrive in time.
* The monitor uses threads: one for receiving heartbeats, one for the failure check, and one for Flask.
* I used a Lock to protect the shared `nodes` dictionary. Before I added it, I got some strange bugs.

## Possible improvements (not done yet)

* Use multiple monitors with leader election (so the monitor is not a single point of failure).
* Add authentication, so not anyone can send a fake heartbeat.
* Save history to a database.
* Show CPU and memory as graphs over time.



