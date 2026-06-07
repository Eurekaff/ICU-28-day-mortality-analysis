# ICU 28 天死亡风险预测实验

本项目基于 MIMIC-IV 衍生结构化数据，构建 ICU 患者入科后 28 天死亡风险预测模型。实验重点包括模型比较、概率校准、缺失机制特征、特征组消融和 SHAP 解释稳定性分析。

默认预测任务：

```text
death_28d = 1 表示 ICU 入科后 28 天内死亡
death_28d = 0 表示 ICU 入科后 28 天内未死亡
```

## 目录结构

```text
.
├── run.py                         # 实验主入口
├── requirements.txt               # Python 依赖
├── src/icu_mortality/
│   ├── config.py                  # 路径、目标变量、特征列表、随机种子和实验参数
│   ├── dataset.py                 # 队列筛选与建模数据集构建
│   ├── io_utils.py                # parquet / csv 读写工具
│   ├── model_specs.py             # 候选模型与参数网格
│   ├── train_eval.py              # 基线训练、评估、曲线绘制、SHAP 解释
│   └── experiments.py             # 校准、缺失机制、消融和 SHAP 稳定性扩展实验
├── tests/
│   └── test_experiments.py
├── data/processed/                # 输入数据、建模数据集、预测结果和模型元数据
└── outputs/
    ├── tables/                    # 实验结果表格
    ├── figures/                   # ROC、PR、校准曲线、SHAP 图
    └── docs/                      # 实验方案、记录和论文文档
```

## 代码模块说明

| 功能 | 对应代码 | 说明 |
| --- | --- | --- |
| 实验入口 | `run.py` | 解析命令行参数，按需执行数据构建、训练评估和扩展实验 |
| 全局配置 | `src/icu_mortality/config.py` | 定义输入输出路径、目标变量、特征列表、随机种子、交叉验证折数、bootstrap 轮数和 SHAP 抽样量 |
| 数据构建 | `src/icu_mortality/dataset.py` | 从 `ch3_analysis_dataset.parquet` 筛选 ICU 住院时长 >= 24 小时且结局明确的记录，生成建模数据集 |
| 模型定义 | `src/icu_mortality/model_specs.py` | 定义 Logistic Regression、Decision Tree、Random Forest、ExtraTrees、HistGradientBoosting、XGBoost、LightGBM、CatBoost 及其参数网格 |
| 基线训练与评估 | `src/icu_mortality/train_eval.py` | 完成预处理、GridSearchCV、测试集评估、Bootstrap CI、ROC/PR/校准曲线、特征重要性和 SHAP 输出 |
| 扩展实验 | `src/icu_mortality/experiments.py` | 运行概率校准、missingness-aware 特征、特征组消融、风险分层和 SHAP 稳定性实验 |
| 测试 | `tests/test_experiments.py` | 覆盖扩展实验中的特征组、缺失机制、校准汇总和风险分层等逻辑 |

## 运行方式

安装依赖：

```bash
pip install -r requirements.txt
```

运行完整实验：

```bash
python run.py
```

只构建建模数据集：

```bash
python run.py --build-only
```

从已有建模数据集开始训练和评估：

```bash
python run.py --train-only
```

只运行指定模型：

```bash
python run.py --train-only --models LogisticRegression DecisionTree --bootstrap-rounds 0
```

减少 bootstrap 次数：

```bash
python run.py --train-only --bootstrap-rounds 200
```

## 实验流程

1. 从 `data/processed/ch3_analysis_dataset.parquet` 读取 MIMIC-IV 衍生数据。
2. 筛选 ICU 住院时长至少 24 小时且 `death_28d` 结局明确的记录。
3. 使用 ICU 入科后前 24 小时结构化变量构建建模数据集。
4. 采用分层训练集/测试集划分和 5 折分层交叉验证比较候选模型。
5. 在训练集选择 F1 最优阈值，并在测试集评价 AUROC、AUPRC、Accuracy、Precision、Recall、F1 和 Brier score。
6. 输出模型性能表、曲线图、混淆矩阵、Bootstrap 95% CI、SHAP 解释和最佳模型预测结果。
7. 扩展运行概率校准、缺失机制、特征组消融、风险分层和 SHAP 稳定性实验。

## 主要输出

| 类型 | 路径 |
| --- | --- |
| 建模数据集 | `data/processed/icu_28d_mortality_dataset.parquet` |
| 测试集预测 | `data/processed/icu_28d_mortality_best_model_test_predictions.csv` |
| 模型元数据 | `data/processed/icu_28d_mortality_best_model_meta.csv` |
| 数据集摘要 | `outputs/tables/icu_28d_mortality_dataset_summary.csv` |
| 模型性能 | `outputs/tables/icu_28d_mortality_table2_model_performance.csv` |
| 阈值与混淆矩阵 | `outputs/tables/icu_28d_mortality_table3_best_threshold_metrics.csv`、`outputs/tables/icu_28d_mortality_confusion_matrix.csv` |
| Bootstrap CI | `outputs/tables/icu_28d_mortality_table4_best_model_bootstrap_ci.csv` |
| 校准实验 | `outputs/tables/icu_28d_mortality_calibration_comparison.csv` |
| 缺失机制实验 | `outputs/tables/icu_28d_mortality_missingness_performance.csv` |
| 消融实验 | `outputs/tables/icu_28d_mortality_ablation_performance.csv` |
| SHAP 解释 | `outputs/tables/icu_28d_mortality_shap_importance.csv`、`outputs/figures/icu_28d_mortality_shap_importance_bar.png`、`outputs/figures/icu_28d_mortality_shap_summary.png` |
| SHAP 稳定性 | `outputs/tables/icu_28d_mortality_shap_stability.csv` |
| ROC / PR / 校准曲线 | `outputs/figures/icu_28d_mortality_roc.png`、`outputs/figures/icu_28d_mortality_pr.png`、`outputs/figures/icu_28d_mortality_calibration.png` |

## 当前结果摘要

当前完整实验纳入 51,838 条 ICU 住次记录，其中 28 天死亡 6,935 例，事件率 13.38%。

LightGBM 在测试集 AUROC 上排名第一：

- AUROC：0.874
- AUPRC：0.556
- Accuracy：87.2%
- Precision：51.8%
- Recall：55.9%
- F1：0.538

校准实验显示，排序能力和概率可靠性不是同一个问题。HistGradientBoosting + sigmoid 的 Brier score 为 0.0828；LightGBM 未校准 Brier 为 0.1361，isotonic 后降至 0.0832。

SHAP 平均绝对贡献排名靠前的变量包括 `anchor_age`、`first_careunit_CVICU`、`bun_mean`、`rr_mean` 和 `cl_first`。SHAP 是模型归因解释，不代表临床因果关系；因此实验中补充了 SHAP 稳定性分析。
