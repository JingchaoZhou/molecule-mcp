import os, pwd, subprocess
from xmlrpc.client import ServerProxy
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("chimerax")
xmlrpc_port = 42184
s = ServerProxy(uri=f"http://127.0.0.1:{xmlrpc_port}/RPC2")

CHIMERAX_BIN = "/usr/lib/ucsf-chimerax/bin/ChimeraX"
CHIMERAX_USER = os.environ.get("CHIMERAX_USER", "nobody")  # 你也可以换成一个真实用户

def _drop_privileges(user: str):
    pw = pwd.getpwnam(user)
    def fn():
        os.setgid(pw.pw_gid)
        os.setuid(pw.pw_uid)
        os.environ["HOME"] = pw.pw_dir
    return fn

@mcp.tool()
def open_chimerax():
    logf = "/tmp/chimerax.log"
    display = os.environ.get("DISPLAY", ":99")

    env = os.environ.copy()
    env["DISPLAY"] = display
    env.setdefault("QT_QPA_PLATFORM", "xcb")
    env.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

    # 关键：给 ChimeraX 可写目录，避免 /do/not/run/as/root
    env["HOME"] = f"/tmp/chimerax_home_{CHIMERAX_USER}"
    env["XDG_CONFIG_HOME"] = env["HOME"] + "/.config"
    env["XDG_DATA_HOME"]   = env["HOME"] + "/.local/share"
    os.makedirs(env["XDG_CONFIG_HOME"], exist_ok=True)
    os.makedirs(env["XDG_DATA_HOME"], exist_ok=True)

    # 关键：GL/EGL 报错时，强制软件渲染（常见救命项）
    env.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    env.setdefault("QT_XCB_GL_INTEGRATION", "none")

    cmd = f"remotecontrol xmlrpc enable address 127.0.0.1 port {xmlrpc_port}"

    subprocess.Popen(
        [CHIMERAX_BIN, "--cmd", cmd],
        stdout=open(logf, "a"),
        stderr=open(logf, "a"),
        text=True,
        env=env,
        preexec_fn=_drop_privileges(CHIMERAX_USER),
    )
    return f"started {CHIMERAX_BIN} DISPLAY={display} user={CHIMERAX_USER}"

@mcp.tool()
def run_chimerax_command(command: str):
    return s.run_command(command)