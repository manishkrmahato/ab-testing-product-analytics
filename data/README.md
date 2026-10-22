## 1. Overview & Provenance

This project utilizes experimentation data from an e-commerce website landing page A/B test. The dataset was originally released by **Udacity** as part of the curriculum project *Analyze A/B Test Results* in the Data Analyst Nanodegree Program. It is widely mirrored on Kaggle and student repositories for experimentation pedagogy.

- **Primary Dataset (`ab_data.csv`)**:
  - Upstream Source URL: `https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv`
  - Canonical Reference: Udacity Data Analyst Nanodegree (`Analyze_ab_test_results_notebook.ipynb`)
  - Verified File Size: 15,901,933 bytes (\~15.16 MB)
  - Verified SHA256: `d56e2accec25e99ac21cb3d76c5df516dd19cc7a77c14c9014f94e1ea1301beb`
  - Total Raw Records: 294,478 observations across 290,584 unique visitor IDs
- **Secondary Segment Dataset (`countries.csv`)**:
  - Upstream Source URL: `https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv`
  - Verified File Size: 2,905,856 bytes (\~2.77 MB)
  - Verified SHA256: `c011d0503d305c295327cd9dff9c37bb62a5f9ef4b356bcdaf7deca20d55e45b`
  - Total Raw Records: 290,584 observations mapping `user_id` to `country` (`US`, `UK`, `CA`)

### Licensing & Usage Rights Notice

The dataset is distributed as open educational courseware for learning and portfolio demonstration. However, the upstream repository does not bundle an explicit formal Creative Commons (e.g., CC0 / CC-BY) license deed. Formal commercial rights and public domain status cannot be independently verified offline. Users evaluating this repository should note that third-party data copyright remains with Udacity and its original authors.

---

## 2. Raw Schema & Column Definitions

### `ab_data.csv`

| **Column Name** | **Data Type**    | **Description**                                     | **Values / Range**                                         |
| --------------- | ---------------- | --------------------------------------------------- | ---------------------------------------------------------- |
| `user_id`       | `int64`          | Unique visitor identifier                           | Range: [630000, 945999]                                    |
| `timestamp`     | `datetime64[ns]` | Timestamp when the page view event was logged (UTC) | `2017-01-02 13:42:05` to `2017-01-24 13:41:54` (22.0 days) |
| `group`         | `category`       | Experimental condition assigned to visitor          | `'control'`, `'treatment'`                                 |
| `landing_page`  | `category`       | Version of webpage rendered to browser              | `'old_page'`, `'new_page'`                                 |
| `converted`     | `int64`          | Binary conversion indicator                         | `0` = No conversion, `1` = Converted                       |

### `countries.csv`

| **Column Name** | **Data Type** | **Description**                              | **Values / Distribution**                        |
| --------------- | ------------- | -------------------------------------------- | ------------------------------------------------ |
| `user_id`       | `int64`       | Foreign key to `ab_data.csv` unique visitors | Matches 290,584 unique visitors                  |
| `country`       | `category`    | User geolocation code                        | `'US'` (70.07%), `'UK'` (24.94%), `'CA'` (4.99%) |

---

## 3. Deep Data Quality Audit: Visitor-Level Structure & Anomalies

An exhaustive audit of raw user sessions reveals critical structural complexities:

### 3.1 Visitor Frequency Distribution

- **Total Raw Records**: 294,478
- **Total Unique Visitors**: 290,584
- **Single-Session Visitors**: 286,690 visitors appear exactly once (98.66%).
- **Multi-Session Visitors**: 3,894 visitors appear exactly twice (1.34%). No visitor appears 3 or more times.

### 3.2 Multi-Session Anomaly Breakdown (3,894 Visitors)

Among the 3,894 visitors with repeat sessions:

1. **Clean Repeat Visitor (1 visitor)**:
   - `user_id = 773192` visited twice (`2017-01-09` and `2017-01-14`), consistently in `treatment` and receiving `new_page` (`converted = 0` on both).
2. **Conflicting Group Assignments (1,895 visitors)**:
   - These visitors have one session logged as `control` and one session logged as `treatment`. In both sessions, the rendered `landing_page` was identical (e.g., `old_page` on both visits or `new_page` on both visits).
   - *Implication*: Their assigned experimental group was unstable across sessions, indicating cookie resets, cross-device switching, or bucketing re-randomization.
3. **Conflicting Landing Pages Delivered (1,998 visitors)**:
   - These visitors had a stable `group` assignment across both sessions, but were served conflicting landing pages (`old_page` on one visit and `new_page` on the other).
   - *Implication*: These visitors experienced cross-variant exposure (treatment contamination).
4. **Row-Level Routing Mismatches**:
   - Across the entire raw dataset, there are **3,893 rows** where `group == 'control'` and `landing_page == 'new_page'` (1,928 rows) or `group == 'treatment'` and `landing_page == 'old_page'` (1,965 rows).
   - Notice that `1,895+1,998=3,893`. Every single multi-session visitor (except `773192`) accounts for exactly one matched row and one mismatched row!

---

## 4. Visitor-Level Analysis Rules & Methodological Trade-offs

We explicitly define and evaluate four analytical specifications rather than silently discarding records:

| **Specification**                   | **Defining Rule**                                                                   | **Sample Size (`N`)** | **Methodological Trade-off**                                                                                     |
| ----------------------------------- | ----------------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **1. Strictly Unambiguous Cohort**  | Excludes all 3,893 visitors with routing errors or conflicting groups               | **286,691**           | Eliminates contamination; complete-case analysis, but assumes drop-outs are Missing Completely at Random (MCAR). |
| **2. Benchmark Matched Filter**     | Drops the 3,893 mismatched rows, keeping 1 matched row per user                     | **290,584**           | Standard Udacity curriculum convention; retains all visitors but ignores that 1,998 users saw both pages.        |
| **3. First-Touch Assignment Proxy** | Assigns user to earliest recorded `group`; conversion = `max(converted)`            | **290,584**           | Sensitivity analysis only; not verified ITT because authoritative assignment logs are unavailable.               |
| **4. As-Treated (First Page)**      | Assigns user to the first page version actually seen; conversion = `max(converted)` | **290,584**           | Measures effect of page actually rendered; loses pure random assignment properties.                              |

### Causal Inference Caveat

We do **not** claim that filtering mismatched rows "prevents contamination" or that the resulting estimate is "automatically unbiased." If routing errors or multi-session returns were influenced by page performance or user engagement, complete-case filtering can induce selection or attrition bias. Demonstrating robustness across all four specifications is essential for statistical defensibility.

---

## 5. Automated Data Ingestion

curl.exe -L -o data/raw/ab_data.csv [https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv](https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv) curl.exe -L -o data/raw/countries.csv [https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv](https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv)





anything needed to change and is this the way user will reead it ?
