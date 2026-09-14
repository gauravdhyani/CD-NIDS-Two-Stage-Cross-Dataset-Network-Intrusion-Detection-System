# CD-NIDS: Cross-Dataset Two-Stage Network Intrusion Detection System

> **Train on CICIDS2017, validate on CICIDS2017, and externally test on CSE-CIC-IDS2018**

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](#technology-stack)
[![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Scikit--learn-F7931E)](#technology-stack)
[![Models](https://img.shields.io/badge/Models-XGBoost%20%7C%20LightGBM-2F855A)](#models-evaluated)
[![Deployment](https://img.shields.io/badge/Export-Joblib%20%7C%20ONNX-5C2D91)](#model-export-and-deployment-artifacts)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)
[![Status](https://img.shields.io/badge/Status-Research%20Prototype-yellow)](#production-readiness)

CD-NIDS is a large-scale machine-learning research pipeline for evaluating whether a two-stage Network Intrusion Detection System trained on one benchmark dataset can generalize to traffic collected in another year and environment.

The system first detects whether a network flow is benign or malicious, then classifies malicious flows into normalized attack families. Its primary contribution is a rigorous comparison between **same-dataset validation performance** and **cross-dataset external performance**.

> [!IMPORTANT]
> The project is an academic and defensive-security prototype. It is not currently a production-ready IDS. The external results reveal substantial dataset shift, model-specific generalization failure, and an operational tradeoff between attack recall and false-alert volume.

---

## Key Results

| Evaluation setting | Best reported model | Primary metric | Result |
|---|---|---:|---:|
| CICIDS2017 binary validation | Decision Tree | F1-score | **0.9918** |
| CSE-CIC-IDS2018 binary test | Logistic Regression | F1-score | **0.7919** |
| CSE-CIC-IDS2018 binary test | Logistic Regression | Recall | **0.9242** |
| CSE-CIC-IDS2018 binary test | Logistic Regression | False-positive rate | **0.4063** |
| CSE-CIC-IDS2018 multiclass test | LightGBM | Macro F1-score | **0.2501** |
| Best transferred attack family | LightGBM on BOT | F1-score | **0.97** |

### Central finding

The model with the strongest CICIDS2017 validation performance was not the strongest cross-dataset model. The Decision Tree's binary F1-score declined from **0.9918** on CICIDS2017 validation to **0.2490** on CSE-CIC-IDS2018, an absolute decrease of **0.7428**.

Logistic Regression generalized better by binary F1 and recall, but its **40.63% false-positive rate** would create a substantial alert burden. Multiclass generalization remained weak, with the best reported macro F1-score reaching only **0.2501**.

---

## Contents

- [Project Overview](#project-overview)
- [Research Aim](#research-aim)
- [Motivation](#motivation)
- [Why a Two-Stage IDS?](#why-a-two-stage-ids)
- [System Architecture](#system-architecture)
- [Datasets](#datasets)
- [Attack Label Normalization](#attack-label-normalization)
- [Methodology](#methodology)
- [Exploratory Data Analysis](#exploratory-data-analysis)
- [Stage 1: Binary Attack Detection](#stage-1-binary-attack-detection)
- [Stage 2: Multiclass Attack Classification](#stage-2-multiclass-attack-classification)
- [Model Comparison Summary](#model-comparison-summary)
- [Principal Findings](#principal-findings)
- [Achievements](#achievements)
- [Effectiveness Assessment](#effectiveness-assessment)
- [Threats to Validity](#threats-to-validity-and-implementation-limitations)
- [Model Export and Deployment](#model-export-and-deployment-artifacts)
- [Recommended Improvements](#recommended-improvements)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Running the Experiment](#running-the-experiment)
- [Reproducibility](#reproducibility-parameters)
- [Conclusion](#conclusion)
- [License](#license)

---

## Project Overview

This project develops and evaluates a **two-stage machine-learning Network Intrusion Detection System (NIDS)** for detecting malicious network traffic and identifying attack categories.

Unlike conventional intrusion-detection studies that train and test models on random partitions of the same dataset, this work performs a more challenging **cross-dataset evaluation**:

```text
Training dataset    : CICIDS2017
Validation dataset  : CICIDS2017
External test set   : CSE-CIC-IDS2018
```

The principal objective is to determine whether models trained on network traffic collected in one environment and year can generalize to traffic collected under different conditions.

The proposed system contains two stages:

1. **Stage 1: Binary Attack Detection**  
   Classifies each network flow as **Benign** or **Attack**.

2. **Stage 2: Multiclass Attack Classification**  
   Classifies malicious flows into a normalized cyberattack family.

The results demonstrate that excellent same-dataset validation performance does not necessarily translate into reliable external performance. This generalization gap is the central finding of the project.

---

## Research Aim

The aim of this project is to design, implement, and assess a scalable intrusion-detection pipeline that can:

- distinguish benign network traffic from malicious activity;
- identify the attack family associated with a malicious flow;
- process millions of network-flow records efficiently;
- reconcile schema and label differences between CICIDS2017 and CSE-CIC-IDS2018;
- compare linear, tree-based, and gradient-boosting models;
- quantify the difference between in-domain validation and cross-dataset testing;
- export trained models and preprocessing artifacts for future inference experiments.

The project addresses the following research question:

> **To what extent can a Network Intrusion Detection System trained on CICIDS2017 generalize to unseen network traffic from CSE-CIC-IDS2018?**

---

## Motivation

Machine-learning intrusion-detection models often report very high accuracy when training and testing are performed on random subsets of the same dataset. However, such evaluation may overestimate operational effectiveness because both partitions share similar:

- traffic-generation procedures;
- network configurations;
- feature distributions;
- attack implementations;
- class frequencies;
- collection tools;
- temporal and dataset-specific artifacts.

A practical NIDS must remain effective when the deployment environment differs from the training environment. Cross-dataset evaluation therefore provides a stronger assessment of robustness than a conventional random train-test split.

This project uses CICIDS2017 as the source domain and CSE-CIC-IDS2018 as the external target domain. The resulting performance difference provides evidence of the system's ability, or inability, to generalize across datasets.

---

## Why a Two-Stage IDS?

Direct multiclass classification requires one model to distinguish benign flows from several attack families simultaneously. This becomes difficult when benign traffic dominates the dataset and some attacks have very few examples.

The proposed two-stage architecture decomposes the task into two related problems.

## Stage 1: Binary Detection

The first stage performs rapid filtering:

```text
Benign -> 0
Attack -> 1
```

Its purpose is to identify suspicious traffic while minimizing missed attacks and unnecessary alerts.

## Stage 2: Attack Classification

The second stage processes attack traffic and predicts the corresponding attack family:

```text
BOT
BRUTEFORCE
DDOS
DOS
HEARTBLEED
INFILTRATION
PORTSCAN
WEBATTACK
```

## Expected Advantages

A two-stage design may provide:

- simpler decision boundaries at each stage;
- efficient filtering of benign traffic;
- improved focus on attack-family discrimination;
- separate threshold optimization for detection and attribution;
- a modular architecture suitable for future streaming deployment.

## Current Experimental Scope

The two stages are trained and evaluated separately in the current notebook. Stage 2 is tested using flows whose ground-truth label is already known to be malicious.

Therefore, the current results do **not** yet represent the performance of a complete operational cascade. An end-to-end evaluation must pass Stage 1 predictions into Stage 2 and account for both:

- attacks missed by Stage 1;
- benign flows incorrectly forwarded to Stage 2.

---

## System Architecture

```text
Raw Network Traffic
        |
        v
Flow Extraction using CICFlowMeter
        |
        v
Schema Alignment and Label Normalization
        |
        v
Numeric Cleaning and Missing-Value Handling
        |
        v
Feature Scaling
        |
        v
Variance Threshold and ANOVA Selection
        |
        v
Principal Component Analysis
        |
        v
Stage 1: Binary Attack Detector
        |
        +----------------------+
        |                      |
     Benign                  Attack
                               |
                               v
                 Stage 2: Attack Classifier
                               |
                               v
                    Predicted Attack Family
                               |
                               v
                         Security Alert
```

---

## Datasets

Two benchmark intrusion-detection datasets are used.

## CICIDS2017

CICIDS2017 is used for model development, feature selection, training, cross-validation, and internal validation.

### Dataset Statistics

| Property | Value |
|---|---:|
| Dataset role | Training and validation |
| Files loaded | 8 |
| Total raw records | **2,830,743 flows** |
| Original columns | **79** |
| Aligned columns | **72** |
| Numeric model features | **71** |
| Benign flows | **2,273,097** |
| Attack flows | **557,646** |

### Input Files

```text
Monday-WorkingHours.pcap_ISCX.csv
Tuesday-WorkingHours.pcap_ISCX.csv
Wednesday-workingHours.pcap_ISCX.csv
Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
Friday-WorkingHours-Morning.pcap_ISCX.csv
Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

## CSE-CIC-IDS2018

CSE-CIC-IDS2018 is used exclusively as the external evaluation dataset in the intended experimental design.

### Dataset Statistics

| Property | Value |
|---|---:|
| Dataset role | Cross-dataset external test |
| Files loaded | 10 |
| Loading limit | First 300,000 rows per file |
| Total loaded records | **3,000,000 flows** |
| Records after label cleaning | **2,999,975 flows** |
| Original columns | **84** |
| Aligned columns | **72** |
| Numeric model features | **71** |
| Benign flows | **1,506,473** |
| Attack flows | **1,493,502** |

The use of `nrows=300000` limits computational demand, but it selects the first records from each file rather than a random or stratified sample. This limitation must be considered when interpreting the results.

---

## Attack Label Normalization

CICIDS2017 and CSE-CIC-IDS2018 use different names for related attacks. A normalization dictionary maps dataset-specific labels into a common taxonomy.

Examples include:

```text
DDoS
DDOS attack-LOIC-UDP
DDOS attack-HOIC
DDoS attacks-LOIC-HTTP
                    -> DDOS
```

```text
DoS Hulk
DoS GoldenEye
DoS Slowhttptest
DoS slowloris
DoS attacks-Hulk
DoS attacks-SlowHTTPTest
                    -> DOS
```

```text
FTP-Patator
SSH-Patator
FTP-BruteForce
SSH-Bruteforce
                    -> BRUTEFORCE
```

```text
Web Attack Brute Force
Web Attack XSS
Web Attack SQL Injection
Brute Force -Web
Brute Force -XSS
SQL Injection
                    -> WEBATTACK
```

## Final Label Distribution

| Normalized class | CICIDS2017 | CSE-CIC-IDS2018 |
|---|---:|---:|
| BENIGN | 2,273,097 | 1,506,473 |
| BOT | 1,966 | 242,500 |
| BRUTEFORCE | 13,835 | 299,205 |
| DDOS | 128,027 | 597,627 |
| DOS | 252,661 | 260,179 |
| HEARTBLEED | 11 | 0 |
| INFILTRATION | 36 | 93,063 |
| PORTSCAN | 158,930 | 0 |
| WEBATTACK | 2,180 | 928 |

The distribution shows substantial **class-prior shift** between the two datasets. It also shows that HEARTBLEED and PORTSCAN are present in CICIDS2017 but absent from the retained CSE-CIC-IDS2018 sample.

---

## Methodology

## 1. Data Loading

All eight CICIDS2017 files are loaded and concatenated into one DataFrame. Ten CSE-CIC-IDS2018 files are loaded with a maximum of 300,000 records per file.

## 2. Schema Alignment

The two datasets use different names for several equivalent CICFlowMeter features. The 2018 columns are renamed to match the 2017 schema.

Examples:

```text
Dst Port          -> Destination Port
Tot Fwd Pkts      -> Total Fwd Packets
Tot Bwd Pkts      -> Total Backward Packets
Flow Byts/s       -> Flow Bytes/s
Pkt Len Mean      -> Packet Length Mean
FIN Flag Cnt      -> FIN Flag Count
```

Only columns shared by both datasets are retained. This produces 71 common numeric features and one label column.

## 3. Target Construction

Two targets are created.

### Binary Target

```text
BENIGN -> 0
Any normalized attack class -> 1
```

### Multiclass Target

A `LabelEncoder` converts normalized attack-family names into integer classes.

| Encoded value | Class |
|---:|---|
| 0 | BENIGN |
| 1 | BOT |
| 2 | BRUTEFORCE |
| 3 | DDOS |
| 4 | DOS |
| 5 | HEARTBLEED |
| 6 | INFILTRATION |
| 7 | PORTSCAN |
| 8 | WEBATTACK |

## 4. Numerical Preprocessing

The preprocessing procedure:

1. retains numeric attributes;
2. converts invalid values to missing values;
3. replaces positive and negative infinity with `NaN`;
4. imputes missing values using the feature median;
5. converts features to `float32`;
6. aligns column names and ordering across datasets.

## 5. Feature Scaling

`StandardScaler` standardizes the 2017 feature distribution. The fitted scaler is then applied to the 2018 data.

## 6. Feature Selection

Three feature-reduction techniques are applied sequentially.

### Variance Threshold

```text
VarianceThreshold(threshold=0.01)
```

This removes features with very low variance after scaling.

| Processing stage | Features retained |
|---|---:|
| Common numeric features | 71 |
| After variance filtering | 69 |

### ANOVA Feature Selection

```text
SelectKBest(score_func=f_classif, k=30)
```

ANOVA F-scores identify features with strong statistical separation between benign and attack samples.

The first reported selected features include:

- ACK Flag Count
- Average Packet Size
- Average Backward Segment Size
- Backward IAT Maximum
- Backward IAT Standard Deviation
- Backward Packet Length Maximum
- Backward Packet Length Mean
- Backward Packet Length Minimum
- Backward Packet Length Standard Deviation
- Destination Port

### Principal Component Analysis

PCA is applied to the 30 ANOVA-selected features.

| PCA criterion | Components |
|---|---:|
| 95% explained variance | **11** |
| 99% explained variance | **16** |

The experiment uses **11 principal components**, preserving approximately **95.60%** of the variance in the selected feature space.

## 7. Train-Validation Split

CICIDS2017 is divided using an 80/20 stratified split.

| Partition | Samples | Components |
|---|---:|---:|
| Training set | **2,264,594** | 11 |
| Validation set | **566,149** | 11 |

The training subset contains:

```text
Benign flows : 1,818,477
Attack flows :   446,117
```

## 8. External Evaluation

Models fitted using CICIDS2017 are applied to the transformed CSE-CIC-IDS2018 data without retraining on 2018 features.

This evaluation measures performance under a source-to-target dataset shift.

---

## Exploratory Data Analysis

The project includes the following exploratory analyses:

- attack-class distributions for both datasets;
- benign-versus-attack feature histograms;
- feature correlation heatmap;
- scaled feature-variance analysis;
- ANOVA F-score ranking;
- cumulative PCA explained variance;
- two-dimensional PCA projection;
- model-comparison charts;
- confusion matrices;
- ROC curves.

## Purpose of the EDA

The analysis is used to investigate:

- class imbalance;
- differences in attack prevalence across years;
- redundant and correlated network-flow features;
- candidate features for attack detection;
- separability of benign and malicious samples;
- changes in model behavior across datasets.

## EDA Interpretation

The class distributions reveal substantial differences between CICIDS2017 and CSE-CIC-IDS2018. These differences are likely to affect model calibration, classification thresholds, and class-specific recall.

One limitation is that the variance ranking is computed after standardization. Since StandardScaler transforms most nonconstant features to approximately unit variance, this plot has limited value for comparing feature importance. Raw variance, robust dispersion, mutual information, or model-based importance would provide a more informative analysis.

---

## Models Evaluated

The experimental comparison covers complementary model families:

| Model family | Binary stage | Multiclass stage | Role in the comparison |
|---|:---:|:---:|---|
| Logistic Regression | Yes | Yes | Linear and interpretable baseline |
| Decision Tree | Yes | Yes | Nonlinear single-tree baseline |
| XGBoost | Yes | Yes | Regularized gradient-boosted trees |
| LightGBM | Yes | Yes | Efficient gradient-boosting baseline |

Class weighting or equivalent positive-class weighting is used where supported. Model selection is assessed with accuracy, precision, recall, F1-score, ROC-AUC, false-positive rate, macro-averaged metrics, and training time as available.

---

## Stage 1: Binary Attack Detection

## Objective

Stage 1 determines whether a network flow is benign or malicious.

```text
Input  : 11 PCA components
Output : Benign or Attack
```

## Models Evaluated

- Logistic Regression
- Decision Tree
- XGBoost
- LightGBM

Balanced class weights or equivalent weighting are used to reduce the influence of binary class imbalance.

## Cross-Validation Results on CICIDS2017

The executed code uses two-fold stratified cross-validation.

| Model | Mean CV accuracy | Standard deviation |
|---|---:|---:|
| **Decision Tree** | **0.996465** | 0.000030 |
| XGBoost | 0.987429 | 0.000049 |
| LightGBM | 0.987060 | 0.000763 |
| Logistic Regression | 0.782251 | 0.000199 |

The Decision Tree produces the highest cross-validation accuracy. However, cross-validation within CICIDS2017 measures in-domain performance rather than cross-dataset generalization.

## CICIDS2017 Validation Performance

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC | FPR | Training time |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Decision Tree** | **0.9968** | **0.9889** | 0.9947 | **0.9918** | 0.9970 | **0.0027** | 127.52 s |
| XGBoost | 0.9879 | 0.9444 | 0.9971 | 0.9700 | **0.9992** | 0.0144 | 25.26 s |
| LightGBM | 0.9865 | 0.9382 | **0.9972** | 0.9668 | 0.9992 | 0.0161 | 31.05 s |
| Logistic Regression | 0.7821 | 0.4735 | 0.9490 | 0.6318 | 0.8940 | 0.2589 | **6.06 s** |

### In-Domain Best Model

The **Decision Tree** is the strongest model on the CICIDS2017 validation set according to F1-score and false-positive rate.

However, this result does not establish external robustness.

## CSE-CIC-IDS2018 External Test Performance

| Model | Accuracy | Precision | Recall | F1-score | ROC-AUC | FPR |
|---|---:|---:|---:|---:|---:|---:|
| **Logistic Regression** | **0.7582** | 0.6928 | **0.9242** | **0.7919** | 0.7985 | 0.4063 |
| XGBoost | 0.6630 | **0.8597** | 0.3861 | 0.5329 | **0.8037** | 0.0625 |
| Decision Tree | 0.5518 | 0.7510 | 0.1492 | 0.2490 | 0.5436 | **0.0491** |
| LightGBM | Not available in supplied output | Not available | Not available | Not available | Not available | Not available |

The supplied notebook output is truncated before the complete LightGBM binary test row. Missing values are therefore not inferred.

## Cross-Dataset Performance Comparison

| Model | CICIDS2017 validation F1 | CSE-CIC-IDS2018 test F1 | Absolute change |
|---|---:|---:|---:|
| Logistic Regression | 0.6318 | **0.7919** | +0.1601 |
| Decision Tree | **0.9918** | 0.2490 | **-0.7428** |
| XGBoost | 0.9700 | 0.5329 | -0.4371 |

## Stage 1 Interpretation

### Decision Tree

The Decision Tree achieves near-perfect in-domain performance but suffers the largest generalization loss. Its F1-score decreases from 0.9918 to 0.2490. The model detects only 14.92% of attacks in the 2018 sample.

This result indicates strong sensitivity to dataset-specific decision boundaries.

### XGBoost

XGBoost provides high external precision and a comparatively low false-positive rate, but its recall decreases to 38.61%. It is more conservative than Logistic Regression, but misses a large proportion of malicious flows.

### Logistic Regression

Logistic Regression obtains the highest reported external F1-score and detects 92.42% of attacks. However, its false-positive rate is 40.63%, meaning a large proportion of benign flows are incorrectly flagged as malicious.

Its strong recall is therefore accompanied by a potentially unacceptable operational alert burden.

### Main Binary Finding

The model that performs best on CICIDS2017 is not the model that performs best on CSE-CIC-IDS2018. Model complexity improves in-domain fit but does not guarantee cross-dataset robustness.

---

## Stage 2: Multiclass Attack Classification

## Objective

Stage 2 classifies flows known to be malicious into attack families.

```text
Input  : Attack-only network flows
Output : Predicted attack family
```

## Dataset Size

| Dataset | Attack flows |
|---|---:|
| CICIDS2017 | **557,646** |
| CSE-CIC-IDS2018 | **1,493,502** |

## Models Evaluated

- Multinomial Logistic Regression
- Decision Tree
- XGBoost multiclass classifier
- LightGBM multiclass classifier

Macro-averaged precision, recall, and F1 are used because the attack classes are highly imbalanced.

## CSE-CIC-IDS2018 Multiclass Results

| Model | Accuracy | Macro precision | Macro recall | Macro F1-score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | **0.3802** | 0.2725 | **0.3419** | 0.2354 | NaN |
| Decision Tree | 0.2200 | 0.3279 | 0.1927 | 0.1724 | NaN |
| XGBoost | 0.3313 | 0.3631 | 0.3087 | 0.2480 | NaN |
| **LightGBM** | 0.3251 | **0.3708** | 0.3312 | **0.2501** | NaN |

### Best Reported Cross-Dataset Multiclass Model

**LightGBM** achieves the highest reported macro F1-score:

```text
Macro F1-score : 0.2501
Accuracy       : 0.3251
Macro precision: 0.3708
Macro recall   : 0.3312
```

Although LightGBM ranks first by macro F1, the overall result remains insufficient for reliable attack attribution.

## LightGBM Per-Class Performance on CSE-CIC-IDS2018

| Attack family | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| **BOT** | 0.96 | 0.99 | **0.97** | 242,500 |
| BRUTEFORCE | 0.27 | 0.40 | 0.32 | 299,205 |
| DDOS | 0.08 | 0.00 | 0.00 | 597,627 |
| DOS | 0.28 | 0.47 | 0.35 | 260,179 |
| INFILTRATION | 0.99 | 0.04 | 0.08 | 93,063 |
| WEBATTACK | 0.01 | 0.42 | 0.03 | 928 |

HEARTBLEED and PORTSCAN have zero support in the retained 2018 sample and are not meaningful test classes for that subset.

## Stage 2 Interpretation

### BOT

BOT is the only attack family that generalizes strongly, achieving 0.97 F1-score. Its flow characteristics appear comparatively consistent across the two datasets.

### DDOS

DDOS is the largest attack class in the 2018 sample, yet the model records effectively zero recall. This indicates that the DDOS patterns learned from CICIDS2017 do not transfer effectively to the variants represented in CSE-CIC-IDS2018.

### INFILTRATION

INFILTRATION achieves very high precision but only 4% recall. When the model predicts INFILTRATION it is usually correct, but it fails to identify most infiltration flows.

### WEBATTACK

WEBATTACK records 42% recall but only 1% precision. The model generates many false WEBATTACK predictions, making the class unreliable for operational attribution.

### Main Multiclass Finding

Attack-family classification is substantially more sensitive to dataset shift than binary attack detection. The normalized class names do not guarantee consistent feature distributions across years.

---

## Model Comparison Summary

| Research criterion | Strongest reported model | Interpretation |
|---|---|---|
| CICIDS2017 binary validation F1 | Decision Tree | Best in-domain classifier |
| CICIDS2017 binary ROC-AUC | XGBoost | Strong ranking ability in-domain |
| CSE-CIC-IDS2018 binary F1 | Logistic Regression | Best external detection balance |
| CSE-CIC-IDS2018 binary precision | XGBoost | Most precise reported external model |
| CSE-CIC-IDS2018 binary FPR | Decision Tree | Lowest false-alarm rate, but very low recall |
| CSE-CIC-IDS2018 multiclass macro F1 | LightGBM | Best overall attack-family balance |
| Best transferred attack family | BOT with LightGBM | Strong class-level generalization |

No single model dominates every criterion. Model choice depends on the operational cost assigned to missed attacks, false alerts, and incorrect attack attribution.

---

## Principal Findings

## 1. Same-Dataset Validation Overestimates Generalization

The Decision Tree achieves 0.9918 F1 on CICIDS2017 validation but only 0.2490 on CSE-CIC-IDS2018. This 0.7428 absolute decrease is the clearest evidence of dataset-specific overfitting.

## 2. Simpler Models Can Generalize Better

Logistic Regression performs poorly relative to the tree models within CICIDS2017, yet obtains the highest reported external binary F1. A simpler decision boundary may be less dependent on dataset-specific partitions.

## 3. High Recall Can Produce Excessive False Alerts

Logistic Regression detects most 2018 attacks, but its 40.63% false-positive rate would create substantial alert volume in a production Security Operations Centre.

## 4. Cross-Dataset Multiclass Classification Remains Difficult

The best external macro F1 is only 0.2501. Broad attack labels do not eliminate differences in attack tools, traffic patterns, or collection environments.

## 5. Class-Specific Generalization Varies Substantially

BOT transfers well, while DDOS, INFILTRATION, and WEBATTACK demonstrate severe generalization limitations.

## 6. Class Imbalance Is Extreme

CICIDS2017 contains only 11 HEARTBLEED and 36 INFILTRATION records, while the retained 2018 sample contains 93,063 INFILTRATION flows and no HEARTBLEED flows. Such differences complicate supervised learning and fair comparison.

---

## Achievements

The project successfully:

- processed approximately 5.83 million loaded network-flow records;
- aligned two related but nonidentical CICFlowMeter schemas;
- normalized heterogeneous attack labels into a common taxonomy;
- implemented binary and multiclass detection stages;
- reduced 71 numeric features to 11 principal components;
- compared linear, decision-tree, and gradient-boosting algorithms;
- measured both in-domain and external test performance;
- generated EDA, feature-selection, PCA, ROC, and confusion-matrix visualizations;
- demonstrated a substantial cross-dataset generalization gap;
- saved trained models using Joblib;
- exported compatible scikit-learn models to ONNX;
- created a compressed model bundle for future inference development.

The most important achievement is not the highest accuracy score. It is the empirical demonstration that strong CICIDS2017 validation results can fail to generalize to CSE-CIC-IDS2018.

---

## Effectiveness Assessment

## Research Effectiveness

The project is effective as a research prototype because it evaluates a more realistic and difficult problem than ordinary random-split benchmarking. It identifies where standard models fail and establishes a foundation for domain-generalization research.

## Binary Detection Effectiveness

The binary stage demonstrates partial effectiveness:

- Logistic Regression provides high attack recall;
- XGBoost provides stronger precision and false-positive control;
- Decision Tree provides excellent source-domain performance but weak external recall.

None of the reported models simultaneously achieves high recall and a low false-positive rate on CSE-CIC-IDS2018.

## Multiclass Effectiveness

The multiclass stage is not sufficiently reliable for automatic external attack attribution. LightGBM's macro F1-score of 0.2501 indicates that most attack classes remain difficult to identify consistently across datasets.

## Production Readiness

The system should **not** currently be treated as a production-ready IDS because:

- the complete cascade has not been evaluated;
- preprocessing leakage affects the internal validation protocol;
- the external test set is used for post-hoc model selection;
- inference artifacts are incomplete;
- probability thresholds are not operationally tuned;
- concept drift and class-prior drift are not explicitly handled;
- no real-time throughput or latency evaluation is reported.

---

## Threats to Validity and Implementation Limitations

## 1. Feature-Selection Leakage

Scaling, variance filtering, ANOVA selection, and PCA are fitted before the CICIDS2017 train-validation split. Since ANOVA uses target labels, the validation partition influences feature selection.

All transformations should be fitted only on the training partition or inside each cross-validation fold.

## 2. Test-Set Median Imputation

The preprocessing function computes medians independently for each dataset. Consequently, missing values in CSE-CIC-IDS2018 are filled using statistics calculated from the external test data.

A fitted `SimpleImputer` trained on CICIDS2017 should be saved and applied unchanged to validation, test, and live data.

## 3. Test-Set Model Selection

The code identifies the best model by maximizing F1 on CSE-CIC-IDS2018. This uses the external dataset for model selection and may produce an optimistic final estimate.

The final model should be selected using CICIDS2017 validation data before a single locked evaluation on 2018.

## 4. Nonrandom 2018 Sampling

The first 300,000 rows from each CSV are loaded. If the files are temporally ordered, this procedure may not represent their complete traffic distributions.

## 5. Binary-Derived Features Reused for Stage 2

The ANOVA selector is fitted using the binary target and reused for multiclass classification. Features that distinguish benign traffic from attack traffic are not necessarily optimal for distinguishing attack families.

Stage 2 should use a separately fitted multiclass preprocessing pipeline.

## 6. Incomplete End-to-End Evaluation

Stage 2 receives ground-truth attack flows rather than Stage 1 predicted attacks. The reported multiclass results therefore exclude error propagation from the binary detector.

## 7. Unsupported and Zero-Support Classes

HEARTBLEED and PORTSCAN are absent from the retained 2018 sample. Their zero-support metrics should not be interpreted as ordinary classification failures.

## 8. Multiclass ROC-AUC Failure

The multiclass ROC-AUC values are `NaN`, most likely because encoded labels, model probability columns, and the subset of classes present in the test data are not consistently aligned. Broad exception handling suppresses the precise error.

## 9. Cross-Validation Documentation Mismatch

The notebook description refers to five-fold cross-validation, while the binary implementation uses two folds.

## 10. Post-Scaling Variance Analysis

Ranking feature variance after standardization is not strongly informative because standardized nonconstant features have approximately unit variance.

---

## Recommended Improvements

## Experimental Design

- Perform the train-validation split before fitting preprocessing objects.
- Place imputation, scaling, feature selection, PCA, and classification inside an `sklearn` pipeline.
- Fit transformations independently inside each cross-validation fold.
- Select models using CICIDS2017 validation only.
- Reserve CSE-CIC-IDS2018 for one final external evaluation.
- Evaluate the complete two-stage cascade.
- Report per-file and per-day results to identify temporal instability.
- Replace fixed first-row sampling with randomized, stratified, temporal, or complete evaluation.

## Feature Engineering

- Compare PCA and non-PCA models.
- Fit a separate feature selector for Stage 2.
- Evaluate mutual information and model-based selection.
- Measure source-target feature drift using PSI, Kolmogorov-Smirnov statistics, or Wasserstein distance.
- Investigate invariant features that retain predictive power across datasets.

## Model Development

- Tune probability thresholds using validation precision-recall curves.
- Evaluate calibrated Logistic Regression, XGBoost, and LightGBM models.
- Compare cost-sensitive learning and focal-style objectives.
- Investigate domain adaptation and transfer learning.
- Add an `UNKNOWN_ATTACK` class for low-confidence or unseen patterns.
- Explore ensemble strategies that combine high-recall and low-FPR detectors.

## Evaluation

- Report PR-AUC in addition to ROC-AUC.
- Report confidence intervals.
- Measure alerts per million benign flows.
- Report false negatives per attack family.
- Evaluate model calibration.
- Compare macro, weighted, and class-specific metrics.
- Preserve an untouched final test protocol.

## Deployment

- Save one complete fitted pipeline for each stage.
- Pin dependency versions in `requirements.txt`.
- add schema-validation tests;
- add Joblib-to-ONNX prediction-parity tests;
- use `onnxmltools` or registered converters for XGBoost and LightGBM;
- benchmark inference throughput and latency;
- monitor live feature and prediction drift.

---

## Technology Stack

- **Python**
- **Pandas**
- **NumPy**
- **Scikit-learn**
- **XGBoost**
- **LightGBM**
- **Matplotlib**
- **Seaborn**
- **Joblib**
- **ONNX**
- **skl2onnx**

## Execution Environment

```text
Kaggle Notebook
Python 3
CPU-based model training
```
---

## Running the Experiment

## 1. Configure Dataset Paths

```python
path_2017 = "/path/to/CICIDS2017/"
path_2018 = "/path/to/CSE-CIC-IDS2018/"
```

## 2. Execute the Pipeline

Run the notebook sections in the following order:

1. import dependencies;
2. load CICIDS2017;
3. load CSE-CIC-IDS2018;
4. align feature schemas;
5. normalize attack labels;
6. construct binary and multiclass targets;
7. perform exploratory analysis;
8. preprocess features;
9. perform feature selection and PCA;
10. train binary models;
11. evaluate binary models;
12. train multiclass models;
13. evaluate multiclass models;
14. export models and metadata.

## 3. Inspect Outputs

The model archive is created at:

```text
/kaggle/working/ids_model_bundle.zip
```

Before inference, verify that every required preprocessing artifact and encoder is present.

---

## Reproducibility Parameters

| Parameter | Value |
|---|---:|
| Random seed | 42 |
| CICIDS2017 validation proportion | 20% |
| Split strategy | Stratified |
| Binary CV folds | 2 |
| Multiclass CV folds | 3 for selected models |
| Variance threshold | 0.01 |
| ANOVA features | 30 |
| PCA variance target | 95% |
| PCA components | 11 |
| 2018 limit | 300,000 rows per file |

---

## Applications

This project can support research and development in:

- network intrusion-detection benchmarking;
- cross-dataset machine-learning evaluation;
- cybersecurity analytics;
- domain-shift and concept-drift analysis;
- Security Operations Centre alert prioritization;
- model portability and ONNX deployment experiments;
- real-time NIDS prototyping;
- robust feature-selection research.

---

## Conclusion

This project presents a large-scale two-stage Network Intrusion Detection System trained on CICIDS2017 and externally evaluated on CSE-CIC-IDS2018.

Within CICIDS2017, the Decision Tree achieves almost perfect binary classification performance with an F1-score of 0.9918. However, its F1-score decreases to 0.2490 on CSE-CIC-IDS2018. XGBoost also experiences a substantial decline. Logistic Regression achieves the highest reported external binary F1-score of 0.7919 and recall of 0.9242, but this improvement is accompanied by a false-positive rate of 0.4063.

For multiclass attack classification, LightGBM achieves the highest reported macro F1-score of 0.2501. BOT transfers effectively across datasets, while DDOS, INFILTRATION, and WEBATTACK remain difficult to classify reliably.

The central conclusion is:

> **High performance on a same-dataset validation split is not sufficient evidence of a robust Network Intrusion Detection System. External cross-dataset testing reveals substantial distribution shift and model-specific generalization failure.**

The proposed pipeline is valuable as an academic prototype and cross-dataset benchmark. Further work is required to eliminate preprocessing leakage, preserve test independence, train stage-specific feature pipelines, evaluate the complete cascade, reduce false alerts, and create a complete reproducible deployment artifact.

---

## Ethical and Operational Notice

This project is intended for defensive cybersecurity research and educational evaluation. The trained models should not be used as the sole security control in a production network. Operational deployment requires environment-specific validation, continuous drift monitoring, human analyst review, and layered security controls.

---

## Dataset References

- **CICIDS2017:** Canadian Institute for Cybersecurity, University of New Brunswick, *Intrusion Detection Evaluation Dataset 2017*.
- **CSE-CIC-IDS2018:** Canadian Institute for Cybersecurity and Communications Security Establishment, *CSE-CIC-IDS2018 on AWS*.

Users should obtain datasets through authorized sources and comply with the providers' usage and attribution requirements. Dataset files are not included in this repository.

---

## License

This project is released under the **MIT License**. Dataset use remains subject to the terms and attribution requirements of the respective dataset providers.
