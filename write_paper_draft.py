from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

try:
    from .settings import DOCS_DIR, FIGURES_DIR, PROCESSED_DIR, TABLES_DIR, TASK_NAME
except ImportError:
    from settings import DOCS_DIR, FIGURES_DIR, PROCESSED_DIR, TABLES_DIR, TASK_NAME


OUTPUT_NAME = "基于MIMIC-IV的ICU患者28天死亡风险预测研究_论文初稿.docx"
OUTPUT_PATH = DOCS_DIR / OUTPUT_NAME


def fmt(value: float | int | str, digits: int = 3) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text: str, bold: bool = False, size: int = 9) -> None:
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(0)
    run = para.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.7)
    section.right_margin = Cm(2.4)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(11)

    for style_name in ["Heading 1", "Heading 2", "Heading 3"]:
        style = doc.styles[style_name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True


def add_center(doc: Document, text: str, size: int = 12, bold: bool = False) -> None:
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(4)
    run = para.add_run(text)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    run.bold = bold


def add_body(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.first_line_indent = Cm(0.74)
    para.paragraph_format.line_spacing = 1.35
    para.paragraph_format.space_after = Pt(5)
    run = para.add_run(text)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(11)


def add_compact_body(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.first_line_indent = Cm(0.55)
    para.paragraph_format.line_spacing = 1.08
    para.paragraph_format.space_after = Pt(2)
    run = para.add_run(text)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(9)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    para = doc.add_heading(text, level=level)
    para.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    para.paragraph_format.space_after = Pt(5)
    for run in para.runs:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        run.font.size = Pt(15 if level == 1 else 13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)


def add_caption(doc: Document, text: str) -> None:
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(2)
    para.paragraph_format.space_after = Pt(7)
    run = para.add_run(text)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(9)


def add_table(doc: Document, df: pd.DataFrame, columns: list[str], headers: list[str]) -> None:
    table = doc.add_table(rows=1, cols=len(columns))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = True

    for idx, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[idx], header, bold=True, size=8)
        set_cell_shading(table.rows[0].cells[idx], "D9EAF7")

    for _, row in df.iterrows():
        cells = table.add_row().cells
        for idx, col in enumerate(columns):
            value = row[col]
            set_cell_text(cells[idx], fmt(value), size=8)

    doc.add_paragraph()


def jpeg_for_docx(image_path: Path) -> Path:
    out_path = DOCS_DIR / f"{image_path.stem}.jpg"
    with Image.open(image_path) as img:
        img.convert("RGB").save(out_path, "JPEG", quality=95)
    return out_path


def load_results() -> dict[str, pd.DataFrame]:
    return {
        "summary": pd.read_csv(TABLES_DIR / f"{TASK_NAME}_dataset_summary.csv"),
        "performance": pd.read_csv(TABLES_DIR / f"{TASK_NAME}_table2_model_performance.csv"),
        "ci": pd.read_csv(TABLES_DIR / f"{TASK_NAME}_table4_best_model_bootstrap_ci.csv"),
        "importance": pd.read_csv(TABLES_DIR / f"{TASK_NAME}_feature_importance.csv"),
        "confusion": pd.read_csv(TABLES_DIR / f"{TASK_NAME}_confusion_matrix.csv"),
        "meta": pd.read_csv(PROCESSED_DIR / f"{TASK_NAME}_best_model_meta.csv"),
    }


def build_docx() -> Path:
    results = load_results()
    summary = results["summary"].iloc[0]
    perf = results["performance"].copy()
    ci = results["ci"].copy()
    importance = results["importance"].head(12).copy()
    confusion = results["confusion"].copy()
    best = results["meta"].iloc[0]
    best_model = str(best["best_model"])
    best_row = perf.loc[perf["model"] == best_model].iloc[0]
    best_confusion = confusion.loc[confusion["model"] == best_model].iloc[0]

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    configure_document(doc)

    add_center(doc, "本  科  毕  业  论  文 （设 计）", size=18, bold=True)
    add_center(doc, "（主修专业）", size=14)
    doc.add_paragraph()
    add_center(doc, "基于 MIMIC-IV 的 ICU 患者 28 天死亡风险预测研究", size=16, bold=True)
    add_center(doc, "Prediction of 28-Day Mortality in ICU Patients Based on MIMIC-IV", size=12)
    doc.add_paragraph()
    for line in [
        "姓    名：方明正",
        "学    号：37220222203586",
        "学    院：信息学院",
        "专    业：软件工程",
        "年    级：2022级",
        "校内指导教师：黄晨曦   助理教授",
    ]:
        add_center(doc, line, size=12)
    doc.add_paragraph()
    add_center(doc, "二〇二六年 五月", size=12)
    doc.add_page_break()

    add_center(doc, "摘　要", size=16, bold=True)
    add_body(
        doc,
        "目的：重症监护病房（intensive care unit，ICU）患者短期死亡风险较高，早期识别高危患者有助于临床风险分层、监护强度安排和医疗资源配置。本研究基于 MIMIC-IV 衍生分析数据集，构建 ICU 患者 28 天死亡风险预测模型，并评估入 ICU 后前 24 小时结构化临床变量的预测价值。",
    )
    add_body(
        doc,
        f"方法：纳入 ICU 住院时长不少于 24 小时且 28 天死亡结局可用的患者。预测变量包括人口学信息、首次 ICU 入科单元、前 24 小时生命体征和实验室指标。采用分层训练集/测试集划分和 5 折分层交叉验证，比较 Logistic 回归、决策树、随机森林、ExtraTrees、HistGradientBoosting、XGBoost、LightGBM 和 CatBoost 等模型。主要评价指标为 AUROC，同时报告 AUPRC、准确率、精确率、召回率、F1、Brier score、混淆矩阵和 bootstrap 95% 置信区间。",
    )
    add_body(
        doc,
        f"结果：共纳入 {int(summary['n_total'])} 例 ICU 患者，其中 28 天内死亡 {int(summary['n_events'])} 例，事件率为 {100 * float(summary['event_rate']):.2f}%。{best_model} 表现最佳，测试集 AUROC 为 {fmt(best_row['test_auroc'])}，AUPRC 为 {fmt(best_row['test_auprc'])}，准确率为 {fmt(best_row['test_accuracy'])}，精确率为 {fmt(best_row['test_precision'])}，召回率为 {fmt(best_row['test_recall'])}，F1 为 {fmt(best_row['test_f1'])}。Bootstrap 分析显示最佳模型 AUROC 的 95% 置信区间为 {fmt(ci.loc[ci['metric'] == 'auroc', 'lcl_95'].iloc[0])}-{fmt(ci.loc[ci['metric'] == 'auroc', 'ucl_95'].iloc[0])}。",
    )
    add_body(
        doc,
        "结论：基于 ICU 入科早期常规结构化数据构建的机器学习模型能够较好预测 ICU 患者 28 天死亡风险。重要特征集中于年龄、氧合状态、体温、呼吸频率、心率、肾功能、炎症指标和血压状态，符合 ICU 短期预后受基础脆弱性、呼吸循环不稳定、感染炎症负荷和器官功能损伤共同影响的临床认知。",
    )
    add_body(doc, "关键词：MIMIC-IV；ICU；28 天死亡；机器学习；风险预测；LightGBM")

    add_center(doc, "Abstract", size=16, bold=True)
    add_compact_body(
        doc,
        "Objective: This study developed machine-learning models to predict 28-day mortality among intensive care unit patients using structured clinical variables from the first 24 hours after ICU admission.",
    )
    add_compact_body(
        doc,
        "Methods: ICU stays with available 28-day mortality labels and ICU length of stay of at least 24 hours were included. Demographics, first ICU care unit, vital signs, and laboratory measurements were used as predictors. Candidate models were compared using stratified train-test split and 5-fold cross-validation.",
    )
    add_compact_body(
        doc,
        f"Results: A total of {int(summary['n_total'])} ICU patients were included, including {int(summary['n_events'])} deaths within 28 days. {best_model} achieved the best performance, with a test AUROC of {fmt(best_row['test_auroc'])}, AUPRC of {fmt(best_row['test_auprc'])}, and AUROC 95% confidence interval of {fmt(ci.loc[ci['metric'] == 'auroc', 'lcl_95'].iloc[0])}-{fmt(ci.loc[ci['metric'] == 'auroc', 'ucl_95'].iloc[0])}.",
    )
    add_compact_body(
        doc,
        "Conclusion: Early structured ICU data provided strong information for 28-day mortality prediction and may support clinical risk stratification after external validation.",
    )
    add_compact_body(doc, "Key words: MIMIC-IV; ICU; 28-day mortality; machine learning; risk prediction")
    doc.add_page_break()

    add_heading(doc, "1 绪论", 1)
    add_heading(doc, "1.1 研究背景", 2)
    add_body(
        doc,
        "ICU 收治的患者通常存在急性生理紊乱、器官功能损伤和较高短期死亡风险。28 天死亡是重症医学研究中常用的短期预后结局，能够反映患者入 ICU 后早期疾病严重程度、治疗反应和整体预后。随着电子健康记录和公共数据库的发展，利用早期临床数据构建可复现的风险预测模型，已成为重症医学与医学人工智能交叉研究的重要方向。",
    )
    add_heading(doc, "1.2 研究意义", 2)
    add_body(
        doc,
        "传统 ICU 风险评分依赖固定变量和人工计算，难以充分利用电子病历中丰富的结构化数据。机器学习方法能够整合生命体征、实验室指标和基础人口学信息，捕捉变量之间的非线性关系。本研究以 MIMIC-IV 衍生数据为基础，围绕 ICU 患者 28 天死亡构建预测模型，有助于探索早期常规数据在短期预后评估中的应用价值。",
    )
    add_heading(doc, "1.3 研究内容", 2)
    add_body(
        doc,
        "本研究主要完成以下工作：第一，构建 ICU 患者 28 天死亡预测数据集；第二，比较多种机器学习模型的预测性能；第三，输出 ROC、PR、校准曲线及 bootstrap 置信区间；第四，分析最佳模型的重要特征并讨论其医学意义。",
    )

    add_heading(doc, "2 资料与方法", 1)
    add_heading(doc, "2.1 数据来源与研究对象", 2)
    add_body(
        doc,
        "本研究使用基于 MIMIC-IV 数据库整理得到的分析数据集 ch3_analysis_dataset。纳入标准为 ICU 住院时长可用、ICU 住院时长不少于 24 小时且 28 天死亡结局可用。最终纳入患者记录用于建模分析。",
    )
    add_heading(doc, "2.2 结局定义", 2)
    add_body(
        doc,
        "主要结局为 ICU 入科后 28 天内死亡，变量名为 death_28d。death_28d = 1 表示患者在 ICU 入科后 28 天内死亡，death_28d = 0 表示未在 28 天内死亡。",
    )
    add_heading(doc, "2.3 预测变量", 2)
    add_body(
        doc,
        "预测变量包括年龄、性别、种族分组、首次 ICU 入科单元，以及入 ICU 后前 24 小时生命体征和实验室指标。生命体征包括心率、呼吸频率、血氧饱和度、收缩压、舒张压、平均动脉压和体温等；实验室指标包括白细胞、血红蛋白、血小板、电解质、肾功能、血糖、阴离子间隙和凝血功能等。对于同一指标，尽可能使用 first、mean、min 和 max 等统计量表示早期状态和波动范围。",
    )
    add_heading(doc, "2.4 建模与评价方法", 2)
    add_body(
        doc,
        "数据按 8:2 分层划分训练集和测试集。数值变量采用中位数填补并标准化，分类变量采用众数填补并进行 one-hot 编码。模型训练在训练集内采用 5 折分层交叉验证和网格搜索完成。候选模型包括 Logistic 回归、决策树、随机森林、ExtraTrees、HistGradientBoosting、XGBoost、LightGBM 和 CatBoost。模型主要依据测试集 AUROC 进行比较，同时报告 AUPRC、准确率、精确率、召回率、F1、Brier score 和混淆矩阵。最佳模型通过 bootstrap 重采样估计 95% 置信区间。",
    )

    add_heading(doc, "3 结果", 1)
    add_heading(doc, "3.1 队列概况", 2)
    add_body(
        doc,
        f"本研究最终纳入 {int(summary['n_total'])} 例 ICU 患者，其中 28 天内死亡 {int(summary['n_events'])} 例，事件率为 {100 * float(summary['event_rate']):.2f}%。训练集样本量为 {int(best['n_train'])}，测试集样本量为 {int(best['n_test'])}；训练集死亡例数为 {int(best['n_train_events'])}，测试集死亡例数为 {int(best['n_test_events'])}。",
    )

    add_caption(doc, "表 1 数据集概况")
    summary_table = pd.DataFrame(
        [
            ["总样本量", int(summary["n_total"])],
            ["28 天死亡例数", int(summary["n_events"])],
            ["事件率", f"{100 * float(summary['event_rate']):.2f}%"],
            ["数值特征数", int(summary["n_numeric_features"])],
            ["分类特征数", int(summary["n_categorical_features"])],
        ],
        columns=["项目", "数值"],
    )
    add_table(doc, summary_table, ["项目", "数值"], ["项目", "数值"])

    add_heading(doc, "3.2 模型性能比较", 2)
    add_body(
        doc,
        f"不同模型在测试集上的性能见表 2。{best_model} 取得最高测试集 AUROC，为 {fmt(best_row['test_auroc'])}，AUPRC 为 {fmt(best_row['test_auprc'])}。整体来看，梯度提升类模型表现优于单棵决策树和 Logistic 回归，说明非线性模型能够更充分利用 ICU 早期结构化变量中的预测信息。",
    )
    perf_show = perf[
        [
            "model",
            "test_auroc",
            "test_auprc",
            "test_accuracy",
            "test_precision",
            "test_recall",
            "test_f1",
            "test_brier",
        ]
    ].copy()
    add_caption(doc, "表 2 不同模型在测试集上的预测性能")
    add_table(
        doc,
        perf_show,
        ["model", "test_auroc", "test_auprc", "test_accuracy", "test_precision", "test_recall", "test_f1", "test_brier"],
        ["模型", "AUROC", "AUPRC", "准确率", "精确率", "召回率", "F1", "Brier"],
    )

    add_heading(doc, "3.3 最佳模型稳定性与混淆矩阵", 2)
    add_body(
        doc,
        f"Bootstrap 结果显示，最佳模型 AUROC 均值为 {fmt(ci.loc[ci['metric'] == 'auroc', 'mean'].iloc[0])}，95% 置信区间为 {fmt(ci.loc[ci['metric'] == 'auroc', 'lcl_95'].iloc[0])}-{fmt(ci.loc[ci['metric'] == 'auroc', 'ucl_95'].iloc[0])}，提示模型区分度较稳定。在最佳 F1 阈值下，测试集真阴性 {int(best_confusion['tn'])} 例，假阳性 {int(best_confusion['fp'])} 例，假阴性 {int(best_confusion['fn'])} 例，真阳性 {int(best_confusion['tp'])} 例。",
    )
    add_caption(doc, "表 3 最佳模型 bootstrap 95% 置信区间")
    add_table(
        doc,
        ci,
        ["metric", "mean", "lcl_95", "ucl_95"],
        ["指标", "均值", "95%CI 下限", "95%CI 上限"],
    )

    for image_name, caption in [
        (f"{TASK_NAME}_roc.png", "图 1 不同模型 ROC 曲线"),
        (f"{TASK_NAME}_pr.png", "图 2 不同模型 PR 曲线"),
        (f"{TASK_NAME}_calibration.png", "图 3 最佳模型校准曲线"),
    ]:
        image_path = FIGURES_DIR / image_name
        if image_path.exists():
            doc.add_picture(str(jpeg_for_docx(image_path)), width=Inches(5.2))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_caption(doc, caption)

    add_heading(doc, "3.4 特征重要性", 2)
    add_body(
        doc,
        "最佳模型的重要特征主要包括年龄、平均 SpO2、平均体温、平均呼吸频率、平均心率、最高体温、平均 BUN、平均收缩压、最高 WBC、最低体温等。上述变量分别反映基础脆弱性、氧合状态、感染或炎症反应、呼吸循环负荷、肾功能状态和血流动力学稳定性，具有明确的临床解释基础。",
    )
    add_caption(doc, "表 4 最佳模型前 12 个重要特征")
    add_table(
        doc,
        importance,
        ["feature", "importance"],
        ["特征", "重要性"],
    )

    add_heading(doc, "4 讨论", 1)
    add_heading(doc, "4.1 主要发现", 2)
    add_body(
        doc,
        f"本研究基于 {int(summary['n_total'])} 例 ICU 患者构建 28 天死亡风险预测模型，最佳模型 {best_model} 的测试集 AUROC 达到 {fmt(best_row['test_auroc'])}，说明入 ICU 后前 24 小时的常规结构化数据包含较强的短期死亡预测信息。该结局定义明确，事件数充足，模型区分度较高，具有较好的研究稳定性和临床解释价值。",
    )
    add_heading(doc, "4.2 医学意义", 2)
    add_body(
        doc,
        "特征重要性结果与临床认知基本一致。年龄代表患者基础脆弱性和恢复储备；SpO2、呼吸频率和心率反映呼吸循环负荷；体温和 WBC 与感染、炎症和应激状态相关；BUN、肌酐和电解质反映肾功能与内环境紊乱；血压相关变量提示循环灌注状态。这些因素共同影响 ICU 患者短期预后，也解释了模型能够取得较好区分度的原因。",
    )
    add_heading(doc, "4.3 临床应用前景", 2)
    add_body(
        doc,
        "该模型可作为 ICU 入科早期风险分层工具的研究基础。对于预测为高风险的患者，临床团队可进一步结合病情评估、器官支持需求和治疗目标，优化监护频率、资源配置和医患沟通。但模型输出不应替代临床判断，而应作为辅助信息使用。",
    )
    add_heading(doc, "4.4 局限性", 2)
    add_body(
        doc,
        "本研究仍存在一定局限。第一，研究基于回顾性数据库，可能受到数据缺失、测量偏倚和未观测混杂因素影响。第二，当前模型仅使用结构化变量，尚未纳入诊断、用药、治疗措施、护理记录和时间序列动态变化等信息。第三，模型尚未进行外部验证，泛化能力仍需在其他医院或数据集中进一步评估。第四，特征重要性反映的是模型预测贡献，不能直接解释为因果关系。",
    )

    add_heading(doc, "5 结论", 1)
    add_body(
        doc,
        f"本研究构建了基于 MIMIC-IV 衍生数据集的 ICU 患者 28 天死亡风险预测模型。结果显示，{best_model} 在测试集中取得较好的预测性能，AUROC 为 {fmt(best_row['test_auroc'])}，bootstrap 95% 置信区间为 {fmt(ci.loc[ci['metric'] == 'auroc', 'lcl_95'].iloc[0])}-{fmt(ci.loc[ci['metric'] == 'auroc', 'ucl_95'].iloc[0])}。模型重要特征具有较好的医学解释性，提示入 ICU 早期常规临床数据可用于短期死亡风险分层。未来研究应进一步开展外部验证，并结合更多动态临床信息提升模型稳定性和临床可用性。",
    )

    add_heading(doc, "参考文献", 1)
    references = [
        "[1] Johnson A E W, Bulgarelli L, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset [J]. Scientific Data, 2023, 10: 1.",
        "[2] Goldberger A L, Amaral L A N, Glass L, et al. PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals [J]. Circulation, 2000, 101(23): e215-e220.",
        "[3] Harrell F E. Regression Modeling Strategies: With Applications to Linear Models, Logistic and Ordinal Regression, and Survival Analysis [M]. Springer, 2015.",
        "[4] Lundberg S M, Lee S I. A unified approach to interpreting model predictions [C]. Advances in Neural Information Processing Systems, 2017.",
        "[5] Steyerberg E W. Clinical Prediction Models: A Practical Approach to Development, Validation, and Updating [M]. Springer, 2019.",
        "[6] Rajkomar A, Dean J, Kohane I. Machine learning in medicine [J]. New England Journal of Medicine, 2019, 380(14): 1347-1358.",
        "[7] Liu V X, Escobar G J, Greene J D, et al. The expected trajectory of acute organ failure after admission to a general intensive care unit [J]. Critical Care Medicine, 2013, 41(3): 599-608.",
        "[8] Shillan D, Sterne J A C, Champneys A, Gibbison B. Use of machine learning to analyse routinely collected intensive care unit data: a systematic review [J]. Critical Care, 2019, 23: 284.",
    ]
    for ref in references:
        para = doc.add_paragraph()
        para.paragraph_format.first_line_indent = Cm(-0.5)
        para.paragraph_format.left_indent = Cm(0.5)
        para.paragraph_format.line_spacing = 1.2
        run = para.add_run(ref)
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        run.font.size = Pt(10)

    doc.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build_docx()
    print(path)
