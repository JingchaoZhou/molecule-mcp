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
    d = os.environ.get("DISPLAY")
    if d:
        return d
    return ":99"

@mcp.tool()
def open_chimerax():
    chimerax_bin = "/usr/lib/ucsf-chimerax/bin/ChimeraX"
    logf = "/tmp/chimerax.log"

    display = _pick_display()
    env = os.environ.copy()
    env["DISPLAY"] = display
    env.setdefault("QT_QPA_PLATFORM", "xcb")

    subprocess.Popen(
        [chimerax_bin,
         "--cmd", "remotecontrol xmlrpc true",
         "--no-sandbox",
         ],
        stdout=open(logf, "a"),
        stderr=open(logf, "a"),
        text=True,
        env=env,
    )
    return f"started {chimerax_bin} with DISPLAY={display}"

@mcp.tool()
def run_chimerax_command(command: str):
    """run chimerax command"""
    return s.run_command(command)