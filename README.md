# Node Health Checking and Monitoring

Distributed System course project.

## What it does

A simple distributed monitoring system. There is one **Monitor** server and many **Node** workers.
Every nodes sends heartbeat messages (cpu / memory / disk info) to the monitor.
If the monitor does not receive any heartbeat from a node for a while, it marks as DEAD.
You can see everything in real-time on a web dashboard.

## Architecture


   +--------+        UDP heartbeat        +-----------+
   | Node 1 | --------------------------> |           |
   +--------+                             |           |
                                          |  Monitor  |  <-- browser http://localhost:8080
   +--------+        UDP heartbeat        |           |
   | Node 2 | --------------------------> |           |
   +--------+                             +-----------+
   ...


- **Communication**: UDP for heartbeats (lightweight, no connection needed)
- **Failure detection**: timeout based (no hb for 15 sec -> DEAD)
- **Dashboard**: Flask + HTML + JS polling

## Files

- `monitor.py` - the central monitor server
- `node.py` - the worker node program
- `templates/dashboard.html` - the web dashboard page
- `requirements.txt` - python libs needed
- `monitor.log` - generated when running, stores events

## How to run

1. Install dependencies:

pip install -r requirements.txt


2. Start the monitor (in one terminal):

python monitor.py

Then open http://localhost:8080 in your browser.

3. Start some nodes (each in its own terminal):

python node.py --id node-1
python node.py --id node-2
python node.py --id node-3


You can also run nodes on different machines, just pass `--monitor <ip>`:

python node.py --id node-4 --monitor 192.168.1.10


## Testing failure detection

Just kill a node (Ctrl+C). After about 15 seconds the dashboard will mark it DEAD.
If you restart it, it will come back to ALIVE again.

You can also use `--fail-after` to simulate a crash:

python node.py --id node-test --fail-after 20

This node will run for 20 seconds and then exit.

## Things I learned

- UDP is good for heartbeats because we don't really care if 1 packet is lost, we just need most of them to arrive in time.
- The monitor uses threads: one for receiving heartbeats, one for failure check, one for Flask.
- Used a lock to protect the shared `nodes` dict.

## Possible improvements

- Use multiple monitors with leader election
- Add authentication
- Save history to a database
- Better visualization (graphs)
