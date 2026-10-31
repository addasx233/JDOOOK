/**
 * 环境变量 JD_PROXY_API 为取代理地址。不填则直连。
 * 活动火爆或代理失效时重新取。连续火爆 3 次由调用方跳过账号。
 */
const http = require("http");
const https = require("https");

const HOT_LIMIT = 3;
let upstream = "";
let hot = 0;
let bypass = false;

function enabled() {
  return Boolean((process.env.JD_PROXY_API || "").trim());
}

function getText(url) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith("https:") ? https : http;
    const req = lib.get(url, { timeout: 15000 }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve(Buffer.concat(chunks).toString("utf8").trim()));
    });
    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("timeout"));
    });
  });
}

function parseProxy(text) {
  for (const line of String(text || "").split(/\r?\n/)) {
    const item = line.trim();
    if (/^\d{1,3}(?:\.\d{1,3}){3}:\d{2,5}$/.test(item)) return item;
  }
  return "";
}

async function currentIp(fallback) {
  try {
    const text = await getText("https://api.ipify.org");
    const matched = String(text).match(/\d{1,3}(?:\.\d{1,3}){3}/);
    if (matched) return matched[0];
  } catch (err) {
    /* 公网 IP 接口失败时用取代理接口返回里的地址 */
  }
  const matched = String(fallback || "").match(/\d{1,3}(?:\.\d{1,3}){3}/);
  return matched ? matched[0] : "未知";
}

async function refresh(reason) {
  const api = (process.env.JD_PROXY_API || "").trim();
  if (!api) return;
  console.log(reason);
  let text = "";
  try {
    text = await getText(api);
  } catch (err) {
    text = String(err && err.message ? err.message : err);
  }
  const proxy = parseProxy(text);
  if (!proxy) {
    const ip = await currentIp(text);
    console.log("取代理失败：" + text.slice(0, 200));
    console.log("当前 IP " + ip + "，是不是不在白名单？本次不加代理，直接运行");
    upstream = "";
    bypass = true;
    return;
  }
  bypass = false;
  upstream = proxy;
  console.log("使用代理 " + proxy);
}

function axiosProxy() {
  if (!upstream) return false;
  const [host, port] = upstream.split(":");
  return { host, port: Number(port), protocol: "http" };
}

function isDead(err) {
  const text = String(err && (err.message || err)).toLowerCase();
  return ["proxy", "timeout", "timed out", "econnreset", "econnrefused", "socket", "tunnel", "network"].some(
    (mark) => text.includes(mark)
  );
}

async function beginAccount() {
  hot = 0;
  bypass = false;
  upstream = "";
  if (enabled()) await refresh("获取代理");
}

function watchText(text) {
  if (!String(text || "").includes("火爆")) {
    if (text) hot = 0;
    return false;
  }
  hot += 1;
  console.log(`活动火爆（连续 ${hot}/${HOT_LIMIT}）`);
  if (hot >= HOT_LIMIT) {
    const error = new Error(`连续火爆 ${HOT_LIMIT} 次，跳过当前账号`);
    error.hotSkip = true;
    throw error;
  }
  return true;
}

async function post(axios, url, data, config) {
  let last;
  for (let i = 0; i < 6; i++) {
    const options = Object.assign({}, config);
    if (enabled() && !bypass) {
      if (!upstream) await refresh("获取代理");
      if (upstream && !bypass) options.proxy = axiosProxy();
    }
    try {
      const resp = await axios.post(url, data, options);
      const text = typeof resp.data === "string" ? resp.data : JSON.stringify(resp.data || "");
      if (watchText(text)) {
        if (enabled() && !bypass) await refresh("活动火爆，更换代理");
        continue;
      }
      return resp;
    } catch (err) {
      if (err && err.hotSkip) throw err;
      last = err;
      if (enabled() && !bypass && isDead(err)) {
        console.log("代理失效：" + (err.message || err));
        await refresh("代理失效，更换代理");
        continue;
      }
      throw err;
    }
  }
  throw last || new Error("请求失败");
}

module.exports = { beginAccount, post, enabled };
