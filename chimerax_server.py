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
    # 1) 优先使用当前 DISPLAY（但必须 socket 存在）
    d = os.environ.get("DISPLAY", "")
    if d.startswith(":"):
        sock = f"/tmp/.X11-unix/X{d[1:]}"
        if os.path.exists(sock):
            return d

    # 2) 自动找一个存在的 X socket（你现在会选到 :171）
    xs = sorted(glob.glob("/tmp/.X11-unix/X*"))
    if xs:
        # 取第一个/最后一个都行；这里取第一个更直觉
        num = os.path.basename(xs[0])[1:]
        return f":{num}"

    # 3) 兜底
    return ":105"

@mcp.tool()
def open_chimerax():
    chimerax_bin = "/usr/lib/ucsf-chimerax/bin/ChimeraX"
    logf = "/tmp/chimerax.log"

    display = _pick_display()
    env = os.environ.copy()
    env["DISPLAY"] = display
    env.setdefault("QT_QPA_PLATFORM", "xcb")

    subprocess.Popen(
        [chimerax_bin, "--cmd", "remotecontrol xmlrpc true"],
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