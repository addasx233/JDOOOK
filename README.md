## 自用京东脚本,ai修改,侵权删,不上传ck只拿点助力,拿多少都写清楚了,介意的话请勿运行

## 账号必填

每个账号必须有自己的真实抓包，缺一项就打印缺什么并跳过。不能拿别的号或脚本里的值顶上。信息保存在 `cache/accounts/<pt_pin>.json`。

iPhone 用 Stream 抓 `api.m.jd.com`，点右上角复制 cURL，整段贴进 `JD_COOKIE`。安卓自己抓同一条请求。

| 必填 | 抓包里的名字 | 要求 |
| --- | --- | --- |
| `pt_key`、`pt_pin` | Cookie | 登录态 |
| `user_agent` | `User-Agent` | 以 `jdapp;` 开头，并且能看出系统版本 |
| `uuid` | `uuid` | 32 到 40 位十六进制 |
| `eid_token` | `x-api-eid-token` | `jdd` 开头，长度 100–400 |
| `wg_token` | `wg-sdk-token` | `jdd01` 开头，长度至少 100 |
| `d_brand`、`d_model` | `d_brand`、`d_model` | 明文机型，密文丢掉 |
| `os_version` | `osVersion` | 如 `18.5` |
| `build` | `build` | 5 到 8 位数字，也可以从 UA 的 `appBuild` 取 |
| `client_version` | `clientVersion` | App 版本，也可以从 `jdapp` UA 取 |

`screen`、`openudid` 可以不写。没有 `openudid` 时用 `uuid`。`h5st` 每次请求现签，不写进缓存。

系统版本只认这些：iOS 13、14–15、16–17、18–19、26，Android 10–16。

`JD_COOKIE` 可以是 HAR、curl，或用分号把上面的字段串起来。`User-Agent` 里面的分号不用转义，下一段以字段名加等号开头。多账号用 `&`、换行，或下一段直接以 `;pt_key=` 接上。只填 `pt_key` 和 `pt_pin` 时，用这个账号已有的缓存，没有或不全就跳过。

```text
pt_key=xxx;pt_pin=jd_xxx;User-Agent=jdapp;iPhone;16.1.50;;;M/5.0;appBuild/171135;uuid=0123456789abcdef0123456789abcdef01234567;x-api-eid-token=jdd...;wg-sdk-token=jdd01...;d_brand=iPhone;d_model=iPhone17,2;osVersion=18.5;build=171135;clientVersion=16.1.50
```

| 脚本                    | 活动             |
| --------------------- | -------------- |
| jd_jdjx.py            | 京东惊喜           |
| jd_jyzs.py            | 交易指数           |
| jd_klhb.py            | 快乐红包           |
| jd_sjg.py             | 手机馆            |
| jd_sjq.py             | 手机圈            |
| jd_qzqd.py            | 圈子签到           |
| jd_qyzxld.py          | 权益中心领豆         |
| jd_wyqdzx.py          | 网页签到中心         |
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
| `JD_COOKIE` | 必填。写法见上面的「账号必填」。手机端脚本用，网页签到中心不读这个。 |
| `WEBJD_COOKIE` | 只给网页签到中心用。www.jd.com 登录后的 Cookie，里面要有 `thor`。账号名用 `pin`，没有就用 `_pst`。多账号用 `&` 或换行。不认手机端 `pt_key`。 |
| `FARM_ASSIST_PRIORITY` | 可选，只给东东农场用。优先被助力的 `pt_pin`，按顺序写，用 `&` 或逗号分隔。每个号最多助力 3 次，前 2 个号先助力作者，然后按这个名单，不够再随机帮其他号。 |
| `FARM_BROWSER` | 可选。Chrome / Chromium / Edge 的可执行文件路径。不填就自动找。 |
| `JD_H5ST_CMD` | 可选。外部签名程序。stdin 一行 JSON，stdout 一行 h5st。晒家大赛、东东农场转盘、京东特价会读。 |
| `JD_PROXY_API` | 可选。代理提取接口的完整地址，返回一行 `ip:port`。每个账号开始时取一次。取失败只提示当前 IP 是不是不在白名单，然后不加代理直接运行。活动火爆或代理失效会重新取。连续火爆 3 次跳过当前账号。不填则直连。 |

## 环境依赖

| 脚本                    | 依赖                                      |
| --------------------- | --------------------------------------- |
| jd_jdjx.py            | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_jyzs.py            | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_klhb.py            | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_sjg.py             | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_sjq.py             | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_qzqd.py            | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_qyzxld.py          | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_wyqdzx.py          | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_jdtj.py            | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_mobileFarm.py      | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_nczp.py            | Python `requests`、Node                  |
| jd_sjds.py            | Python `requests`、Node                  |
| jd_ttgjd.py           | Python `requests`、Node、Chromium、Xvfb、字体 |
| jd_beans_7days_new.py | Python `requests`                       |
| jd_rankVote.js        | Node `axios`                            |

登录校验、Cookie 拆分和多账号重试在 `account_common.py`，它不是定时任务。加密后这份代码只在密文里，入口脚本由启动器加载。

东东农场、京东特价、权益中心领豆、网页签到中心、手机圈、圈子签到、京东惊喜、交易指数、快乐红包、手机馆和天天刮京豆的签名走浏览器调试端口，不需要 `chromium-chromedriver`。排行榜领豆这一段页面关了加固，直接请求。青龙容器没有桌面，不装虚拟显示和字体时接口容易返回 405。浏览器路径可以用环境变量 `FARM_BROWSER` 指定。

在宿主机上手动安装。`容器名称` 换成自己的青龙容器，常见是 `qinglong`。仓库目录换成面板里拉下来的文件夹，一般在 `/ql/data/scripts/` 下面。

```shell
docker exec -it 容器名称 bash
```

进容器后进入仓库目录，再执行：

```shell
cd /ql/data/scripts/仓库目录
apk add --no-cache python3 py3-requests nodejs chromium xvfb ttf-freefont font-noto
python3 -m pip install --break-system-packages prettytable
npm install axios
```

`apk` 会装上 Python、Node、Chromium、Xvfb、字体和 `requests`。`prettytable` 给豆子统计用，`axios` 给排行榜做任务用，要在仓库目录里装。旧版 pip 不认识 `--break-system-packages` 时，去掉这个参数再装一次。也可以改成执行 `sh 安装依赖.sh`。

| 包 | 作用 |
| --- | --- |
| `chromium` | 浏览器 |
| `xvfb` | 虚拟显示 |
| `ttf-freefont`、`font-noto` | 字体 |

拉库前改青龙配置文件，加上 `sh` 和加密脚本的 `bin`：

```shell
RepoFileExtensions="js py sh bin"
```

拉库时只给 `jd_` 开头的脚本加定时任务，`utils` 只作为依赖文件：

```shell
ql repo https://github.com/addasx233/JDOOOK.git "jd_" "_payload|utils" "_payload|_boot|_aes|_key|author_invite|proxy_pool|utils" "main" "py|js|bin"
```
