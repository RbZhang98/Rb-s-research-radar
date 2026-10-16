# Research Radar 2.0

在原仓库和原 Pages 地址上增量升级。此开发分支尚未上线，线上1.0保持不变：
https://rbzhang98.github.io/Rb-s-research-radar/

## 使用与验证

需要 Python 3.12+、Node.js 22+。产品运行时没有第三方依赖；fake-indexeddb 和 jsdom 只用于自动化测试。

```bash
npm ci
npm test
npm run build
npm run preview
```

访问 http://localhost:4173 。不要双击HTML，JSON需要通过HTTP读取。全部静态资源和请求使用相对路径，兼容原有 `/Rb-s-research-radar/` 子路径。

## 2.0包含什么

- 橙紫界面、基础/临床独立列表与筛选状态；分别显示新发现、累计推荐、收藏、期刊数。
- 基础14刊配置保留。直接领域相关性和可迁移机制的潜在启发性分别评分；物理词不自动变为成骨证据。
- 临床4刊独立配置与规则。作者及逐作者单位来自 Europe PMC/Crossref；可查看逐来源作者列表，缺失不推测。类型为初筛，证据不足时标记待确认。综述包括P2000，临床前研究也保留，通知/更正不进入推荐历史。
- DOI唯一的IndexedDB收藏对象；两个Radar的评分、关注原因及低评分原因分别保存，文件夹/标签/阅读状态/批注/方法/假设/问题共享。没有DOI时以来源ID代替，未来补DOI需人工确认是否同一对象。
- 完整JSON备份（schema v2）、校验预览与确认恢复；默认合并、同键覆盖，其他记录保留。原子事务确保无半份备份写入。CSV/RIS导出收藏元数据。
- 手动周报、Markdown导出、可追溯DOI和笔记，审核后生效的个人关键词，以及仅在浏览器生效的个性化排序。

## 历史迁移与分层

基准快照是原仓库提交 `39e75ebfa308085857f41c9c7a6a985a3903276e` 的 `data/articles.json`：1972条，A级16条。`backups/v1-articles-2026-10-16.json.gz` 保存未修改的完整原数据；SHA256与16篇DOI保存在 `data/lifecycle.json`。

`migrate_v2.py` 为一次性、幂等迁移，已在此分支执行。不能将新规则重评得到的16篇冒充原有16篇；保留原推荐字段 `legacyRecommendation`。旧快照准确的首次发现时间未知，因此 `firstSeenAt=null`，界面如实显示未知。

1. **原始抓取层**：公开API响应缓存 `.cache/`，不发布。依旧完整查询配置期刊与14天窗口。
2. **推荐历史层**：基础 `data/articles.json` 长期保留原16篇及后续A/B；临床 `data/clinical-articles.json` 从正式启用日积累。DOI去重索引 `basic-seen.json` / `clinical-seen.json` 不含完整题目摘要，也不会发给浏览器。
3. **临时跨领域候选**：直接相关性C但机制启发评分≥2的未清理旧文候选，可在临时列表查看最多14天。到期不保存完整元数据，收藏时在IndexedDB独立保存快照。因此不把C类全文元数据长期塞进推荐库。
4. **个人收藏层**：只在浏览器IndexedDB。公共数据清理、定时任务和迁移脚本均不接触该层；收藏快照不依赖公共文章继续存在。

旧1972条DOI全部在索引标记legacy，日常补查不会回流。需要人工重新发现旧文章时可明确执行 `--rediscover-legacy`；加入后标记historical-rediscovery，不增加今日新增。新收录但实际发表早于启用日的基础文章也标记历史重新发现。临床旧日期文章直接不加入推荐历史。

`firstSeenAt`（首次发现）、`date`（来源发表日期）、`onlineDate`（Crossref明确提供时的在线日期）、`attemptAt`（抓取尝试）是不同字段。新推荐计数以之前没有索引、发表不早于启用日并满足留存条件为准，不把重复抓取或旧文规则升级算成今日新文。

生产构建按每片最多100条生成 `dist/data/{basic,clinical}/`；清单和统计单独加载，默认只加载当前时间范围所需分片，展开列表每次20条。选择全部历史时按需加载对应分片。长期A/B推荐仍会增长，但单个在线JSON不会无限膨胀；去重索引与旧备份不包含在Pages产物内。

## 首次启用与自动更新

此分支 `lifecycle.launchDate=null`，临床正式推荐历史为0；先前45篇历史抓取只用于验证API，不会混入上线后的临床库。**不要为了测试提前修改生产启用日。**

合并到main后的第一次生产工作流运行 `scripts/activate_v2.py`，按北京时间记录启用日。之后该日保持不变。每天北京时间08:00（UTC 00:00）分别运行：

```bash
python scripts/radar.py --radar basic
python scripts/radar.py --radar clinical
```

双模块各有独立成功状态、重试、游标分页和规则。一个失败不阻止另一个尝试；状态保存后可以发布明确的失败提示，但整个运行会标为失败。`lastSuccess`只代表完整抓取成功，保存及部署结果以Actions为准。

更新工作流沿用同一个 `research-radar-pages` 并发组，不取消正在运行的任务；双抓取后只有一个提交/推送步骤。推送前fetch/rebase，有限重试；任何无法自动处理的数据冲突会停止发布，不force push。独立PR测试工作流没有写权限、不会启用临床积累或部署Pages。网页私人数据从不出现在Actions中。

无付费AI、无外部数据库、无登录和跨设备同步、无PDF下载。IndexedDB属于浏览器origin（不是某个URL目录）；建议此域名下不要运行不信任的脚本。清理网站数据、隐私模式或浏览器存储回收都可能删除本地内容，请定期导出JSON并自行保管。

## 推荐与反馈边界

规则配置在 `config/rules.json` 和 `config/clinical-rules.json`。临床不使用基础A/B筛掉研究文章。物理词命中保存独立 `inspirationScore` 和明确证据范围，不能证明适用于成骨。

个人排序：本Radar相关性×2 + 启发性 + 已人工审核关键词命中（最多3分）；不修改公共等级或期刊抓取。周报新增词至少需2篇高评分支持；降低优先级建议至少需3篇相关性低评分且无高评分支持。所有新增词须点击审核，核心检索范围从不自动缩小。当前无人工标注金标准，不声称语义准确率或临床证据质量已经验证。

## 上线、回滚及测试结果

见 [网页端升级步骤](docs/UPGRADE_WEB.md) 和 [2.0验收报告](reports/V2_ACCEPTANCE.md)。

已有工作流和网址保留；本次连接只有仓库读权限，因此未推送、未创建远程PR、未合并。需要有写权限的账号在原仓库新建分支、上传改动并创建PR。不要将私人JSON备份上传GitHub。
