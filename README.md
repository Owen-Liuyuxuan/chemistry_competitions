# Chemistry Atlas · 化学竞赛资料库

参照 [Physics Atlas](https://github.com/Owen-Liuyuxuan/physics_competitions) 建立的化学竞赛资料与逐题索引仓库，范围为 **2020–2026**。初版集中于资料调研、原卷归档、题答分切、主题标注和网页浏览。

[打开网页](https://owen-liuyuxuan.github.io/chemistry_competitions/) · [覆盖范围与缺口](notes/COVERAGE.md) · [维护说明](CONTRIBUTING.md)

## 初版数据

- **177条来源/状态记录**，其中140条归档记录，对应139份内容不同的PDF；重复来源保留以便溯源。
- **66份卷与任务**：59份竞赛卷、7份本科开放设计任务。
- **806道题/任务**，其中695道关联参考答案，2913个原页图像分片。
- 中国化学奥林匹克199题，IChO 75题，UKChO 39题，USNCO 486题，本科化工设计7项。

“中国高中化学竞赛复赛”在本库对应正式名称“中国化学奥林匹克（初赛）”，即省级赛/国初；2022年两场分别收录。全国决赛按年份和实际场次独立建档。

## 资料范围

- **CChO**：2020–2026初赛题目与参考答案；2020–2024两场国决理论、2025–2026国决理论，以及取得的2025/2026实验卷。
- **IChO**：2020–2026理论题答，2023–2026实验题答；2026保留官方独立单题原件，并另建整卷汇编。
- **UKChO**：2020–2026 Round 1全部题卷与评分标准。
- **USNCO**：2020–2026 National I/II、2022–2026 National III，按选择题/大题/实验分别切分。
- **本科**：全国大学生化学实验竞赛、化学实验创新设计大赛的赛事与资料调研；全国大学生化工设计竞赛七年官方开放设计任务书，作为邻近化工类别单列。

## 需要了解的数据缺口

- CChO 2020/2023国决参考答案待补；2024参考解答来自第三方解析，第二场暂仅题答合编。2025理论也为题答合编原件。
- CChO 2024实验完整卷未取得；2025实验转载只有印刷页2–3，缺首张。2025/2026实验标准答案未取得。
- 本科化学实验赛不是年赛，实际举办年为2021、2024、2026。已取得2024命题教师三篇评析，完整试卷补充附件受原站验证码限制，网页明确标注。论文不计作原卷。
- 开放设计/创新项目赛无唯一标准答案，按项目索引。IChTo面向高中生，不误归本科。
- USNCO2022全国赛I卷误附地方赛答案，60题已排除错误配对；2024实验2缺评分，保留未关联状态。

详见 [完整覆盖说明](notes/COVERAGE.md)、[本科调研](research/undergraduate/report.md)、[国外来源说明](research/foreign/README.md)。

## 网页功能

整卷档案、逐题索引、覆盖与调研三视图；支持竞赛、年份、化学主题、参考答案状态联合筛选，以及题名/关键词搜索。逐题阅读器显示原题和参考答案原图，保留原页页码、完整原卷与来源入口；支持跨页片段、双栏选择题、共享题干和不连续实验评分页。每题有可分享的hash链接。

网页无外部前端依赖，原题结构式保留原图。OCR只用于辅助定位/检索；标签为词表辅助分类，未逐题专家审校。初版没有生成解答、盲解、翻译或教学内容。

## 文件布局

```text
originals/                  原始PDF、官网原图及无损汇编
research/china/             国内来源、网页证据、切分依据
research/foreign/           国外来源、错链修正、切分依据
research/undergraduate/     本科赛事调研与缺口记录
catalog/                    整卷/逐题/来源/覆盖JSON及OCR定位缓存
  taxonomy.json             化学主题词表
  pages/                    每页原生文本或OCR及坐标
  catalog.json              网页聚合数据
  questions.json            页码、矩形、原件ID、题答关联与hash
derived/                    逐题WebP切片，保持原版图文
web/                        HTML/CSS/JS前端源文件
scripts/                    采集、定位、分切、构建与校验
notes/COVERAGE.md            收录范围、缺口与质量说明
.github/workflows/pages.yml GitHub Pages构建部署
```

## 本地构建

Python 3.10+、Node.js：

```bash
python3 -m pip install -r requirements.txt
python3 scripts/build_site.py
python3 scripts/verify.py
node --check web/app.js
python3 -m http.server 8080 --directory dist
```

浏览 `http://localhost:8080/`。`dist/`为完整静态站，可复制离线使用；由于浏览器本地fetch限制，请用静态HTTP服务打开。

重新生成目录与切片：

```bash
python3 scripts/prepare_china_hints.py
python3 scripts/usnco_hints.py
python3 scripts/build_catalog.py
python3 scripts/build_site.py
python3 scripts/verify.py
```

外文已核验切分依据位于`research/foreign/split_hints.json`；具体维护步骤见`CONTRIBUTING.md`。CI从已提交原件与切片构建，不依赖源站实时可用性。

校验覆盖全部归档hash、PDF页数、切片hash、坐标和页码、题号连续性、静态资源路径，以及已知错误答案排除规则；另完成代表性原卷/切片和网页交互的视觉抽查。这些检查不代表全部化学内容已人工审校。

## 来源与权利

竞赛试题、答案及期刊文章版权归原主办方、作者或出版社。原件及其权利声明保留，来源记录提供官方发布页、实际镜像地址、采集日期与SHA-256。第三方重排/解析与官方原件区分标注；使用及再分发须遵循相应原件要求。
