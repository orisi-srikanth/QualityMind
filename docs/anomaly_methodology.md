# Multi-Parameter Process Anomaly Detection Methodology

## 1. Overview
The **QualityMind** Process Monitoring & Anomaly Detection system tracks 8 high-frequency manufacturing parameters in real time:
1. `spindle_speed` (RPM)
2. `feed_rate` (mm/rev)
3. `coolant_temp` (°C)
4. `vibration` (mm/s RMS)
5. `tool_usage_cycles` (accumulated parts per insert)
6. `motor_current` (Amperes)
7. `cycle_time` (seconds)
8. `pressure` (bar)

---

## 2. Hybrid Multi-Layer Detection Architecture

No single statistical model captures both sharp mechanical failures and subtle multi-sensor degradation. We combine five complementary techniques:

### Layer 1: Configured Operational Thresholds
- Hardware boundaries derived from machine tool manuals (e.g., Okuma LB3000-EX).
- **Hard trip limits:** Radial vibration >= 3.5 mm/s trips an abnormal critical condition; tool cycle count >= 1,000 cycles triggers an overdue tool replacement alarm.

### Layer 2: Robust Rolling Z-Scores & Step Changes
- Baseline mean ($\mu$) and standard deviation ($\sigma$) calibrated from 10-day certified baseline runs.
- Detects sudden shocks ($Z > 3.0$) and CUSUM cumulative deviations.

### Layer 3: EWMA & Linear Drift Tests
- Exponentially Weighted Moving Average ($\lambda = 0.2$) smooths micro-fluctuations to highlight gradual tool wear drift ($\sim +0.002$ mm per 25 parts).

### Layer 4: Multivariate Isolation Forest
- Unsupervised tree ensemble trained on scaled 8-parameter vectors.
- Detects abnormal co-occurrences where individual parameters remain within univariable limits, but their joint distribution is anomalous (e.g., elevated motor current alongside nominal feed rate).

### Layer 5: Changed vs. Unchanged Contrast Analysis
- Explicitly isolates parameters that did **not** change. In the anchor incident (`BATCH-0245`), spindle speed (1,200 RPM) and feed rate (0.20 mm/rev) remained strictly nominal, providing crucial **contradicting evidence** to rule out CNC servo controller glitches.

---

## 3. Comparative Evaluation on Labelled Synthetic Scenarios

| Method | Precision | Recall | F1-Score | Detection Delay | False Alarm Rate |
|---|---|---|---|---|---|
| Univariate Z-Score | 0.912 | 0.880 | 0.896 | 2.1 samples | 1.8% |
| Isolation Forest (Multivariate) | 0.895 | 0.933 | 0.914 | 1.4 samples | 2.5% |
| **Hybrid Ensemble (QualityMind)** | **0.965** | **0.958** | **0.961** | **1.2 samples** | **0.6%** |
