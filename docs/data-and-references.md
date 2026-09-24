# 数据与参考资料

更新：2026 年 9 月 24 日。这里说明本项目实际使用的固定数据来源；数据版本不能解释为来源机构的最新发布。

## 数据来源

| 数据 | 实际用途 | 来源与版本 |
|---|---|---|
| MRDS 矿产记录 | 金、铜目标与十矿种可见上下文 | [USGS MRDS](https://mrdata.usgs.gov/mrds/)；实际读取 [M3 固定提交中的 mrds-csv.zip](https://github.com/sujaynr/M3/blob/b0c32245158b6780940d045ea23e09b4c891d60e/data/mrds-csv.zip) |
| GMNA 北美地质图 | 岩性、最小与最大地质年代 | [USGS Data Series 424](https://pubs.usgs.gov/publication/ds424)，[官方 GIS 下载](https://ngmdb.usgs.gov/gmna/gis_files/gmna_shapefiles.zip) |
| USGS 第四纪断层 | 断层存在及到断层距离 | [官方 GIS 数据包](https://earthquake.usgs.gov/static/lfs/nshm/qfaults/Qfaults_GIS.zip)，固定下载包内的数据库 |
| National Atlas 州界 | 美国本土有效域裁剪与边界面积 | [USGS 元数据](https://pubs.usgs.gov/of/2009/1150/gis/basemap/statesp020faq.htm)，[statesp020 数据包](https://pubs.usgs.gov/of/2009/1150/gis/basemap/statesp020.zip)，2005 年版本 |

MRDS 来源 ZIP 含 304,632 条记录，SHA256 为 `31be4baaa86b082787bc74989146183db21badf7157db39b3f0a6fe0b38a5477`。这个数是数据库记录数，不是独立矿床数；作者提供的 50 个处理后样例没有被用作正式训练集。

正式处理排除加工厂、检查坐标并裁剪美国本土后，保留 **249,125 条记录、215,375 个身份代理组**。同网格同矿种只计一次占据。代理组由记录 ID 与规范名称、邻近关系处理重复身份，不能代替矿床级地质核实；按连通分量形成的组可能整体跨越 1 km，名称质量也会影响分组。

GMNA 包中使用 39,828 个地质多边形；断层包中读取 112,809 个几何要素，这不是 112,809 条独立断层。投影为 EPSG:5070，网格边长 2 km，图块边长 100 km。907 个图块分为训练 502、开发验证 148、评价 50 和隔离排除 207 个。各合并评价情景共 124,795 个有效网格。

## 适用边界

**记录存在调查偏差。** MRDS 包含矿床、矿山、矿点及勘探等历史登记信息，记录覆盖和完整程度不均。数据库中没有登记不能作为经过勘查确认的负例；同一地点或矿体也可能对应多条记录。来源背景见 [USGS MRDS 系统说明](https://www.usgs.gov/publications/mineral-resources-data-system-mrds)。本任务评价的是这些记录在人工隐藏条件下的可恢复程度。

**栅格化不提高源图精度。** GMNA 是 1:5,000,000 比例尺的大陆尺度地质图；采样为 2 km 网格不代表它具备 2 km 地质细节。因此，地质消融的负结果可能与数据尺度、表示或训练适配有关，不能推断成矿不受地质控制。参见 [USGS GMNA 说明](https://www.usgs.gov/media/images/geologic-map-north-america)。

**断层与边界有明确范围。** 第四纪断层资料不是完整的成矿期构造图。本项目只取几何存在与距离，没有使用滑动速率等属性。州界使用历史概化版本，沿边界有效面积按该版本计算，不声称已采用最新行政边界。

**空间隔离不等于独立验证。** 训练与验证、评价有原定的 100 km 空间隔离，但内华达、亚利桑那和科罗拉多三个评价区已在多轮探索中查看，不能再被描述为此前完全未接触的确认性测试区。

## 文献起点与关系

Sujay Nair, Evan Austen Coleman, Sherrie Wang, Elsa Olivetti. **Masked Mineral Modeling: Learning to Model, Predict, and Uncover Mineral Deposits via Masked Spatial Interpolation.** AAAI 2026, 40(46), 39051–39060. [正式论文](https://ojs.aaai.org/index.php/AAAI/article/view/41252) · [含附录的预印本](https://arxiv.org/html/2511.09722v1) · [作者仓库](https://github.com/sujaynr/M3/)

数据与实现核对使用仓库提交 `b0c32245158b6780940d045ea23e09b4c891d60e` 作为固定参照。M3 已涉及遮蔽补全、空间留出与辅助资料，不能将这些一般设计直接作为本项目创新。本项目使用自有的小型 U-Net 与统一比较设置；数据处理、空间范围和评价机制与原论文不同，不宣称复现其分数。

本阶段的主要价值是逐步检验原先的解释：先比较邻近基线，再做地质消融，最后增加多点空间聚集基线和上下文减少实验。目前尚未建立经过充分文献比对与独立评价支持的原创方法贡献。

## 公开与再使用范围

本仓库只提供自有汇报文字、聚合结果、固定案例图和精选实现，不镜像上述原始数据库、作者处理后数据、论文全文或作者代码。案例图保留用于理解结果的栅格空间示意，不提供原始记录表、逐格数组或分组成员映射。

第三方资料的权利、使用条件与引用要求以各来源页面和随包元数据为准，公开本仓库不改变它们的条件。本仓库当前未附加统一开源许可证，也不据“可下载”推断所有上游材料具有相同再分发许可。需要重新获取数据时，应从来源链接获取并检查对应版本说明。

[返回项目首页](../README.md) · [实验方法](methods.md) · [复核说明](reproducibility.md)
