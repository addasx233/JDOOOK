# -*- coding: utf-8 -*-
"""运行加密后的脚本。入口文件只负责调用这里。"""

import os
import sys

from _aes import decrypt
from _key import KEY


def run(script_path):
    script_path = os.path.abspath(script_path)
    root = os.path.dirname(os.path.abspath(__file__))
    rel = os.path.relpath(script_path, root).replace("\\", "/")
    blob_path = os.path.join(root, "_payload", rel + ".bin")
    with open(blob_path, "rb") as handle:
        source = decrypt(KEY, handle.read()).decode("utf-8")
    code = compile(source, script_path, "exec")
    globs = {
        "__name__": "__main__",
        "__file__": script_path,
        "__package__": None,
        "__cached__": None,
    }
    sys.argv[0] = script_path
    exec(code, globs)
