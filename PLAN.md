# GitHub 热榜网页 · 技术方案

## 目标
随时浏览 GitHub 日/周/月热榜，定期自动更新并微信通知，支持回溯查看历史榜单。

## 技术决策（grill-me 确定）
- 平台：纯静态网页（HTML/CSS/JS，零构建零依赖）
- 数据管道：GitHub Actions 定时抓取 GitHub Trending → 解析存 JSON 到仓库
- 部署：GitHub Pages 托管（全免费、零运维）
- 通知：Server酱推送微信
- 功能：日/周/月榜 tab 切换 + 项目详情 + 跳转 GitHub + 历史热榜回溯

## 架构
```
GitHub Trending 页面
      ↓ 定时触发（每日/每周一/每月初）
GitHub Actions → Python 抓取+解析（HTML → JSON）
      ↓ 存仓库 data/                          ↓ 推送
data/{daily,weekly,monthly}.json           Server酱 → 微信通知
data/history/{type}/YYYY-MM-DD.json  ← 历史归档
data/history/index.json              ← 日期索引
      ↓ fetch 读取
GitHub Pages 网页
├─ 当前榜：日/周/月 tab + 项目列表 + 详情 + 跳转 GitHub
└─ 历史榜：选时段 → 选日期 → 渲染当时榜单
```

## 数据文件
```
data/
├── daily.json              # 当前日榜 Top25
├── weekly.json             # 当前周榜 Top25
├── monthly.json            # 当前月榜 Top25
└── history/
    ├── index.json          # 历史日期索引
    ├── daily/
    │   └── 2026-08-16.json # 历史日榜快照
    ├── weekly/
    │   └── 2026-08-11.json # 历史周榜快照
    └── monthly/
        └── 2026-08-01.json # 历史月榜快照
```

index.json 格式：
```json
{
  "daily": ["2026-08-16", "2026-08-15"],
  "weekly": ["2026-08-11", "2026-08-04"],
  "monthly": ["2026-08-01", "2026-07-01"]
}
```

每条记录字段：
- rank: 排名
- repo: owner/name
- description: 简介
- language: 编程语言
- stars_period: 本期新增 star
- stars_total: 总 star
- forks: fork 数
- url: GitHub 链接
- fetched_at: 抓取时间

## 历史热榜设计
- **归档**：每次抓取除覆盖当前 JSON 外，额外归档一份到 `history/{type}/{date}.json`，并更新 `index.json` 索引
- **索引**：`index.json` 记录所有可用历史日期，避免前端猜测文件名或列目录（GitHub Pages 不支持目录列表）
- **浏览**：前端"历史榜"入口 → 选时段（日/周/月）→ fetch index.json 取日期列表 → 选日期 → fetch 对应历史 JSON → 渲染当时榜单（复用列表组件）
- **保留策略**：默认无限保留（Git 仓库存储免费）；如需控制体积可保留近 365 天，旧快照由 Actions 清理

## 项目结构
```
trending-web/
├── index.html              # 单页应用
├── style.css               # 样式
├── app.js                  # 逻辑（fetch JSON、渲染、tab切换、历史浏览）
├── data/                   # Actions 抓取的 JSON
│   ├── daily.json
│   ├── weekly.json
│   ├── monthly.json
│   └── history/
│       ├── index.json
│       ├── daily/
│       ├── weekly/
│       └── monthly/
├── scripts/
│   └── fetch_trending.py   # 抓取脚本（含归档+更新索引）
└── .github/
    └── workflows/
        └── fetch.yml       # 定时任务（抓取+存JSON+归档+推送）
```

## 定时计划（三个 date range 独立更新）
- today（daily）：每天 UTC 16:00（北京 00:00）抓取 github.com/trending?since=daily
- this week（weekly）：每周一 UTC 16:00 抓取 github.com/trending?since=weekly
- this month（monthly）：每月 1 号 UTC 16:00 抓取 github.com/trending?since=monthly
- 三个 cron 各自独立触发，互不干扰；周一且月初时三个分别跑
- 每次抓取完整 25 个项目，归档历史快照 + 更新 index.json
- weekly 抓取完成后调 Server酱 推送微信通知
- 支持手动触发（workflow_dispatch）指定 date range

## 开发步骤
1. 搭网页骨架（index.html + style.css + app.js）
2. 写 Python 抓取脚本（fetch_trending.py，抓取+解析+归档+更新索引）
3. 写 GitHub Actions workflow（定时 + 存 JSON + 归档 + 调 Server酱）
4. 实现日/周/月榜 tab 切换 + 列表渲染
5. 实现项目详情展开 + 跳转 GitHub
6. 实现历史热榜浏览（选时段 → 选日期 → 渲染历史榜单）
7. 部署到 GitHub Pages
8. 配置 Server酱 sendkey 到仓库 Secrets

## 优势（对比之前的小程序方案）
- 零审核风险（无需微信审核）
- 零后端运维（无需云开发/服务器/数据库）
- 全免费（GitHub Actions 公开仓库无限额度 + Pages 免费）
- 数据有 Git 版本历史，可回溯任意时间点榜单
- 历史快照独立归档，前端直接 fetch 浏览，无需翻 Git
- 手机浏览器直接打开，无需安装任何东西

## 风险
- GitHub 页面结构变更需维护 Python 解析脚本（低频）
- GitHub Actions 免费额度：公开仓库无限，足够
- 历史快照长期积累体积增长：单文件约 30-50KB，一年约 10-15MB，可接受；必要时设保留策略清理

## 参考项目
- huchenme/github-trending-api（828⭐）— trending 解析逻辑参考
- aneasystone/github-trending（203⭐）— GitHub Actions 抓取思路参考
- hanford/trends（490⭐）— Next.js PWA trending 应用，UI 参考
