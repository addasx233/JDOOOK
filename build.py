# -*- coding: utf-8 -*-
"""把仓库里的脚本打成 encrypted 目录中的加密副本。分享时只发这个目录。

只重写源码有改动或新增的文件。密文带随机数，不能靠比较 .bin 判断改动，
所以用 .manifest.json 记下明文摘要。没有记录时先解密已有密文核对，内容一样就不重写。
"""

import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from _aes import decrypt, encrypt  # noqa: E402
from _key import KEY  # noqa: E402

PAYLOAD = os.path.join(HERE, "_payload")
UTILS = os.path.join(HERE, "utils")
MANIFEST = os.path.join(HERE, ".manifest.json")
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
    "ja4_client.py",
)
# 活动脚本会 import 这些文件。打进密文，分享目录不留明文，由 _boot 按需解密。
SHARED = ("account_common.py",)
# 源码放在 utils，导入名仍是 ja4_client。
JA4_SOURCE = os.path.join("utils", "ja4_client.py")
JA4_MODULE = "ja4_client.py"


def env_banner(text, filename):
    name = re.search(r"""new Env\(\s*['"](.+?)['"]\s*\)""", text)
    cron = re.search(r"(?m)^\s*(\d+\s+\d+\s+\*\s+\*\s+\*\s+\S+)", text)
    version = re.search(r"版本：(\d{8})", text)
    if not name:
        return ""
    lines = ["new Env('%s');" % name.group(1)]
    if cron:
        lines.append(cron.group(1))
    if version:
        lines.append("版本：%s" % version.group(1))
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


def digest_of(*parts):
    hasher = hashlib.sha256()
    for part in parts:
        if isinstance(part, str):
            part = part.encode("utf-8")
        hasher.update(part)
        hasher.update(b"\0")
    return hasher.hexdigest()


def load_manifest():
    try:
        with open(MANIFEST, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_manifest(manifest):
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def read_text(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def payload_path(rel):
    return os.path.join(PAYLOAD, rel + ".bin")


def same_payload(rel, plain):
    path = payload_path(rel)
    if not os.path.isfile(path):
        return False
    try:
        return decrypt(KEY, read_bytes(path)) == plain
    except (OSError, ValueError):
        return False


def same_text(path, text):
    if not os.path.isfile(path):
        return False
    try:
        return read_text(path) == text
    except OSError:
        return False


def same_bytes(path, data):
    if not os.path.isfile(path):
        return False
    try:
        return read_bytes(path) == data
    except OSError:
        return False


def drop(path, label, stats):
    if not os.path.isfile(path):
        return
    os.remove(path)
    stats["delete"].append(label)
    print("删除 " + label)


def publish_payload(manifest, stats, key, plain, loader_path, loader_text):
    digest = digest_of(plain, loader_text or "")
    loader_ready = loader_path is None or os.path.isfile(loader_path)
    if manifest.get(key) == digest and os.path.isfile(payload_path(key)) and loader_ready:
        stats["skip"] += 1
        return False
    loader_same = loader_path is None or same_text(loader_path, loader_text)
    if same_payload(key, plain) and loader_same:
        manifest[key] = digest
        stats["skip"] += 1
        return False
    write_payload(key, plain)
    if loader_path is not None:
        os.makedirs(os.path.dirname(loader_path), exist_ok=True)
        with open(loader_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(loader_text)
    manifest[key] = digest
    stats["update"].append(key)
    print("更新 " + key)
    return True


def publish_bytes(manifest, stats, key, data, dest):
    digest = digest_of(data)
    if manifest.get(key) == digest and os.path.isfile(dest):
        stats["skip"] += 1
        return False
    if same_bytes(dest, data):
        manifest[key] = digest
        stats["skip"] += 1
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as handle:
        handle.write(data)
    manifest[key] = digest
    stats["update"].append(key)
    print("更新 " + key)
    return True


def script_loader(name, text):
    banner = env_banner(text, name)
    if name.endswith(".py"):
        return python_loader(name, banner)
    return js_loader(name, banner)


def util_loader(name):
    rel = "utils/" + name
    if name.endswith(".py"):
        return (
            "# -*- coding: utf-8 -*-\n"
            "import os\n"
            "import sys\n"
            "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
            "from _boot import run\n"
            "run(__file__)\n"
        )
    return js_loader(rel, "")


def list_scripts():
    scripts = []
    for name in sorted(os.listdir(ROOT)):
        if name.startswith("jd_") and name.endswith((".py", ".js")):
            scripts.append(name)
    return scripts


def prune(scripts, expected_payloads, manifest, stats):
    script_names = set(scripts)
    if os.path.isdir(PAYLOAD):
        for dirpath, _, names in os.walk(PAYLOAD):
            for name in names:
                if not name.endswith(".bin"):
                    continue
                blob = os.path.join(dirpath, name)
                rel = os.path.relpath(blob, PAYLOAD).replace("\\", "/")[: -len(".bin")]
                if rel in expected_payloads:
                    continue
                os.remove(blob)
                manifest.pop(rel, None)
                loader = None
                if rel.startswith("utils/"):
                    candidate = os.path.join(HERE, rel.replace("/", os.sep))
                    base = os.path.basename(candidate)
                    if base not in VENDOR and base != "proxy_pool.js":
                        loader = candidate
                elif rel.startswith("jd_"):
                    loader = os.path.join(HERE, rel)
                if loader is not None and os.path.isfile(loader):
                    os.remove(loader)
                stats["delete"].append(rel)
                print("删除 " + rel)
    for name in os.listdir(HERE):
        if name.startswith("jd_") and name.endswith((".py", ".js")) and name not in script_names:
            drop(os.path.join(HERE, name), name, stats)


def rebuild():
    os.makedirs(PAYLOAD, exist_ok=True)
    os.makedirs(UTILS, exist_ok=True)
    manifest = load_manifest()
    stats = {"update": [], "skip": 0, "delete": []}
    expected = set()
    expected_payloads = set()
    scripts = list_scripts()

    for name in scripts:
        text = inline_author_invite(read_text(os.path.join(ROOT, name)))
        plain = text.encode("utf-8")
        publish_payload(
            manifest, stats, name, plain, os.path.join(HERE, name), script_loader(name, text)
        )
        expected.add(name)
        expected_payloads.add(name)

    for name in SHARED:
        text = read_text(os.path.join(ROOT, name))
        publish_payload(manifest, stats, name, text.encode("utf-8"), None, None)
        expected.add(name)
        expected_payloads.add(name)
        drop(os.path.join(HERE, name), name, stats)

    ja4_text = read_text(os.path.join(ROOT, JA4_SOURCE))
    publish_payload(manifest, stats, JA4_MODULE, ja4_text.encode("utf-8"), None, None)
    expected.add(JA4_MODULE)
    expected_payloads.add(JA4_MODULE)
    drop(os.path.join(HERE, JA4_MODULE), JA4_MODULE, stats)

    for name in OWN_UTILS:
        rel = "utils/" + name
        text = read_text(os.path.join(ROOT, "utils", name))
        publish_payload(
            manifest,
            stats,
            rel,
            text.encode("utf-8"),
            os.path.join(UTILS, name),
            util_loader(name),
        )
        expected.add(rel)
        expected_payloads.add(rel)

    for name in VENDOR:
        rel = "utils/" + name
        dest = os.path.join(UTILS, name)
        publish_bytes(manifest, stats, rel, read_bytes(os.path.join(ROOT, "utils", name)), dest)
        expected.add(rel)

    drop(os.path.join(HERE, "author_invite.py"), "author_invite.py", stats)
    publish_bytes(
        manifest,
        stats,
        "proxy_pool.py",
        read_bytes(os.path.join(ROOT, "proxy_pool.py")),
        os.path.join(HERE, "proxy_pool.py"),
    )
    expected.add("proxy_pool.py")
    publish_bytes(
        manifest,
        stats,
        "utils/proxy_pool.js",
        read_bytes(os.path.join(ROOT, "utils", "proxy_pool.js")),
        os.path.join(UTILS, "proxy_pool.js"),
    )
    expected.add("utils/proxy_pool.js")

    boot = write_js_boot().encode("utf-8")
    publish_bytes(manifest, stats, "_boot.js", boot, os.path.join(HERE, "_boot.js"))
    expected.add("_boot.js")

    prune(scripts, expected_payloads, manifest, stats)
    for key in list(manifest):
        if key not in expected:
            del manifest[key]
    save_manifest(manifest)

    written = [name for name in stats["update"] if name in expected_payloads]
    check_roundtrip(written, "_boot.js" in stats["update"])
    removed = len(stats["delete"])
    extra = ("，删除 %d 个" % removed) if removed else ""
    print(
        "加密完成，更新 %d 个，未改动 %d 个%s，目录 %s"
        % (len(stats["update"]), stats["skip"], extra, HERE)
    )


def write_js_boot():
    hex_key = KEY.hex()
    return """const crypto = require("crypto");
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


def check_roundtrip(names, boot_changed):
    for rel in names:
        blob_path = payload_path(rel)
        plain = decrypt(KEY, read_bytes(blob_path)).decode("utf-8")
        source_rel = JA4_SOURCE if rel == JA4_MODULE else rel.replace("/", os.sep)
        original = inline_author_invite(read_text(os.path.join(ROOT, source_rel)))
        if plain != original:
            raise SystemExit("回读校验失败: " + rel)
    if not names and not boot_changed:
        return
    if "utils/farm_edge_sign.js" not in names and not boot_changed:
        return
    proc = subprocess.run(
        ["node", "-e", "const b=require('./_boot.js'); process.stdout.write(b.decrypt(require('path').join(__dirname,'utils','farm_edge_sign.js')))"],
        cwd=HERE,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.decode("utf-8", "replace") or "node 解密失败")
    js_plain = proc.stdout.decode("utf-8")
    js_orig = read_text(os.path.join(ROOT, "utils", "farm_edge_sign.js"))
    if js_plain != js_orig:
        raise SystemExit("node 解密结果和源码不一致")


if __name__ == "__main__":
    rebuild()
