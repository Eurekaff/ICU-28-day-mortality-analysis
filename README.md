# ICU 28 天死亡风险预测实验

本项目是一个基于 MIMIC-IV 衍生分析数据集的 ICU 患者 28 天死亡风险预测实验，用于构建建模数据集、训练多个机器学习模型，并输出表格、图像、最佳模型和论文初稿。

默认预测任务为：

```text
death_28d = 1 表示 ICU 入科后 28 天内死亡
death_28d = 0 表示 ICU 入科后 28 天内未死亡
```

## 实验计划

1. 从 `ch3_analysis_dataset` 中筛选 ICU 住院时长至少 24 小时且 28 天死亡结局可用的患者。
2. 使用 ICU 入科后前 24 小时结构化变量构建建模数据集，包括人口学信息、ICU 入科单元、生命体征和实验室指标。
3. 采用分层训练集/测试集划分和分层交叉验证比较多个机器学习模型。
4. 以测试集 AUROC 选择最佳模型，并输出 AUPRC、准确率、精确率、召回率、F1、Brier score、混淆矩阵和 bootstrap 95% 置信区间。
5. 保存 ROC、PR、校准曲线、特征重要性、最佳模型、测试集预测结果和模型元数据。

## 项目结构

- `run.py`：主入口，负责构建数据集并训练/评估模型。
- `build_dataset.py`：构建 ICU 28 天死亡预测数据集。
- `train_eval.py`：模型训练、交叉验证、测试集评估、阈值分析、置信区间和图表输出。
- `model_specs.py`：定义候选模型和参数网格。
- `settings.py`：集中配置输入输出路径、目标变量、特征列表、随机种子、交叉验证折数和 bootstrap 次数。
- `write_paper_draft.py`：根据当前实验结果生成论文初稿。
- `data/processed/`：输入数据、建模数据集、最佳模型、测试集预测结果和模型元数据。
- `outputs/tables/`：数据概览、缺失率、基线表、模型性能、阈值指标、混淆矩阵、特征重要性等表格。
- `outputs/figures/`：ROC、PR 和校准曲线图。
- `outputs/docs/`：论文初稿文档。

## 输入与输出

默认输入文件：

```text
data/processed/ch3_analysis_dataset.parquet
```

如果同名 `.parquet` 文件不存在，程序会尝试读取：

```text
data/processed/ch3_analysis_dataset.csv
```

主要输出包括：

- 建模数据集：`data/processed/icu_28d_mortality_dataset.parquet`
- 最佳模型：`data/processed/icu_28d_mortality_best_model.joblib`
- 最佳模型测试集预测：`data/processed/icu_28d_mortality_best_model_test_predictions.csv`
- 模型元数据：`data/processed/icu_28d_mortality_best_model_meta.csv`
- 结果表格：`outputs/tables/icu_28d_mortality_*`
- 结果图像：`outputs/figures/icu_28d_mortality_*`
- 论文初稿：`outputs/docs/基于MIMIC-IV的ICU患者28天死亡风险预测研究_论文初稿.docx`

## 环境准备

建议在项目目录中安装依赖：

```powershell
cd <project-dir>
pip install -r requirements.txt
```

其中 `xgboost`、`lightgbm` 和 `catboost` 属于可选增强模型依赖；如果环境中缺少这些包，对应模型会被跳过，基础的 scikit-learn 模型仍可运行。

## 运行方式

在项目目录中直接运行完整实验：

```powershell
cd <project-dir>
python run.py
```

快速冒烟测试：

```powershell
python run.py --models LogisticRegression DecisionTree --bootstrap-rounds 0
```

只构建建模数据集，不训练模型：

```powershell
python run.py --build-only
```

从已有建模数据集开始训练和评估：

```powershell
python run.py --train-only
```

只运行指定模型：

```powershell
python run.py --models LogisticRegression RandomForest XGBoost
```

临时覆盖 bootstrap 次数：

```powershell
python run.py --bootstrap-rounds 200
```

重新生成论文初稿：

```powershell
python write_paper_draft.py
```

## 使用其他输入目录

默认情况下，输入数据来自本项目的 `data/processed/`。如需临时使用其他已处理数据目录，可设置环境变量：

```powershell
$env:ICU_MORTALITY_INPUT_DIR = "E:\path\to\processed"
python run.py
```

## 默认队列与特征

默认队列规则：

- ICU 住院时长必须可用。
- ICU 住院时长至少为 24 小时。
- `death_28d` 结局必须可用。

默认特征包括：

- 人口学变量：年龄、性别、种族分组。
- ICU 入科单元：首次 ICU care unit。
- 入 ICU 后前 24 小时生命体征：心率、呼吸频率、SpO2、收缩压、舒张压、平均动脉压和体温等。
- 入 ICU 后前 24 小时实验室指标：白细胞、血红蛋白、血小板、电解质、肾功能、血糖、阴离子间隙、凝血指标等。

## 候选模型

默认包含以下模型：

- `LogisticRegression`
- `DecisionTree`
- `RandomForest`
- `ExtraTrees`
- `HistGradientBoosting`
- `XGBoost`，依赖 `xgboost`
- `LightGBM`，依赖 `lightgbm`
- `CatBoost`，依赖 `catboost`

## 主要配置

常用配置集中在 `settings.py`：

- `TASK_NAME`：当前任务名，默认为 `icu_28d_mortality`。
- `TARGET`：目标变量，默认为 `death_28d`。
- `MIN_ICU_LOS_HOURS`：纳入队列的最短 ICU 住院时长，默认 24 小时。
- `NUMERIC_FEATURES` / `CATEGORICAL_FEATURES`：数值型和分类型特征列表。
- `TEST_SIZE`：测试集比例，默认 0.2。
- `CV_FOLDS`：交叉验证折数，默认 5。
- `BOOTSTRAP_ROUNDS`：bootstrap 轮数，默认 1000。
- `RANDOM_STATE`：随机种子，默认 42。

修改配置后重新运行 `run.py` 即可生成新的实验结果。
