# 分组光谱融合：2026年10月15日聚合材料

只含模型×种子×固定情景×距离子集级指标与十类混淆计数，无坐标、点身份、逐点预测、模型参数权重或原始光谱。数据来源为[Afifi等的Tinto固定版本](https://rodare.hzdr.de/record/2256)，DOI10.14278/rodare.2256；原数据CC BY 4.0，原包和处理数组不镜像。

| 文件 | 内容 |
|---|---|
| [metrics.csv](metrics.csv) | 756行指标，macro-F1、mIoU、accuracy为0—1比例，支持数为点数 |
| [aggregate_records.json](aggregate_records.json) | 对应756条10×10聚合混淆矩阵、逐类F1、支持和三项指标 |
| [summary.json](summary.json) | 三阶段、三距离子集的全部均值、三种子配对差和固定判据 |
| [weight_diagnostics.json](weight_diagnostics.json) | 各种子/情景8192个预定诊断点的权重均值与点间总体标准差；无点记录 |
| [provenance.json](provenance.json) | 研究来源SHA256、公开附件大小及SHA256、自有图件原字节复制说明 |

v1为168预测×3子集=504行；continue仅计21新预测×3=63行；features为63预测×3=189行，共252个不同预测矩阵、756条子集指标。继续训练比较引用的旧C/D/A与v1一致，不重复算新增量。E0/E10/E20互有重叠，不能当作三套独立数据。

v1的early宽度70，features的early宽度74、参数匹配，不能混为同一基线。先在固定情景内计算十类macro-F1，再对三种噪声/缺失条件及三个种子等权；不堆叠混淆矩阵后替代平均，不删除缺类NA后取均值。展示macro-F1时乘100成为百分数，差乘100成为百分点。

运行 `python analysis/check_group_fusion.py` 只从公开混淆计数复算756条指标、全部均值和固定配对/判据，核对CSV、文档及附件哈希，绝对容差1e-12。既有保存预测独立复算及检查点审计是来源证据，本脚本不读取逐点数组或模型，不训练或推理。原四个检查脚本与历史附件保持。

[结果专题](../../docs/group-fusion-results.md) · [数据与准备历史](../../docs/group-fusion-preparation.md)
