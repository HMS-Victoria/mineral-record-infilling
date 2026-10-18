# 10月18日新增聚合证据

| 材料 | 内容与边界 |
|---|---|
| [coverage_metrics.csv](coverage_metrics.csv)、[coverage_fixed.csv](coverage_fixed.csv) | 990条六组逐折指标、924条固定名义预测的替代标签重评；数值MAE/RMSE/bias单位为百分点 |
| [magnetic_metrics.csv](magnetic_metrics.csv)、[magnetic_fixed.csv](magnetic_fixed.csv) | 660条四组逐折指标、616条固定预测重评；raw_outside_fraction是折内越界比例，不是逐格预测 |
| [tinto_complementarity.json](tinto_complementarity.json) | 63组模型联合正确性及逐类整数计数，无点身份或位置 |
| [tinto_transitions.json](tinto_transitions.json) | 252组干净到扰动的正确性计数，含36组干净恒等对照 |
| [summary.json](summary.json) | 三类空间检查的全部MAE均值、差值/判据、Tinto计数均值及最新岩性准入状态 |
| [provenance.json](provenance.json) | 来源SHA256、公开附件大小/SHA及三幅自有聚合图的原字节复制记录 |

四CSV与两计数JSON仅将源CRLF规范为LF，解析后全部字段与源一致；三幅自有图保持原字节。逐格标签、光谱/磁场特征、位置映射、预测、模型参数、原图及第三方资料不公开。逐折指标是聚合结果；共同训练与嵌套支持不增加独立样本。名义与14种预设标签扰动分开，重新拟合与固定预测重评分开；MAE按每类检查内部折等权。

运行 `python analysis/check_progress_20261018.py` 使用标准库核对全部3190行指标的矩阵与聚合、Tinto计数恒等式及原公开模型准确率、配准汇总算术、准入状态和附件SHA，绝对容差1e-12。它不读取逐格预测、光谱/磁场数组或模型，不重跑科学实验。原五个检查脚本与历史附件保持。

[Cuprite CPU结果](../../docs/cuprite-cpu-results.md) · [最新岩性准备](../../docs/cuprite-lithology-stage.md) · [Tinto错误诊断](../../docs/tinto-error-analysis.md)
