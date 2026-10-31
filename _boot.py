# -*- coding: utf-8 -*-
"""运行加密后的脚本。入口文件只负责调用这里。"""

import importlib.abc
import importlib.machinery
import os
import sys

from _aes import decrypt
from _key import KEY


class _PayloadLoader(importlib.abc.Loader):
    def __init__(self, blob_path, origin):
        self.blob_path = blob_path
        self.origin = origin

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.blob_path, "rb") as handle:
            source = decrypt(KEY, handle.read()).decode("utf-8")
        module.__file__ = self.origin
        exec(compile(source, self.origin, "exec"), module.__dict__)


class _PayloadFinder(importlib.abc.MetaPathFinder):
    """分享目录里没有明文的依赖，从密文加载。已有的明文文件仍走普通导入。"""

    def find_spec(self, fullname, path, target=None):
        if path is not None or "." in fullname or fullname.startswith("_"):
            return None
        root = os.path.dirname(os.path.abspath(__file__))
        origin = os.path.join(root, fullname + ".py")
        if os.path.isfile(origin):
            return None
        blob_path = os.path.join(root, "_payload", fullname + ".py.bin")
        if not os.path.isfile(blob_path):
            return None
        loader = _PayloadLoader(blob_path, origin)
        return importlib.machinery.ModuleSpec(fullname, loader, origin=origin)


def _install_finder():
    if any(isinstance(item, _PayloadFinder) for item in sys.meta_path):
        return
    sys.meta_path.insert(0, _PayloadFinder())


_install_finder()


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
