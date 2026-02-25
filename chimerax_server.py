import socket
import time
import subprocess
from xmlrpc.client import ServerProxy
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("chimerax")
xmlrpc_port = 42184
s = ServerProxy(uri=f"http://127.0.0.1:{xmlrpc_port}/RPC2")

def _wait_port(host: str, port: int, timeout_s: float = 20.0) -> None:
    end = time.time() + timeout_s
    last_err = None
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except Exception as e:
            last_err = e
            time.sleep(0.2)
    raise RuntimeError(f"xmlrpc not ready on {host}:{port}, last_err={last_err}")

@mcp.tool()
def open_chimerax():
    """open chimerax with remote control enabled"""
    chimerax_bin = "/usr/lib/ucsf-chimerax/bin/ChimeraX"
    logf = "/tmp/chimerax.log"

    with open(logf, "a") as lf:
        subprocess.Popen(
            [chimerax_bin, "--cmd", "remotecontrol xmlrpc true"],
            stdout=lf,
            stderr=lf,
            text=True,
            close_fds=True,
        )

    _wait_port("127.0.0.1", xmlrpc_port, timeout_s=30.0)
    return f"started {chimerax_bin} (xmlrpc on {xmlrpc_port})"

@mcp.tool()
def run_chimerax_command(command: str):
    """run chimerax command"""
    return s.run_command(command)