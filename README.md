## 自用京东脚本,ai修改,侵权删,不上传ck只拿点助力,拿多少都写清楚了,介意的话请勿运行

## 账号必填

每个账号必须有自己的真实抓包，缺一项就打印缺什么并跳过。不能拿别的号或脚本里的值顶上。信息保存在 `cache/accounts/<pt_pin>.json`。

优先用 iPhone 抓的 Cookie。用 Stream 抓 `api.m.jd.com`，点右上角复制 cURL，整段贴进 `JD_COOKIE`。安卓环境抓的没测过，可能会有问题。

| 必填 | 抓包里的名字 | 要求 |
| --- | --- | --- |
| `pt_key`、`pt_pin` | Cookie | 登录态 |
| `user_agent` | `User-Agent` | 以 `jdapp;` 开头，并且能看出系统版本；`ep` 就在里面，整段别裁 |
| `uuid` | `uuid` | 32 到 40 位十六进制 |
| `eid_token` | `x-api-eid-token` | `jdd` 开头，长度 100–400 |
| `d_brand`、`d_model` | `d_brand`、`d_model` | 明文机型，密文丢掉 |
| `os_version` | `osVersion` | 如 `18.5` |
| `build` | `build` | 5 到 8 位数字；没抓到时自动从 UA 的 `appBuild` 取 |
| `client_version` | `clientVersion` | App 版本；没抓到时自动从 `jdapp` UA 取 |

**按脚本才需要**：`wg_token`（抓包名 `wg-sdk-token`，`jdd01` 开头、长度至少 100）。
只有 `task_wegame`（weGame）、`jd_ttgjd`（天天刮京豆）、`task_ap`（ap 活动）、
`jd_yyy`（摇一摇）、`task_finance` / `task_fish`（金融、捕鱼）这几条线会发这个字段。
没有它的账号照样能跑其它脚本，跑到这几条线时会打印「缺少 wg-sdk-token」并跳过该账号。

`screen`、`openudid` 可以不写。没有 `openudid` 时用 `uuid`。`h5st` 每次请求现签，不写进缓存。

系统版本只认这些：iOS 13、14–15、16–17、18–19、26–27，Android 10–16。iOS 27 先用 iOS 26 的 ClientHello。

`JD_COOKIE` 可以是 HAR、curl，或用分号把上面的字段串起来。`User-Agent` 里面的分号不用转义，下一段以字段名加等号开头。多账号用 `&`、换行，或下一段直接以 `;pt_key=` 接上。只填 `pt_key` 和 `pt_pin` 时，用这个账号已有的缓存，没有或不全就跳过。设备信息写入缓存后，对应的 `JD_COOKIE` 会改成 `pt_key=...;pt_pin=...;`，下次不再重复写入。没写全的账号保持原样。

```text
pt_key=xxx;pt_pin=jd_xxx;User-Agent=jdapp;iPhone;16.1.50;;;M/5.0;appBuild/171135;uuid=0123456789abcdef0123456789abcdef01234567;x-api-eid-token=jdd...;wg-sdk-token=jdd01...;d_brand=iPhone;d_model=iPhone17,2;osVersion=18.5;build=171135;clientVersion=16.1.50
```

| 脚本                    | 活动       |
| --------------------- | -------- |
| jd_beans_7days_new.py | 豆子7天统计   |
| jd_byzl.py            | 捕鱼助力     |
| jd_jdjx.py            | 京东惊喜     |
| jd_jdms.py            | 京东秒杀     |
| jd_jdfw.py            | 京东服务     |
| jd_jdpm.py            | 京豆拍卖     |
| jd_jdtj.py            | 京东特价     |
| jd_jrby.py            | 京融捕鱼     |
| jd_jrdl.py            | 金融集电量    |
| jd_jrld.py            | 金融领豆     |
| jd_jyzs.py            | 交易指数     |
| jd_kbmy.py            | 看病买药     |
| jd_klhb.py            | 快乐红包     |
| jd_lqzx.py            | 领券中心     |
| jd_lsxd.py            | 零散小豆     |
| jd_mobileFarm.py      | 东东农场     |
| jd_nczp.py            | 东东农场转盘   |
| jd_qyzxld.py          | 权益中心领豆   |
| jd_qzqd.py            | 圈子签到     |
| jd_rankVote.py        | 排行榜做任务   |
| jd_sjds.py            | 晒家大赛     |
| jd_sjg.py             | 手机馆      |
| jd_sytj.py            | 收益统计     |
| jd_sjq.py             | 手机圈      |
| jd_ttgjd.py           | 天天挂京豆    |
| jd_wmjq.py            | 外卖抢金券    |
| jd_wyqdzx.py          | 网页签到中心   |
| jd_yyy.py             | 摇一摇得京豆   |
| jd_zhf.py             | 赚话费      |
| jd_zjd.py             | 9.9包邮砸金蛋 |

各活动脚本跑完一个账号后，把这次领到的京豆和红包加进 `cache/earnings/<pt_pin>.json`。东东农场和东东农场转盘同时记领到的水滴。一个账号一个文件，同一天多次运行会累加，只保留最近三天。`jd_sytj.py` 按脚本打印这些记录，并删掉三天前的日期。

## 任务分类

同一类任务只写一份，放在 `utils`，各活动脚本只留页面、活动编号和自己独有的流程。改一类任务的做法，改对应模块就行。这些模块只是依赖，不加定时任务。加密后只在密文里，分享目录不放明文。

| 模块 | 任务类型 | 使用的脚本 |
| --- | --- | --- |
| `edge_bridge.py` | 签名浏览器：页面里签 h5st、发请求、金融签名；接口重试 | 用浏览器的全部脚本 |
| `task_common.py` | 数字和任务字段、京豆累计、打开会场、单次收益打印 | 大部分脚本 |
| `task_jxzy.py` | 京喜频道：签到，浏览会场后领豆 | 京东惊喜、交易指数、手机馆 |
| `task_interact.py` | 互动任务：多会场浏览、单会场倒计时浏览、领取和完成 | 领券中心、9.9包邮砸金蛋、外卖抢金券、京豆拍卖、京东特价 |
| `task_babel.py` | 通天塔：倒计时浏览（时长不足再补一次）、加购、品牌会员、权益中心、圈子签到 | 天天挂京豆、手机圈、晒家大赛、圈子签到 |
| `task_ap.py` | 限时浏览：开始计时、等待、完成、领奖 | 东东农场、东东农场转盘 |
| `task_farm.py` | 邀请码缓存、助力顺序 | 东东农场、捕鱼助力 |
| `task_finance.py` | 京东金融：网关签名请求、阅读任务 | 金融集电量、金融领豆，捕鱼经 `task_fish.py` 使用 |
| `task_fish.py` | 金融捕鱼游戏：打鱼、补能量、道具、邀请码和助力 | 京融捕鱼、捕鱼助力 |
| `task_browse.py` | 浏览计时：读浏览秒数、开始、等待、领奖 | 快乐红包、赚话费、排行榜做任务、网页签到中心、摇一摇得京豆 |
| `task_sign.py` | 京豆频道签到 | 京东秒杀 |
| `task_comp_click.py` | 频道楼层点商品，进度满后领豆 | 零散小豆 |
| `task_plus.py` | PLUS 盲盒、京豆商城刮卡 | 零散小豆 |
| `task_wegame.py` | 游戏页签到抽奖 | 零散小豆 |

权益中心领豆、豆子7天统计、收益统计是单独的流程，只用上面的基础模块或不用。

## 环境变量

| 名称 | 作用 |
| --- | --- |
| `JD_COOKIE` | 必填。写法见上面的「账号必填」。手机端脚本用，网页签到中心不读这个。 |
| `WEBJD_COOKIE` | 只给网页签到中心用。www.jd.com 登录后的 Cookie，里面要有 `thor`。账号名用 `pin`，没有就用 `_pst`。多账号用 `&` 或换行。不认手机端 `pt_key`。 |
| `FARM_ASSIST_TIMES` | 可选，只给东东农场用。每个号最多被助力的次数。不填则 35 次。农场每个账号只能助力一次。作者、优先 pin 和指定助力码被助力到这个数后，后面的账号改帮下一个。 |
| `FARM_ASSIST_PRIORITY` | 可选，只给东东农场用。优先被助力的 `pt_pin`，按顺序写，用 `&` 或逗号分隔。每个号助力成功一次即停，前 2 个号先助力作者，然后按这个名单，再按 `FARM_ASSIST_CODE`，它们都被助力满 `FARM_ASSIST_TIMES` 次后再随机帮其他号。 |
| `FARM_ASSIST_CODE` | 可选，只给东东农场用。直接指定被助力的邀请码，按顺序写，用 `&` 或逗号分隔。也可以贴带 `inviteCode` 的分享链接。排在优先 pin 之后、随机互助力之前。和自己缓存里的邀请码相同则跳过。 |
| `FISH_ASSIST_PRIORITY` | 可选，只给捕鱼助力用。被助力的 `pt_pin`，按顺序写，用 `&` 或逗号分隔。第一个号先助力作者，其余号按这个名单助力。邀请码缓存在 `cache/fish_invite.json`，取到时打印出来。 |
| `FISH_ASSIST_CODE` | 可选，只给捕鱼助力用。直接指定被助力的邀请码，按顺序写，用 `&` 或逗号分隔。也可以贴带 `inviteCode` 的分享链接。排在优先 pin 之后。和自己缓存里的邀请码相同则跳过。 |
| `FISH_ASSIST_TIMES` | 可选，只给捕鱼助力用。每个邀请码最多被助力成功的次数。不填则 10 次。作者、优先 pin 和指定邀请码被助力到这个数后，后面的账号不再助力它。 |
| `AUCTION_GUESS_RANDOM` | 可选，只给京豆拍卖用。设为 1 时，题目里没有正确答案就从选项里随便猜。不设就只在题目带了正确答案时才猜。 |
| `FARM_BROWSER` | 可选。Chrome / Chromium / Edge 的可执行文件路径。不填就自动找。 |
| `JD_PROXY_API` | 可选。代理提取接口的完整地址，返回一行 `ip:port`。每个账号开始时取一次。取失败只提示当前 IP 是不是不在白名单，然后不加代理直接运行。活动火爆或代理失效会重新取。连续火爆 3 次跳过当前账号。不填则直连。 |

## 环境依赖

整套脚本一起装这些就够：Python 3、`requests`、`prettytable`、Node、Chromium、Xvfb、字体、OpenSSL。

登录校验、Cookie 拆分和多账号重试在 `account_common.py`，它不是定时任务。加密后这份代码只在密文里，入口脚本由启动器加载。

签名走浏览器调试端口，不需要 `chromium-chromedriver`。排行榜领豆这一段页面关了加固，直接请求。青龙容器没有桌面，不装虚拟显示和字体时接口容易返回 405。浏览器路径可以用环境变量 `FARM_BROWSER` 指定。

在宿主机上手动安装。`容器名称` 换成自己的青龙容器，常见是 `qinglong`。仓库目录换成面板里拉下来的文件夹，一般在 `/ql/data/scripts/` 下面。

```shell
docker exec -it 容器名称 bash
```

进容器后进入仓库目录，再执行：

```shell
cd /ql/data/scripts/仓库目录
apk add --no-cache python3 py3-requests nodejs chromium xvfb ttf-freefont font-noto libssl3
python3 -m pip install --break-system-packages prettytable
```

`apk` 会装上 Python、Node、Chromium、Xvfb、字体、OpenSSL 和 `requests`。`libssl3` 提供登录校验要用的 `libcrypto` 和 `libssl`。`prettytable` 给豆子统计用，要在仓库目录里装。旧版 pip 不认识 `--break-system-packages` 时，去掉这个参数再装一次。也可以改成执行 `sh 安装依赖.sh`。

| 包 | 作用 |
| --- | --- |
| `chromium` | 浏览器 |
| `xvfb` | 虚拟显示 |
| `ttf-freefont`、`font-noto` | 字体 |
| `libssl3` | OpenSSL，登录校验用 |

拉库只给 `jd_` 开头的脚本加定时任务。黑名单里的文件不会加定时，依赖文件仍会拷下来。青龙先按最后一个参数里的后缀过滤，再按白名单和依赖决定留哪些文件。

```shell
ql repo https://github.com/addasx233/JDOOOK.git "jd_" "_payload|utils" "_payload|_boot|_aes|_key|author_invite|proxy_pool|utils" "main" "py|js|bin"
```