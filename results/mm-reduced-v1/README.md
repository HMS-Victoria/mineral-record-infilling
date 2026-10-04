# mm-reduced-v1：数据覆盖聚合材料

对应2026年10月3日固定27图块数据阶段。G单独通过；R覆盖未通过，联合输入审计及模型阶段未执行。没有本版本的AP或模型比较表。

| 文件 | 内容与来源 |
|---|---|
| [coverage_summary.json](coverage_summary.json) | 从G/R准入记录选择公开字段，分别保留原面积分母、门槛及状态；G/R面积浮点尾数有微小差异，未强行合并分母 |
| [R_role_missingness.csv](R_role_missingness.csv) | 五分区R原有效面积、达标格面积、缺口与状态，逐字节复制已复核的自有聚合表 |
| [角色覆盖图](../../figures/mm-reduced-v1/R_role_admission.png) | 自有聚合图的原字节副本，显示80%门槛及两个失败分区 |
| [provenance.json](provenance.json) | 附件来源标识、原/公开SHA256及引用的本地证据记录哈希；不上传内部记录本体 |

R分母是该分区全部原有效面积；分子是格内合格像元比例至少60%的格所占原有效面积。每个分区各自须达80%，不能用平均覆盖抵消失败。`valid_cells`与`qualified_cells`是网格数，不能代替面积加权比例；`shortfall_to_80pct_km2`是达到80%尚需增加的达标格有效面积。

在仓库根目录运行 `python analysis/check_multimodal_summary.py` 核对聚合算术与附件哈希。该脚本不读取原影像或逐格数组，不拟合或推理，不计算AP，也不替代原始数据处理复核。9月模型实验仍用原 `analysis/summarize.py` 和原聚合表，不放松或改写其检查规则。

[阶段报告与限制](../../docs/multimodal-data-stage.md) · [复核说明](../../docs/reproducibility.md) · [返回结果目录](../README.md)
