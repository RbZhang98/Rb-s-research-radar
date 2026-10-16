# Research Radar

个人科研文献追踪网站。中文界面，英文题目与来源摘要；电脑和手机响应式布局，随系统切换深浅色。无账户、数据库、全文下载、付费服务或私有 API Key。通过 GitHub Pages 固定网址阅读，GitHub Actions 每日维护数据。

## 本地运行

环境：Python 3.12+、Node.js 22+（仅用于测试与 npm 快捷命令），无须安装第三方包。

```bash
npm test
npm run build
npm run preview
```

打开 `http://localhost:4173`。不要直接双击 index.html，浏览器会阻止本地 JSON 加载。生产文件在 `dist/`，可以部署到任意静态托管服务；所有资源均使用相对路径，兼容 Pages 仓库子路径。

重新初始化指定日期：

```bash
python scripts/radar.py --start 2026-09-16 --end 2026-10-16 --journals nature,nature-communications,bone-research
python scripts/radar.py --start 2026-09-16 --end 2026-10-16
npm run build
```

日常更新：`python scripts/radar.py`。默认截止日为北京时间今天，补查从今天减14天至今天（含两端），按 DOI 和来源 ID 持续去重。首次数据已附在 `data/`，部署时应一并提交。若需要补查更久的延迟收录，可手动指定较早的 `--start`。14天窗口无法保证补到超过窗口才出现的旧文，建议偶尔执行较长窗口补查。

## 部署 GitHub Pages（尚未上线）

当前目录没有绑定远程仓库；没有创建或修改任何用户仓库。GitHub 账户连接不代表已配置 Pages 或开通定时运行。

1. 在 GitHub 新建空仓库（例如 `research-radar`）。个人免费 Pages 通常使用公开仓库；请依据账户计划选择可用的仓库可见性。不要上传任何密钥。该项目仅含公开论文元数据。
2. 将当前目录源码上传/推送到新仓库的 `main` 分支，包含 `.github/workflows/update.yml`、`data/`、`config/`、`scripts/`、`tests/`、`web/`、`package.json`。不要推送 `.cache/`。

   ```bash
   git init -b main
   git add .
   git commit -m "Build Research Radar metadata dashboard"
   git remote add origin https://github.com/YOUR_ACCOUNT/research-radar.git
   git push -u origin main
   ```

3. 仓库 Settings → Pages → Build and deployment → Source，选择 **GitHub Actions**。Settings → Actions → General 中允许 Actions 运行，并确保工作流可写入仓库；组织策略或保护分支可能阻止 bot 提交，需调整相应规则。
4. Actions → **Update Research Radar** → **Run workflow**。检查 Test、Collect、Persist、Build 和 Deploy 步骤。只有 Deploy 成功后，其 environment URL 才是实际网址。此处没有声称任何网址已上线。
5. 部署后用电脑和手机打开实际 URL，验证筛选与展开摘要；检查状态页与 Actions 日志一致。

计划任务为 `0 0 * * *`（UTC），即北京时间上午8:00。GitHub 调度可能延迟；公共仓库长期无活动时计划任务可能被停用，可在 Actions 页面重新启用。也可以手动触发。

工作流无需 Secrets。`GITHUB_TOKEN` 使用工作流内最小必需权限：contents 写入保存 JSON，pages 和 id-token 写入部署。测试失败、提交/推送失败或发布失败都会使运行失败。部分 API 失败时，仍提交新增记录及错误状态并发布历史数据，让页面说明故障；最终工作流会保持失败，不能把它当成完整成功更新。bot 使用默认 token 的数据提交不会无限触发自己的 push workflow。

自动更新的代码及本地抓取已验证；远程调度、bot 推送和 Pages 发布只有上传仓库后才能实测。目录中 `reports/ACCEPTANCE.md` 提供本次实际验收数字。

## 数据与精确期刊匹配

- `config/journals.json`：14本期刊、规范刊名、纸质/电子 ISSN。修改配置即可增刊。
- 每次运行按各 ISSN 调用 Crossref `/journals/{issn}` 核对规范刊名与 ISSN。若某个电子 ISSN 没有独立注册接口（404），使用 Europe PMC 对应 ISSN 的期刊元数据核验。各注册记录可能只列一个 ISSN，因此逐个核验；核验失败会阻止该刊检索。
- Europe PMC 的 `ISSN`、`FIRST_PDATE` 查询，`resultType=core` 获取摘要。它包含 PubMed/MEDLINE 元数据；不是独立再重复调用 PubMed。分页使用 cursorMark；再次检查响应的 ISSN。
- Crossref 对每个 ISSN 查询 `/journals/{issn}/works`，使用发布日期区间、journal-article 类型和游标分页，并再次核验响应 ISSN。查询两个 ISSN 是必要的：纸质和电子版本的存储可能分开。Cell 和 Cell Stem Cell 的电子 ISSN 无独立 Crossref 接口时，状态页明确列出，Crossref 使用有效的纸质 ISSN；Europe PMC 继续查询全部 ISSN。
- 两来源合并；DOI 去掉 URL 前缀并转为小写。无 DOI 时保留来源 ID，不进行模糊标题合并以免误并。后续 DOI 出现的无 DOI 记录暂可能残留重复（详见限制）。
- 日期优先取可用 online/print/published/issued 日期中的最早日期，再按实际日期复核窗口；精度为年/月时保存精度提示，不假装精确到日。Europe PMC 使用 firstPublicationDate。两源日期不一致时保留最早日期。期刊日期和数据库索引时点不同会造成两来源数量差异。
- 摘要仅清除 JATS/HTML 标记并解码实体，不生成或补写。缺失即标记缺失；不获取任何全文接口或 PDF。
- 来源返回的完整记录保存在版本化 JSON，包含低相关记录以便审计/检索。首页默认 A/B；切换「全部等级」可查看 C。
- 请求4次内重试、45秒超时、指数退避；缓存6小时在 `.cache/`，Actions 缓存重用。状态页区分零结果和失败。来源返回成功但索引尚不完整无法自动识别。

权威元数据文档：
- Europe PMC REST: https://europepmc.org/RestfulWebService
- Crossref API: https://api.crossref.org/swagger-ui/index.html
- 每个 ISSN 的核验 URL 及返回刊名：`data/status.json` → verification。

## 分级与可维护性

`config/rules.json` 提供词组、中文主题标签、加分项和 A/B 阈值。评分可解释，不是学术质量评价：

- A/B/C 目标词组每组最多计3项，A/B/C领域词每项3分，骨免疫/可迁移基础发现词每项1分。
- 骨组织线索与免疫词共同出现加3分，骨线索与机制词共同出现加2分。
- 达到8分且有骨/牙周上下文，才可能 A；3分起 B；其余 C。缺摘要的 A 降为 B。没有骨线索的泛技术/再生词命中标记待确认。
- 普通炎症、巨噬细胞或纳米材料单独出现不计为目标领域；没有 tFNA 特殊检索。更正/撤稿/社论通知归 C。
- 每篇提供命中词、理由、版本号；“待确认”独立于 A/B/C。测试中的合成标题只用于单元测试，从未写入正式数据。
- 规则不理解因果关系、否定或研究重点，存在漏检/误检。骨髓免疫学可能仅有间接相关性，值得人工复核。当前没有中文翻译或智能总结。

`scripts/semantic.py` 是可选语义审核接口协议，默认未启用，不提供任何强制模型依赖。将来集成时仅在 Actions 后台调用；按 DOI+摘要哈希+模型+提示词版本缓存，设条数和美元预算，凭据仅通过 Secrets，并将模型解释与来源事实分开保存。当前不调用任何模型、不产生模型费用。

## 目录

```text
config/        期刊和规则配置
scripts/       抓取、标准化、合并、构建及语义接口协议
web/           原生 ES modules + CSS 静态应用（无打包依赖）
data/          版本化历史 JSON 与最近抓取状态
reports/       初始抓取、三刊验证与验收报告
tests/         后台与浏览器筛选逻辑测试
.github/       每日抓取、提交、构建和 Pages 发布
```

静态方案功能等同于轻量 Vite 网站，无运行时 CDN、第三方字体或浏览器私有凭据。筛选在浏览器完成，每次最多新增渲染20张卡片。数据先加载完整 JSON，若未来达到数万条可按年份分片；本次规模无须服务器数据库。

## 当前限制

- 尚未绑定部署仓库；没有上线网址。远程 Actions 调度/部署未测试。
- 当前环境未提供支持的浏览器 QA，已完成构建、数据完整性及 JS/Python 测试；真实浏览器视觉和手机触控验证仍待部署后执行。
- 关键词分级不等价于人工语义审核，C级中可能存在可迁移发现；缺摘要较多时须点原文确认。
- 无 DOI 来源记录未来补 DOI 时不能自动跨 ID 合并；两源都无摘要时无法可靠识别内容。Crossref 和 Europe PMC 不保证实时或完整收录。
- `lastSuccess` 只指完整抓取成功，不代表保存/发布成功；提交与发布以 Actions 的结果为准。站点显示旧数据时会在48小时后提示过期。部分抓取成功不会覆盖最近完整成功时间。
