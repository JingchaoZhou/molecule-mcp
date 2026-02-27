import glob, os, pwd, subprocess
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
    return fn

def _prepare_dirs_for(user: str, home: str):
    pw = pwd.getpwnam(user)
    cfg = os.path.join(home, ".config")
    data = os.path.join(home, ".local", "share")
    os.makedirs(cfg, exist_ok=True)
    os.makedirs(data, exist_ok=True)
    # 关键：目录必须归 nobody，否则 drop 后无法写
    os.chown(home, pw.pw_uid, pw.pw_gid)
    os.chown(os.path.join(home, ".config"), pw.pw_uid, pw.pw_gid)
    os.chown(os.path.join(home, ".local"), pw.pw_uid, pw.pw_gid)
    os.chown(os.path.join(home, ".local", "share"), pw.pw_uid, pw.pw_gid)

def _display_usable(d: str) -> bool:
    # 只要 X socket 在就基本可用（Xvfb -ac 无鉴权）
    if not d or not d.startswith(":"):
        return False
    sock = f"/tmp/.X11-unix/X{d[1:]}"
    return os.path.exists(sock)

def _pick_display() -> str:
    # 1) 优先用当前 DISPLAY（但必须真的可用）
    d = os.environ.get("DISPLAY", "")
    if _display_usable(d):
        return d

    # 2) 否则从 /tmp/.X11-unix/X* 自动挑一个存在的
    xs = sorted(glob.glob("/tmp/.X11-unix/X*"))
    if xs:
        num = os.path.basename(xs[-1])[1:]   # 取最后一个（通常是最新起的）
        return f":{num}"

    # 3) 实在没有才兜底
    return ":99"

@mcp.tool()
def open_chimerax():
    logf = "/tmp/chimerax.log"
    display = _pick_display()

    home = f"/tmp/chimerax_home_{CHIMERAX_USER}"
    os.makedirs(home, exist_ok=True)
    _prepare_dirs_for(CHIMERAX_USER, home)

    env = os.environ.copy()
    env["DISPLAY"] = display
    env["HOME"] = home
    env["XDG_CONFIG_HOME"] = os.path.join(home, ".config")
    env["XDG_DATA_HOME"]   = os.path.join(home, ".local", "share")
    env.setdefault("QT_QPA_PLATFORM", "xcb")
    env.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
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