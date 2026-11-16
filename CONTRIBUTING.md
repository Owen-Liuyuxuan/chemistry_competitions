# 维护资料

1. 在research对应地区resources.json新增来源，记录实际比赛年、阶段、kind、authority、landing_url、source_url、下载状态。不能仅靠文件名判断年份和题/答。
2. 下载PDF后核验封面、正文、页数，错误HTML不能保存为PDF。保留实际mirror_url、源文件版本及访问限制，不覆盖原件。
3. `catalog/pages/`保存原生文本或OCR定位数据；`research/*/*hints.json`是可审查切分依据。页码从1开始，坐标为PDF point。双栏、共享题干、实验设备页须显式segments；有空白答题册须显式end_page/end_y。
4. 题面和答案按相同赛事、年、场次、题号核对。未获取、未发布、取消、非年度、开放项目分别标记。不得自动将combined整个文件当作每题答案。
5. 用`python3 scripts/build_catalog.py`重建切片与目录，用`python3 scripts/build_site.py`构建网页，再执行`python3 scripts/verify.py`和`node --check web/app.js`。每次调整坐标需删除对应derived文件后重建，并视觉检查边界。
6. 原图归档初赛由`scripts/collect_china.py`处理，国决来源由`scripts/collect_finals.py`处理。国外探索脚本存在中间状态，常规补档应用主来源清单，避免从探索脚本重置人工纠错记录。

本版不生成教学与解答，不将论文评析冒充比赛官方评分标准。
