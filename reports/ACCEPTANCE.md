# Research Radar 验收报告

抓取窗口：2026-09-16 — 2026-10-16（含两端）
最近完整抓取：2026-10-16T09:55:04.485897+00:00（UTC）

| 验收项 | 实际结果 |
|---|---|
| 本地生产构建 | 成功；npm run build |
| 期刊完整检索 | 14/14；每刊 Europe PMC 与可用 Crossref 接口均成功 |
| 合并真实元数据 | 1957 条 |
| A / B / C | 16 / 15 / 1926 |
| 摘要可用 / 缺失 | 864 / 1093 |
| DOI 可用 | 1957 / 1957 |
| 两来源 DOI 交集 | 629 |
| 重复抓取 | 总数不变，新增0，DOI与ID均无重复 |
| 单元测试 | 23项通过：16项Python + 7项JavaScript |
| 生产完整性 | 静态引用、DOM ID、JSON字段、期刊名、DOI唯一性、A级摘要条件通过 |
| GitHub Pages | 未部署；未指定目标仓库，无上线网址 |
| 自动更新 | 每天北京时间08:00 + 手动入口已编写；本地抓取已实测，远程调度/提交/部署未实测 |
| 浏览器 QA | 当前环境无支持的浏览器技能；未进行视觉或手机实际交互验证 |

## 逐刊结果

| 期刊 | Europe PMC | Crossref（ISSN合并） | 去重总数 | 双来源交集 | 摘要缺失 |
|---|---:|---:|---:|---:|---:|
| Nature | 200 | 422 | 423 | 199 | 327 |
| Science | 120 | 209 | 209 | 120 | 33 |
| Cell | 34 | 63 | 83 | 14 | 51 |
| Nature Medicine | 39 | 58 | 58 | 39 | 31 |
| Nature Biomedical Engineering | 7 | 25 | 25 | 7 | 18 |
| Nature Materials | 28 | 24 | 35 | 17 | 24 |
| Nature Communications | 120 | 855 | 856 | 119 | 485 |
| Cell Stem Cell | 11 | 21 | 22 | 10 | 12 |
| Cell Reports Medicine | 26 | 24 | 47 | 3 | 22 |
| Cell Reports | 82 | 151 | 154 | 79 | 81 |
| Bone Research | 4 | 6 | 6 | 4 | 0 |
| Journal of Bone and Mineral Research | 7 | 13 | 13 | 7 | 5 |
| Journal of Dental Research | 3 | 7 | 7 | 3 | 0 |
| Journal of Clinical Periodontology | 8 | 19 | 19 | 8 | 4 |

## 核验与修正

先执行 Nature、Nature Communications、Bone Research 三刊试点，日志见 pilot.log 和 pilot-status.json。初次错误 ISSN 被注册表拦截；Bone Research 的电子 ISSN 已修正为2095-6231。
Crossref 单独使用纸质 ISSN 可能缺少电子版记录，因此逐个查询全部可用 ISSN。Cell、Cell Stem Cell 电子 ISSN 的 Crossref 注册/works 接口返回404，已用 Europe PMC 的规范期刊元数据核验该电子 ISSN；Crossref 使用有效纸质 ISSN，Europe PMC 使用两者。该差异在状态页公开列出。
initial.log 与 initial-all-issns.log 保留中间修正过程；initial-final.log 是全刊通过的初始化记录；idempotence.log 是最后一次重复抓取。以 data/status.json、last-run.json 和本报告为最终结果。
来源不同步、在线与印刷日期不同、Crossref文章类型及Europe PMC收录范围不同，都会导致来源数量差异。没有将API失败或交集不足解释为无文章。

## 分级检查

规则测试覆盖泛炎症/巨噬细胞、骨髓免疫上下文、纳米材料、缺摘要和更正通知，避免这些条件单独触发A级。所有A级记录有摘要。已检查A级标题，仍需用户结合摘要判断实际研究价值；当前没有人工标注金标准，不能声称相关性准确率或召回率。
正式数据仅包含API返回的真实记录；单元测试中的合成样本不会进入data/或dist/。未下载全文或PDF，未生成中文摘要。

## 发布与持久性

工作流将data/和reports/last-run.json提交到main，git push失败会阻止部署；构建成功后上传Pages工件并部署。API部分失败也会保存错误状态，页面显示已保存历史；最终工作流标记失败。部署失败由Actions保持失败状态；JSON的lastSuccess只描述抓取，不声明发布完成。
该实现路径已完成本地测试和静态检查，只有明确GitHub目标仓库并实际运行工作流后，才能验证远程权限、分支保护和Pages部署。README包含逐步操作。

## 尚未解决

1. 没有远程部署和定时工作流实测，没有实际网址。
2. 未进行真实浏览器视觉或手机交互QA。
3. 规则分级存在语义误判和漏检，摘要缺失不能自动补写；语义接口仅预留、默认未启用。
4. 14天补查不能保证覆盖超过14天才收录的旧论文；必要时手动扩大日期窗口。
5. 无DOI记录未来补DOI时可能跨ID重复，本次全部1957条都有DOI，不受此限制影响。
