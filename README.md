## 自用京东脚本,ai修改,侵权删,不上传ck只拿点助力,拿多少都写清楚了,介意的话请勿运行

| 脚本                    | 活动             |
| --------------------- | -------------- |
| jd_jdjx.py            | 京东惊喜           |
| jd_qyzxld.py          | 权益中心领豆         |
| jd_jdtj.py            | 京东特价           |
| jd_mobileFarm.py      | 东东农场           |
| jd_nczp.py            | 东东农场转盘 |
| jd_sjds.py            | 晒家大赛           |
| jd_ttgjd.py           | 天天刮京豆          |
| jd_beans_7days_new.py | 豆子7天统计         |
| jd_rankVote.js        | 排行榜做任务         |

## 环境变量

| 名称 | 作用 |
| --- | --- |
| `JD_COOKIE` | 必填。账号 Cookie，多账号用 `&` 或换行分隔，每段包含 `pt_key` 和 `pt_pin`。 |
| `FARM_ASSIST_PRIORITY` | 可选，只给东东农场用。优先被助力的 `pt_pin`，按顺序写，用 `&` 或逗号分隔。每个号最多助力 3 次，前 2 个号先助力作者，然后按这个名单，不够再随机帮其他号。 |
| `FARM_BROWSER` | 可选。Chrome / Chromium / Edge 的可执行文件路径。不填就自动找。 |
| `JD_UA` | 可选。请求用的 User-Agent，不填用脚本内置的京东 App UA。 |
| `JD_UUID` | 可选。设备 uuid。京东惊喜、京东特价、权益中心领豆会读，不填用脚本内置值。 |
| `JD_WG_SDK_TOKEN` | 可选。东东农场、东东农场转盘的 `wg-sdk-token`，不填用脚本内置值。 |
| `JD_H5ST_CMD` | 可选。外部签名程序。stdin 一行 JSON，stdout 一行 h5st。晒家大赛、东东农场转盘、京东特价会读。 |
| `JD_EID_TOKEN` | 可选，只给晒家大赛用，作为 `x-api-eid-token`。走浏览器签名的脚本不用填。 |
| `JD_PROXY_API` | 可选。代理提取接口的完整地址，返回一行 `ip:port`。每个账号开始时取一次。取失败只提示当前 IP 是不是不在白名单，然后不加代理直接运行。活动火爆或代理失效会重新取。连续火爆 3 次跳过当前账号。不填则直连。 |

## 环境依赖

| 脚本                    | 依赖                                      |
| --------------------- | --------------------------------------- |
| jd_jdjx.py            | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_qyzxld.py          | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_jdtj.py            | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_mobileFarm.py      | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_nczp.py            | Python `requests`、Node                  |
| jd_sjds.py            | Python `requests`、Node                  |
| jd_ttgjd.py           | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_beans_7days_new.py | Python `requests`                       |
| jd_rankVote.js        | Node `axios`                            |

东东农场、京东特价、权益中心领豆、京东惊喜和天天刮京豆的签名走浏览器调试端口，不需要 `chromium-chromedriver`。排行榜领豆这一段页面关了加固，直接请求。青龙容器没有桌面，不装虚拟显示和字体时接口容易返回 405。浏览器路径可以用环境变量 `FARM_BROWSER` 指定。

在青龙容器里，进入本仓库目录执行（依赖管理里选 Linux 也是这条）：

```shell
sh 安装依赖.sh
```

脚本会安装 Chromium、Xvfb、字体、Python 的 `requests` 和 `prettytable`，以及排行榜脚本用的 `axios`。

| 包 | 作用 |
| --- | --- |
| `chromium` | 浏览器 |
| `xvfb` | 虚拟显示 |
| `ttf-freefont`、`font-noto` | 字体 |

拉库时只给 `jd_` 开头的脚本加定时任务，`utils` 只作为依赖文件：

```shell
ql repo https://github.com/addasx233/JDOOOK.git "jd_" "_payload|utils" "_payload|_boot|_aes|_key|author_invite|proxy_pool|utils" "main" "py|js|bin"
```
