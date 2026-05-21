# 延长 ICU 住院风险预测独立实验

本项目是一个独立的延长 ICU 住院时长（length of stay, LOS）风险预测实验，用于在阿尔茨海默病（AD）ICU 患者队列中构建建模数据集、训练多个机器学习模型，并输出表格、图像、最佳模型和论文初稿相关文件。

默认预测任务为：

```text
prolonged_icu_los = 1 if icu_los_days > 7 else 0
```

也就是：当 ICU 住院时长超过 7 天时，标记为延长 ICU 住院。

## 项目结构

- `run.py`：主入口，负责构建数据集并训练/评估模型。
- `build_dataset.py`：从分析数据集中筛选 AD ICU 队列，并生成延长 ICU 住院预测数据集。
- `train_eval.py`：模型训练、交叉验证、测试集评估、阈值分析、置信区间和图表输出。
- `model_specs.py`：定义候选模型和参数网格。
- `settings.py`：集中配置输入输出路径、标签定义、特征列表、随机种子、交叉验证折数和 bootstrap 次数。
- `write_paper_draft.py`：根据实验结果生成论文初稿文档。
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

- 建模数据集：`data/processed/prolonged_icu_los_dataset.parquet`
- 最佳模型：`data/processed/prolonged_icu_los_best_model.joblib`
- 最佳模型测试集预测：`data/processed/prolonged_icu_los_best_model_test_predictions.csv`
- 模型元数据：`data/processed/prolonged_icu_los_best_model_meta.csv`
- 结果表格：`outputs/tables/`
- 结果图像：`outputs/figures/`
- 论文初稿：`outputs/docs/`

## 环境准备

建议在项目目录中安装依赖：

```powershell
cd E:\prolonged_icu_los_experiment
pip install -r requirements.txt
```

其中 `xgboost`、`lightgbm` 和 `catboost` 属于可选增强模型依赖；如果环境中缺少这些包，对应模型会被跳过，基础的 scikit-learn 模型仍可运行。

## 运行方式

在项目目录中直接运行：

```powershell
cd E:\prolonged_icu_los_experiment
python run.py
```

也可以从 `E:\` 作为模块运行：

```powershell
python -m prolonged_icu_los_experiment.run
```

快速冒烟测试：

```powershell
python -m prolonged_icu_los_experiment.run --models LogisticRegression DecisionTree --bootstrap-rounds 0
```

只构建建模数据集，不训练模型：

```powershell
python -m prolonged_icu_los_experiment.run --build-only
```

从已有建模数据集开始训练和评估：

```powershell
python -m prolonged_icu_los_experiment.run --train-only
```

只运行指定模型：

```powershell
python -m prolonged_icu_los_experiment.run --models LogisticRegression RandomForest XGBoost
```

临时覆盖 bootstrap 次数：

```powershell
python -m prolonged_icu_los_experiment.run --bootstrap-rounds 200
```

## 使用其他输入目录

默认情况下，输入数据来自本项目的 `data/processed/`。如需临时使用其他已处理数据目录，可设置环境变量：

```powershell
$env:PROLONGED_ICU_LOS_INPUT_DIR = "E:\path\to\processed"
python -m prolonged_icu_los_experiment.run
```

## 默认队列与特征

默认队列规则：

- 仅纳入 AD ICU 患者。
- ICU 住院时长必须可用。
- ICU 住院时长至少为 24 小时。

默认特征包括：

- 人口学变量：年龄、性别、种族分组。
- ICU 入科单元：首次 ICU care unit。
- 入 ICU 后前 24 小时生命体征和实验室指标，包括心率、呼吸频率、SpO2、收缩压、舒张压、平均动脉压、白细胞、血红蛋白、血小板、电解质、肾功能、凝血、乳酸、胆红素、白蛋白和 GCS 等可用变量。

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

- `LABEL_MODE`：标签定义方式，可选 `fixed_days`、`median`、`q75`。
- `THRESHOLD_DAYS`：当 `LABEL_MODE = "fixed_days"` 时使用的 ICU 住院天数阈值，默认 7 天。
- `MIN_ICU_LOS_HOURS`：纳入队列的最短 ICU 住院时长，默认 24 小时。
- `NUMERIC_FEATURES` / `CATEGORICAL_FEATURES`：数值型和分类型特征列表。
- `TEST_SIZE`：测试集比例，默认 0.2。
- `CV_FOLDS`：交叉验证折数，默认 5。
- `BOOTSTRAP_ROUNDS`：bootstrap 轮数，默认 1000。
- `RANDOM_STATE`：随机种子，默认 42。

修改配置后重新运行 `run.py` 即可生成新的实验结果。
