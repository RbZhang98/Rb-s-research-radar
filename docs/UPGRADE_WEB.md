# Research Radar 2.0：通过GitHub网页升级

当前连接账户 `hkhllyzh` 对 `RbZhang98/Rb-s-research-radar` 仅有pull权限，push=false。没有修改远程main，也没有声称已创建PR。以下步骤由拥有原仓库写权限的账号执行。无需新建项目或更改Pages地址。

## 先保留稳定版本

1. 打开原仓库：https://github.com/RbZhang98/Rb-s-research-radar
2. 在main分支记录当前提交SHA（本次开发基准为39e75ebfa308085857f41c9c7a6a985a3903276e）。通过 Releases → Draft a new release → Choose a tag → 创建 `v1-before-radar-2`，Target选择当前稳定main，发布此版本标签。也可仅创建指向当前稳定提交的tag。
3. 下载当前main的ZIP作为额外代码备份。升级包内还附有原1972条数据的压缩快照；该文件不要解压后上传到网页数据目录。
4. 如果已有本地私人笔记，先在对应网页导出JSON，不要将私人备份上传仓库。本次2.0脚本不会读取或删除浏览器数据。

## 新分支上传和PR

1. 点击仓库左上分支选择框，输入 `feature/research-radar-2`，选择 **Create branch from main**。确认页头当前分支不是main。
2. 解压 `Research_Radar_2.0_updates.zip`。进入解压后的目录，上传其中的目录和文件，而不是上传ZIP或最外层包装文件夹。保留 `.github/workflows/` 路径；Windows可打开「显示隐藏的项目」。
3. 在新分支根目录点 **Add file → Upload files**。将更新包内容拖入，确认 `web/`、`scripts/`、`config/`、`data/`、`.github/`、`package.json` 等都在仓库根目录层级。若上传界面限制文件数量，分批上传，所有批次始终提交到这个开发分支。不要上传 `node_modules`、`.cache` 或个人备份。
4. 提交说明填入 `Upgrade Research Radar 2.0 with local knowledge library`。确认仍提交到feature分支。
5. 更新包包含新增及修改的文件；不要求手动处理旧dist文件的删除，正式部署会由构建脚本清空dist并重新生成，不会将旧2000条文件发到Pages。若希望仓库工作树也精确反映补丁，可在feature分支删除旧 `dist/data/articles.json`；除此不要删除数据文件。
6. 点 **Compare & pull request**，base为main、compare为feature分支。PR描述可复制 `docs/PR_DESCRIPTION.md`。检查Files changed确认没有私人数据。
7. 等待 **Test Research Radar / verify** 通过。检查数据迁移：`data/articles.json`只保留16篇；`data/clinical-articles.json`为空；`data/lifecycle.json` 的 launchDate为null。这是发布前状态，临床会在首次正式工作流开始积累。
8. 用户确认PR后再点 **Merge pull request**。不要提前手动运行feature分支的生产部署；该工作流也有main分支保护条件。

## 合并后检查

1. Actions → **Update Research Radar**：检查测试、Activate、Basic、Clinical、Persist、Build、Deploy全部结果。原仓库Settings → Pages的Source保持GitHub Actions。
2. 首次生产更新自动写入北京时间启用日；临床不补入启用日前旧文。若当天没有新文章，临床可能暂为空，这是正常结果，必须同时查看源状态是否成功。
3. 等待Deploy成功后打开原地址：https://rbzhang98.github.io/Rb-s-research-radar/
4. 用笔记本浏览器测试：基础/临床切换、修改筛选后切回、收藏、评分和笔记保存；刷新并关闭重开浏览器确认仍存在；导出JSON，在恢复预览中检查覆盖数量，再确认恢复；生成周报并导出Markdown。
5. 页面没变化时先强制刷新（Ctrl+Shift+R）。此项目没有Service Worker，不需要注销缓存服务。移动端和真实浏览器视觉QA需要在这一步完成。
6. 08:00调度允许GitHub正常延迟，也可手动 **Run workflow**。两个Radar独立状态；有失败时不要仅凭Pages仍能访问就认定更新完整成功。

## 回滚

- 对升级PR使用GitHub **Revert** 创建回滚PR，确认并合并，随后等待原工作流部署。
- 或使用先前tag对应的稳定提交，通过新的回滚提交恢复1.0源码与公共数据；不要force push覆盖历史。
- 回滚网页不会主动清理IndexedDB。2.0私人记录应提前导出并保留；1.0不提供读取这些记录的界面。
- 若回滚前已有2.0新收藏，其完整快照在本地及你导出的JSON中，不依赖公共推荐库。
