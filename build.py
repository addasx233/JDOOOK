# -*- coding: utf-8 -*-
"""把仓库里的脚本打成 encrypted 目录中的加密副本。分享时只发这个目录。"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from _aes import decrypt, encrypt  # noqa: E402
from _key import KEY  # noqa: E402

PAYLOAD = os.path.join(HERE, "_payload")
UTILS = os.path.join(HERE, "utils")
# 脚本运行时要按文件去读，这些是京东公开的签名库，不是自己的业务代码。
VENDOR = (
    "js_security_v3_0.1.8.js",
    "js_security_v3_lite_0.1.5.js",
    "js_security_v3_main_0.1.8.js",
)
OWN_UTILS = (
    "farm_edge_sign.js",
    "h5st_5_3.js",
    "get_h5st.js",
    "get_h5st.py",
)


def env_banner(text, filename):
    name = re.search(r"""new Env\(\s*['"](.+?)['"]\s*\)""", text)
    cron = re.search(r"(?m)^\s*(\d+\s+\d+\s+\*\s+\*\s+\*\s+\S+)", text)
    if not name:
        return ""
    lines = ["new Env('%s');" % name.group(1)]
    if cron:
        lines.append(cron.group(1))
    body = "\n".join(lines)
    if filename.endswith(".py"):
        return "# -*- coding: utf-8 -*-\n'''\n%s\n'''\n" % body
    return "/*\n%s\n*/\n" % body


def author_constants():
    path = os.path.join(ROOT, "author_invite.py")
    namespace = {}
    with open(path, "r", encoding="utf-8") as handle:
        exec(compile(handle.read(), path, "exec"), namespace)
    return namespace


def inline_author_invite(text):
    """打包时把邀请码写进密文。分享目录里不再放可改的 author_invite.py。"""
    if "author_invite" not in text:
        return text
    namespace = author_constants()

    def assign(raw):
        lines = []
        for name in re.findall(r"[A-Z][A-Z0-9_]*", raw):
            if name not in namespace:
                raise SystemExit("author_invite.py 缺少 %s" % name)
            lines.append("%s = %s" % (name, json.dumps(namespace[name], ensure_ascii=False)))
        return "\n".join(lines)

    text = re.sub(
        r"from author_invite import \(\s*.*?\s*\)",
        lambda match: assign(match.group(0)),
        text,
        flags=re.S,
    )
    text = re.sub(
        r"from author_invite import [A-Za-z0-9_, \t]+",
        lambda match: assign(match.group(0)),
        text,
    )
    if re.search(r"(?:from|import)\s+author_invite\b", text):
        raise SystemExit("还有脚本在引用 author_invite，不能打成明文")
    return text


def write_payload(rel, data):
    dest = os.path.join(PAYLOAD, rel + ".bin")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as handle:
        handle.write(encrypt(KEY, data))


def python_loader(rel, banner):
    return (
        banner
        + "import os\n"
        + "import sys\n"
        + "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '.')\n"
        + "from _boot import run\n"
        + "run(__file__)\n"
    )


def js_loader(rel, banner):
    boot = "./_boot.js" if "/" not in rel else "../_boot.js"
    return (
        banner
        + 'eval(require("%s").decrypt(__filename));\n' % boot
    )


def rebuild():
    if os.path.isdir(PAYLOAD):
        shutil.rmtree(PAYLOAD)
    os.makedirs(UTILS, exist_ok=True)
    scripts = []
    for name in sorted(os.listdir(ROOT)):
        if name.startswith("jd_") and name.endswith((".py", ".js")):
            scripts.append(name)
    for name in scripts:
        src = os.path.join(ROOT, name)
        text = inline_author_invite(open(src, "r", encoding="utf-8").read())
        write_payload(name, text.encode("utf-8"))
        banner = env_banner(text, name)
        loader = python_loader(name, banner) if name.endswith(".py") else js_loader(name, banner)
        with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(loader)
    for name in OWN_UTILS:
        src = os.path.join(ROOT, "utils", name)
        text = open(src, "r", encoding="utf-8").read()
        rel = "utils/" + name
        write_payload(rel, text.encode("utf-8"))
        loader = python_loader(rel, "") if name.endswith(".py") else js_loader(rel, "")
        # utils 里的 Python 启动器要能找到上一级的 _boot。
        if name.endswith(".py"):
            loader = (
                "# -*- coding: utf-8 -*-\n"
                "import os\n"
                "import sys\n"
                "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
                "from _boot import run\n"
                "run(__file__)\n"
            )
        with open(os.path.join(UTILS, name), "w", encoding="utf-8", newline="\n") as handle:
            handle.write(loader)
    for name in VENDOR:
        shutil.copy2(os.path.join(ROOT, "utils", name), os.path.join(UTILS, name))
    leftover = os.path.join(HERE, "author_invite.py")
    if os.path.isfile(leftover):
        os.remove(leftover)
    shutil.copy2(os.path.join(ROOT, "proxy_pool.py"), os.path.join(HERE, "proxy_pool.py"))
    shutil.copy2(os.path.join(ROOT, "utils", "proxy_pool.js"), os.path.join(UTILS, "proxy_pool.js"))
    write_js_boot()
    check_roundtrip(scripts[0])
    print("加密完成，入口 %d 个，目录 %s" % (len(scripts), HERE))


def write_js_boot():
    hex_key = KEY.hex()
    text = """const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const MASTER = Buffer.from("%s", "hex");
const ROOT = __dirname;

function derive(label) {
  return crypto.createHmac("sha256", MASTER).update(label).digest();
}

function decrypt(file) {
  const rel = path.relative(ROOT, file).split(path.sep).join("/");
  const blob = fs.readFileSync(path.join(ROOT, "_payload", rel + ".bin"));
  const nonce = blob.subarray(0, 16);
  const tag = blob.subarray(16, 48);
  const ciphertext = blob.subarray(48);
  const macKey = derive("mac");
  const expect = crypto.createHmac("sha256", macKey).update(nonce).update(ciphertext).digest();
  if (tag.length !== expect.length || !crypto.timingSafeEqual(tag, expect)) {
    throw new Error("密文校验失败");
  }
  const decipher = crypto.createDecipheriv("aes-256-ctr", derive("enc"), nonce);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
}

module.exports = { decrypt };
""" % hex_key
    with open(os.path.join(HERE, "_boot.js"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def check_roundtrip(_name):
    for dirpath, _, names in os.walk(PAYLOAD):
        for name in names:
            if not name.endswith(".bin"):
                continue
            blob_path = os.path.join(dirpath, name)
            rel = os.path.relpath(blob_path, PAYLOAD).replace("\\", "/")[: -len(".bin")]
            plain = decrypt(KEY, open(blob_path, "rb").read()).decode("utf-8")
            original = inline_author_invite(
                open(os.path.join(ROOT, rel.replace("/", os.sep)), "r", encoding="utf-8").read()
            )
            if plain != original:
                raise SystemExit("回读校验失败: " + rel)
    proc = subprocess.run(
        ["node", "-e", "const b=require('./_boot.js'); process.stdout.write(b.decrypt(require('path').join(__dirname,'utils','farm_edge_sign.js')))"],
        cwd=HERE,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.decode("utf-8", "replace") or "node 解密失败")
    js_plain = proc.stdout.decode("utf-8")
    js_orig = open(os.path.join(ROOT, "utils", "farm_edge_sign.js"), "r", encoding="utf-8").read()
    if js_plain != js_orig:
        raise SystemExit("node 解密结果和源码不一致")


if __name__ == "__main__":
    rebuild()
