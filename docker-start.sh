#!/bin/sh
# Start a virtual display, window manager, VNC, noVNC proxy, then the Tkinter GUI.
set -e

export DISPLAY=:1

echo "[docker] Starting Xvfb..."
Xvfb :1 -screen 0 1280x800x24 &
sleep 2

echo "[docker] Starting fluxbox..."
fluxbox >/tmp/fluxbox.log 2>&1 &
sleep 1

echo "[docker] Starting x11vnc..."
x11vnc -display :1 -nopw -listen localhost -xkb -forever -shared -rfbport 5900 >/tmp/x11vnc.log 2>&1 &
sleep 1

echo "[docker] Starting noVNC on :8080..."
# Debian ships noVNC under /usr/share/novnc/
websockify --web=/usr/share/novnc/ 8080 localhost:5900 >/tmp/websockify.log 2>&1 &
sleep 1

echo "[docker] Launching PNC Language Analysis Simulator..."
echo "[docker] Open http://<host>:8080/vnc.html?autoconnect=true&resize=scale"
exec python3 edu_interpreter.py
