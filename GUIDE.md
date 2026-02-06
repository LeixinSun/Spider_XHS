# 开发者指南（GUIDE.md）

本指南基于当前仓库源码整理，目标是让开发者快速理解整体架构、核心流程与扩展点。

## 1. 项目定位与核心流程

Spider_XHS 是一个面向小红书网页端与创作者平台的采集工具，核心特点是：

- 通过 **cookies + 签名参数（x-s/x-t/x-s-common）** 访问接口
- 以 **requests** 执行 HTTP 请求
- 将结果 **标准化、持久化为 Excel/媒体文件**
- 可选接入 **代理（proxies）**

核心链路（PC 端笔记采集）：

1. `main.py` 作为入口
2. `Data_Spider` 调用 `XHS_Apis`
3. `XHS_Apis` 通过 `xhs_utils/xhs_util.py` 生成签名与 headers
4. 调用 API → 拿到 JSON → `data_util.handle_note_info` 清洗
5. `download_note` 保存媒体与结构化文件

## 2. 目录结构与职责

```
.
├── main.py                         # 入口示例与 Data_Spider
├── apis/
│   ├── xhs_pc_apis.py              # 小红书 PC 端 API 封装
│   └── xhs_creator_apis.py         # 创作者中心 API 封装
├── xhs_utils/
│   ├── xhs_util.py                 # 签名计算、headers、请求参数生成
│   ├── xhs_creator_util.py         # 创作者中心签名与 headers
│   ├── data_util.py                # 数据清洗、保存 Excel、下载媒体
│   ├── cookie_util.py              # cookie 字符串转 dict
│   └── common_util.py              # .env 读取、输出路径初始化
├── static/                         # JS 签名代码与辅助脚本
├── requirements.txt                # Python 依赖
├── package.json                    # Node 依赖（供 execjs 执行 JS）
└── Dockerfile                      # 容器化环境
```

## 3. 运行前准备

### 3.1 依赖与环境

- Python 3.7+（Docker 镜像使用 3.10）
- Node.js 18+（Docker 镜像安装 20）

安装依赖：

```bash
pip install -r requirements.txt
npm install
```

### 3.2 配置 cookie

项目从 `.env` 读取 `COOKIES`：

```
COOKIES=你的 cookie 字符串
```

注意：

- cookie 需来自已登录的小红书页面
- cookie 中必须包含 `a1`，否则签名无法生成

初始化路径由 `xhs_utils/common_util.py` 的 `init()` 创建：

```
datas/media_datas
datas/excel_datas
```

## 4. 入口与主要功能

### 4.1 `main.py`（入口示例）

`main.py` 中定义了 `Data_Spider`，封装常用采集场景：

- `spider_note`：采集单个笔记
- `spider_some_note`：采集多个笔记 URL
- `spider_user_all_note`：采集用户全部笔记
- `spider_some_search_note`：关键词搜索并采集

这些方法最终都依赖 `XHS_Apis` 内部 API 调用。

### 4.2 `apis/xhs_pc_apis.py`（PC 端 API）

封装的主要接口包括：

- 首页频道/推荐
- 用户信息、用户笔记、收藏/点赞列表
- 搜索笔记、搜索用户
- 笔记详情、评论、未读消息等

每个接口都通过 `generate_request_params()` 生成 headers + cookies + body。

### 4.3 `apis/xhs_creator_apis.py`（创作者中心）

目前包含：

- `get_publish_note_info`
- `get_all_publish_note_info`

签名由 `xhs_creator_util.generate_xs()` 生成。

### 4.4 已覆盖的业务能力清单（代码内已实现）

PC 端接口（`xhs_pc_apis.py`）：

- 首页：频道列表、推荐流
- 用户：用户信息、用户笔记、喜欢笔记、收藏笔记
- 搜索：笔记搜索、用户搜索
- 笔记：详情、评论（一级+二级）
- 通知：未读消息、评论/@提醒、点赞/收藏、新增关注

创作者平台（`xhs_creator_apis.py`）：

- 获取已发布作品列表

说明：README 提到的“上传图集/视频”能力在本仓库 Python 代码中未看到实现，若需要请补充新接口封装。

## 5. 签名与请求机制

签名逻辑在 `xhs_utils/xhs_util.py` 中：

- JS 代码位于 `static/xhs_xs_xsc_56.js`
- 使用 `execjs` 调用 JS 生成 `x-s / x-t / x-s-common`
- `generate_request_params()` 负责组装 headers + cookies + body

关键依赖：

- `PyExecJS` 依赖 Node 运行时
- Node 包由 `package.json` 提供（如 `crypto-js`、`jsdom`）

创作者平台签名逻辑类似，但使用 `xhs_creator_xs.js`。

## 6. 数据处理与保存

`xhs_utils/data_util.py` 负责：

- `handle_note_info` / `handle_user_info` / `handle_comment_info`
- `save_to_xlsx`：使用 `openpyxl`
- `download_note`：下载图片/视频并保存结构化文件

保存结构大致如下：

```
datas/media_datas/
  昵称_用户ID/
    标题_笔记ID/
      info.json
      detail.txt
      image_0.jpg
      video.mp4
```

Excel 默认存储在：

```
datas/excel_datas/
```

## 7. 典型业务流程（建议直接改造）

以下示例均基于现有接口封装，可直接复制到新脚本中使用。为了清晰展示，示例中省略异常处理。

### 7.1 单条笔记采集

```python
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init
from xhs_utils.data_util import handle_note_info

cookies_str, _ = init()
xhs = XHS_Apis()

note_url = "https://www.xiaohongshu.com/explore/NOTE_ID?xsec_token=...&xsec_source=pc_user"
ok, msg, res = xhs.get_note_info(note_url, cookies_str)
note = handle_note_info(res["data"]["items"][0])
```

### 7.2 批量笔记采集（URL 列表）

```python
from main import Data_Spider
from xhs_utils.common_util import init

cookies_str, base_path = init()
spider = Data_Spider()

notes = [
    "https://www.xiaohongshu.com/explore/NOTE_ID?xsec_token=...&xsec_source=pc_user",
    "https://www.xiaohongshu.com/explore/NOTE_ID?xsec_token=...&xsec_source=pc_user",
]
spider.spider_some_note(notes, cookies_str, base_path, save_choice="all", excel_name="batch_demo")
```

### 7.3 用户全部笔记采集

```python
from main import Data_Spider
from xhs_utils.common_util import init

cookies_str, base_path = init()
spider = Data_Spider()

user_url = "https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=...&xsec_source=pc_user"
spider.spider_user_all_note(user_url, cookies_str, base_path, save_choice="all")
```

### 7.4 搜索 + 筛选 + 批量采集

```python
from main import Data_Spider
from xhs_utils.common_util import init

cookies_str, base_path = init()
spider = Data_Spider()

query = "榴莲"
require_num = 30
sort_type_choice = 1  # 0 综合, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
note_type = 2         # 0 不限, 1 视频, 2 图文
note_time = 2         # 0 不限, 1 一天内, 2 一周内, 3 半年内
note_range = 0        # 0 不限, 1 已看过, 2 未看过, 3 已关注
pos_distance = 0      # 0 不限, 1 同城, 2 附近

spider.spider_some_search_note(
    query,
    require_num,
    cookies_str,
    base_path,
    save_choice="excel",
    sort_type_choice=sort_type_choice,
    note_type=note_type,
    note_time=note_time,
    note_range=note_range,
    pos_distance=pos_distance,
    geo=None,
    excel_name="search_demo",
)
```

### 7.5 评论采集（一级 + 二级）

```python
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init

cookies_str, _ = init()
xhs = XHS_Apis()

note_url = "https://www.xiaohongshu.com/explore/NOTE_ID?xsec_token=...&xsec_source=pc_user"
ok, msg, comments = xhs.get_note_all_comment(note_url, cookies_str)
```

### 7.6 用户喜欢/收藏笔记

```python
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init

cookies_str, _ = init()
xhs = XHS_Apis()

user_url = "https://www.xiaohongshu.com/user/profile/USER_ID?xsec_token=...&xsec_source=pc_user"
ok, msg, likes = xhs.get_user_all_like_note_info(user_url, cookies_str)
ok, msg, collects = xhs.get_user_all_collect_note_info(user_url, cookies_str)
```

### 7.7 搜索用户

```python
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init

cookies_str, _ = init()
xhs = XHS_Apis()

ok, msg, users = xhs.search_some_user("护肤", require_num=20, cookies_str=cookies_str)
```

### 7.8 首页推荐流

```python
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init

cookies_str, _ = init()
xhs = XHS_Apis()

ok, msg, channels = xhs.get_homefeed_all_channel(cookies_str)
ok, msg, notes = xhs.get_homefeed_recommend_by_num("homefeed_recommend", 40, cookies_str)
```

### 7.9 未读消息与提醒

```python
from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import init

cookies_str, _ = init()
xhs = XHS_Apis()

ok, msg, unread = xhs.get_unread_message(cookies_str)
ok, msg, mentions = xhs.get_all_metions(cookies_str)
ok, msg, likes_collects = xhs.get_all_likesAndcollects(cookies_str)
ok, msg, new_connections = xhs.get_all_new_connections(cookies_str)
```

### 7.10 创作者平台：获取已发布作品

```python
from apis.xhs_creator_apis import XHS_Creator_Apis
from xhs_utils.common_util import init

cookies_str, _ = init()
creator = XHS_Creator_Apis()

ok, msg, notes = creator.get_all_publish_note_info(cookies_str)
```

## 8. 数据字段说明（输出结构）

### 8.1 笔记（`handle_note_info`）

字段包含：`note_id, note_url, note_type, user_id, home_url, nickname, avatar, title, desc, liked_count, collected_count, comment_count, share_count, video_cover, video_addr, image_list, tags, upload_time, ip_location`

### 8.2 用户（`handle_user_info`）

字段包含：`user_id, home_url, nickname, avatar, red_id, gender, ip_location, desc, follows, fans, interaction, tags`

### 8.3 评论（`handle_comment_info`）

字段包含：`note_id, note_url, comment_id, user_id, home_url, nickname, avatar, content, show_tags, like_count, upload_time, ip_location, pictures`

## 7. 开发与扩展建议

### 7.1 新增接口

1. 在 `xhs_pc_apis.py` 增加新方法
2. 使用 `generate_request_params()` 生成 headers/cookies
3. 在 `main.py` 或新脚本中调用
4. 按需在 `data_util.py` 增加解析与保存逻辑

### 7.2 新的保存格式

目前支持：

- media（图片/视频）
- excel（xlsx）
- all（两者）

如果需要 JSON/数据库输出，建议新增新的写入函数并在 `download_note` 或 `Data_Spider` 中调用。

### 7.3 代理接入

多数 API 方法都有 `proxies` 参数，可直接传递到 `requests`：

```python
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
```

## 8. 常见问题与注意事项

- **URL 过期**：用户/笔记链接中的 `xsec_token` 会过期，需要重新获取
- **Cookie 失效**：登录状态失效时接口返回失败
- **反爬更新**：签名 JS 可能失效，需要替换 `static/` 中脚本
- **日志**：使用 `loguru`，可在调用处补充更细粒度的日志
- **代理与证书**：部分创作者接口使用 `verify=False`，如需安全校验请自行调整

## 9. Docker 使用

可直接构建并运行：

```bash
docker build -t spider_xhs .
docker run --rm -it -e COOKIES="你的cookie" spider_xhs
```

## 10. 建议的开发入口

如果你要二次开发，推荐：

1. 先跑通 `main.py` 的单笔记采集
2. 熟悉 `xhs_pc_apis.py` 的接口封装模式
3. 理解 `xhs_util.py` 中的签名流程
4. 再扩展到搜索/批量/创作者平台功能

---

如需进一步扩展或新增功能，可以在此指南基础上补充更具体的业务层说明。
