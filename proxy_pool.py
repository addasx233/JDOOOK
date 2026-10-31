# -*- coding: utf-8 -*-
"""星空这类代理 API。环境变量 JD_PROXY_API 填完整取代理地址，不填则直连。"""

import os
import re
import select
import socket
import threading

import requests

API_ENV = "JD_PROXY_API"
HOT_LIMIT = 3
_IP = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")
_PROXY = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})$")


class ProxyError(RuntimeError):
    """取代理失败。"""


class HotSkip(RuntimeError):
    """连续火爆达到上限，跳过当前账号。"""


class ProxyPool:
    def __init__(self):
        self.hot = 0
        self.upstream = ""
        self.bypass = False
        self._port = 0
        self._server = None
        self._lock = threading.Lock()

    def enabled(self) -> bool:
        return bool(os.environ.get(API_ENV, "").strip())

    def begin_account(self) -> None:
        self.hot = 0
        self.bypass = False
        self.upstream = ""
        if self.enabled():
            self.refresh("获取代理")

    def on_retry(self) -> None:
        if self.enabled() and not self.bypass:
            self.refresh("重试前更换代理")

    def install_browser(self, env: dict) -> None:
        """浏览器固定走本机转发，更换上游时代理地址不用改。取代理失败则不设代理。"""
        env.pop("FARM_PROXY", None)
        if not self.enabled() or self.bypass:
            return
        self._listen()
        if not self.upstream:
            self.refresh("获取代理")
        if self.bypass or not self.upstream:
            return
        env["FARM_PROXY"] = f"http://127.0.0.1:{self._port}"

    def proxies(self):
        if not self.enabled() or self.bypass:
            return None
        self._listen()
        if not self.upstream:
            self.refresh("获取代理")
        if self.bypass or not self.upstream:
            return None
        url = f"http://127.0.0.1:{self._port}"
        return {"http": url, "https": url}

    def post(self, url, **kwargs):
        return self.request("post", url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("get", url, **kwargs)

    def request(self, method, url, **kwargs):
        def once():
            proxy = self.proxies()
            if proxy:
                kwargs["proxies"] = proxy
            else:
                kwargs.pop("proxies", None)
            return requests.request(method, url, **kwargs)

        return self.attempt(once)

    def attempt(self, func):
        last = None
        for _ in range(6):
            try:
                result = func()
            except HotSkip:
                raise
            except Exception as exc:
                last = exc
                if self.revive(exc):
                    continue
                raise
            text = _response_text(result)
            if text is not None and self.watch(text):
                continue
            return result
        if isinstance(last, Exception):
            raise last
        raise RuntimeError("请求失败")

    def watch(self, text: str) -> bool:
        """响应里出现火爆时返回 True，调用方应重试。连续 3 次则跳过账号。"""
        if "火爆" not in (text or ""):
            if text:
                self.hot = 0
            return False
        self.hot += 1
        print(f"活动火爆（连续 {self.hot}/{HOT_LIMIT}）")
        if self.hot >= HOT_LIMIT:
            raise HotSkip(f"连续火爆 {HOT_LIMIT} 次，跳过当前账号")
        if self.enabled() and not self.bypass:
            self.refresh("活动火爆，更换代理")
        return True

    def revive(self, exc: BaseException) -> bool:
        if self.bypass or not self.enabled() or not _is_dead(exc):
            return False
        print(f"代理失效：{exc}")
        self.refresh("代理失效，更换代理")
        return True

    def refresh(self, reason: str) -> None:
        api = os.environ.get(API_ENV, "").strip()
        if not api:
            return
        self._listen()
        print(reason)
        try:
            resp = requests.get(api, timeout=15)
            text = (resp.text or "").strip()
        except requests.RequestException as exc:
            text = str(exc)
        proxy = _parse_proxy(text)
        if not proxy:
            ip = _current_ip(text)
            print(f"取代理失败：{text[:200]}")
            print(f"当前 IP {ip}，是不是不在白名单？本次不加代理，直接运行")
            with self._lock:
                self.upstream = ""
            self.bypass = True
            return
        self.bypass = False
        with self._lock:
            self.upstream = proxy
        print(f"使用代理 {proxy}")

    def _listen(self) -> None:
        if self._server is not None:
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", 0))
        server.listen(64)
        self._server = server
        self._port = server.getsockname()[1]
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self) -> None:
        while True:
            try:
                client, _ = self._server.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(client,), daemon=True).start()

    def _handle(self, client: socket.socket) -> None:
        upstream = None
        try:
            client.settimeout(20)
            raw = _read_headers(client)
            if not raw:
                return
            line = raw.split(b"\r\n", 1)[0].decode("latin1", "replace")
            parts = line.split(" ")
            if len(parts) < 2:
                return
            method, target = parts[0].upper(), parts[1]
            with self._lock:
                proxy = self.upstream
            if not proxy:
                upstream = _connect_direct(method, target, raw)
                if method == "CONNECT":
                    client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                client.settimeout(None)
                upstream.settimeout(None)
                _pipe(client, upstream)
                upstream = None
                client = None
                return
            host, port = _split_proxy(proxy)
            upstream = socket.create_connection((host, port), timeout=20)
            upstream.settimeout(20)
            if method == "CONNECT":
                upstream.sendall(
                    f"CONNECT {target} HTTP/1.1\r\nHost: {target}\r\nProxy-Connection: keep-alive\r\n\r\n".encode()
                )
                reply = _read_headers(upstream)
                status = reply.split(b"\r\n", 1)[0]
                if b" 200 " not in status:
                    client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
                    return
                client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                extra = reply.split(b"\r\n\r\n", 1)[1]
                if extra:
                    client.sendall(extra)
            else:
                upstream.sendall(raw)
            client.settimeout(None)
            upstream.settimeout(None)
            _pipe(client, upstream)
            upstream = None
            client = None
        except OSError:
            try:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
            except OSError:
                pass
        finally:
            for sock in (client, upstream):
                if sock is None:
                    continue
                try:
                    sock.close()
                except OSError:
                    pass


def _response_text(result):
    if hasattr(result, "text"):
        return str(result.text or "")
    if isinstance(result, dict) and "text" in result:
        return str(result.get("text") or "")
    return None


def _parse_proxy(text: str) -> str:
    for line in text.replace("\r", "\n").split("\n"):
        line = line.strip()
        if _PROXY.match(line):
            return "http://" + line
        if line.startswith("http://") or line.startswith("https://"):
            return line
    return ""


def _connect_direct(method: str, target: str, raw: bytes) -> socket.socket:
    """没有上游代理时，本机转发改为直连目标。"""
    if method == "CONNECT":
        host, port = _split_hostport(target, 443)
        return socket.create_connection((host, port), timeout=20)
    host, port, rewritten = _rewrite_http(raw, target)
    sock = socket.create_connection((host, port), timeout=20)
    sock.sendall(rewritten)
    return sock


def _split_hostport(value: str, default_port: int):
    if value.count(":") == 1:
        host, port = value.rsplit(":", 1)
        return host, int(port)
    return value, default_port


def _rewrite_http(raw: bytes, target: str):
    rest = target.split("://", 1)[-1]
    hostport, _, path = rest.partition("/")
    path = "/" + path if path else "/"
    host, port = _split_hostport(hostport, 80)
    _, _, headers = raw.partition(b"\r\n")
    method = raw.split(b" ", 1)[0]
    return host, port, method + b" " + path.encode("latin1") + b" HTTP/1.1\r\n" + headers


def _split_proxy(proxy: str):
    hostport = proxy.split("://", 1)[-1]
    host, port = hostport.rsplit(":", 1)
    return host, int(port)


def _current_ip(fallback_text: str) -> str:
    for url in ("https://api.ipify.org", "http://ip.3322.net"):
        try:
            text = requests.get(url, timeout=8).text.strip()
        except requests.RequestException:
            continue
        matched = _IP.search(text)
        if matched:
            return matched.group(1)
    matched = _IP.search(fallback_text or "")
    return matched.group(1) if matched else "未知"


def _is_dead(exc: BaseException) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    marks = (
        "proxy",
        "timed out",
        "timeout",
        "tunnel",
        "econnreset",
        "econnrefused",
        "failed to fetch",
        "err_proxy",
        "connection aborted",
        "connection reset",
        "remotedisconnected",
        "页面请求失败",
        "max retries",
    )
    return any(mark in text for mark in marks)


def _read_headers(sock: socket.socket) -> bytes:
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        if len(data) > 65536:
            break
    return data


def _pipe(left: socket.socket, right: socket.socket) -> None:
    sockets = [left, right]
    while True:
        readable, _, _ = select.select(sockets, [], [], 120)
        if not readable:
            return
        for sock in readable:
            try:
                data = sock.recv(65536)
            except OSError:
                return
            if not data:
                return
            target = right if sock is left else left
            try:
                target.sendall(data)
            except OSError:
                return


pool = ProxyPool()
