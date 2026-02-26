import socket
import time
import os
import glob
import subprocess
from xmlrpc.client import ServerProxy
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("chimerax")
xmlrpc_port = 42184
s = ServerProxy(uri=f"http://127.0.0.1:{xmlrpc_port}/RPC2")

def _pick_display():
    d = os.environ.get("DISPLAY", "")
    if d.startswith(":"):
        sock = f"/tmp/.X11-unix/X{d[1:]}"
        if os.path.exists(sock):
            return d

    xs = sorted(glob.glob("/tmp/.X11-unix/X*"))
    if xs:
        num = os.path.basename(xs[-1])[1:]
        return f":{num}"

    return ":99"

def _wait_port(host, port, timeout=20):
    start = time.time()
    last_err = None
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True, None
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    return False, last_err

@mcp.tool()
def open_chimerax():
    chimerax_bin = "/usr/lib/ucsf-chimerax/bin/ChimeraX"
    logf = "/tmp/chimerax.log"

    display = _pick_display()
    env = os.environ.copy()
    env["DISPLAY"] = display
    env.setdefault("QT_QPA_PLATFORM", "xcb")

    subprocess.Popen(
        [
            chimerax_bin,
            "--no-sandbox",
            "--cmd",
            f"remotecontrol xmlrpc true port {xmlrpc_port}",
        ],
        stdout=open(logf, "a"),
        stderr=open(logf, "a"),
        text=True,
        env=env,
    )

    ok, err = _wait_port("127.0.0.1", xmlrpc_port, timeout=20)
    if not ok:
        return f"started {chimerax_bin} DISPLAY={display} but xmlrpc not ready on 127.0.0.1:{xmlrpc_port}, last_err={err}"

    return f"ready {chimerax_bin} DISPLAY={display} xmlrpc={xmlrpc_port}"

@mcp.tool()
def run_chimerax_command(command: str):
    return s.run_command(command)