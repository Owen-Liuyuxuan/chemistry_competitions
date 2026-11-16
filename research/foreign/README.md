# 国外化学竞赛原件调研（2026-11-16）

`resources.json` 为来源记录；`split_hints.json` 为主线程切片入口。78 条记录已归档 PDF（包含一个完全相同文件的备用来源），共 90 条来源/状态记录。PDF 原件均在 `originals/foreign/`，哈希、页数、抓取日期及题目身份检查证据在来源记录中。

## 收集范围

- **IChO**：2020–2026 理论题与官方评分/解答；2023–2026 实验题与解答。2020–2022 为远程赛事，实验备考题不混作正式实验赛。2026 官方主办方使用 Google Drive 按单题发布，本库保留 9 道理论、3 道实验的题目与解答原始 PDF。
- **UKChO**：2020–2026 Round One 题目与评分标准，共 14 份官方 RSC PDF。共享常数/周期表、参考文献保留在整卷，逐题片段不重复收录。
- **USNCO**：2020–2026 National Parts I/II，以及 2022–2026 Part III，共 19 套题答 PDF。官方 ACS 目录明确标记 2020、2021 Part III 为 Omitted。Part I 三份补充志愿者逐题详解下载失败；2022合并PDF尾页误附Local Section答案，已排除错误配对。

## 来源可信度与纠错

- UKChO 全部从 `edu.rsc.org` 官方下载地址获得。其页面/下载有时返回 405；带浏览器 User-Agent 的公开下载请求成功。未保存错误 HTML 为 PDF。
- IChO 优先主办方原件；2020、2023–2025 解答及部分分卷来自独立教育档案 PianetaChimica。`authority=official-document-mirror` 表示官方文档的独立镜像，不表示该镜像为赛事主办方。
- USNCO 的 ACS 原始 URL 可被检索工具打开，但本机下载请求返回 403/防机器人 HTML。因此保存 `source_url` 指向 ACS，另记实际取得原件的 `mirror_url`（tylerlong/acs-exams），并检查封面年份/赛名/考试部分。
- IChO2026 官网往届列表的 2023 链接实际提供 **实验题**，已按 PDF 实际内容修正 stage。2025 链接合并理论及实验题。2024 链接为题目+空白答题册，未作为答案。
- IChO2021 `with Solution` 与 IChO2024 solutions 文件为题面中嵌入解答的批注原卷；逐题答案栏应标示“含题面的官方评分/解答”，不要声称纯答案。
- 原 `icho2025.ae` 当前返回与赛事无关的页面，未将其内容纳入来源索引。2025 资料改由后续官方主办方档案及文档镜像获取。

## 切分约定

`split_hints.json` 数组元素含 `resource_id`, `role`, `sections`。坐标原点为页面左上角，单位 PDF point；页码从 1 开始。section 中 `end_page` 为末页，`end_y` 为末页裁剪下界，**必须采用显式末界，不能只裁到下一题开始**：IChO 大量试卷的题目页与空白答卷交错排列。`page/y` 定位首次大题标题，目录中的重复项已剔除。

- IChO2020 解答与纯题面来自不同原卷；解答按独立 `Solution:` 标题切分。
- IChO2021 题目采用官方不含答案版，答案采用含答案版的同题片段。
- IChO2022 题目为 `Qn-*`，评分为 `Mn-*`。
- IChO2023 题目为 `Qn-*`，解答为 `Sn-*`。
- IChO2024 纯题面和批注答案版均按 `Qn-*` 页段切分，在 `An-*` 空白答卷开始前截止。
- IChO2023 实验整卷的 E0-1 至 E0-7（物理页15–21）是共享设备与试剂清单，分题时可从原卷查看；其不属于 Qn 题段。Q1 对应设备页15–18，Q2 对应19–20，Q3 对应21。
- USNCO三个部分现已由独立版式适配器完成486题切分，见`usnco_split_hints.json`和`scripts/usnco_hints.py`。I卷双栏及共享题干、III卷设备/答题纸/评分表使用非连续片段；2022 I卷误附Local答案及2024 III实验2缺评分均不配对。

重建提示：`python3 research/foreign/make_split_hints.py`。采集脚本保留了探索过程，`collect.py` 会重建初始清单，随后需按顺序执行 `fallback.py`, RSC 重试及 `complete_icho.py`, `finalize.py`；常规使用应由仓库主采集器读取已核验的 `resources.json` 下载，勿直接重跑探索脚本覆盖修订元数据。
