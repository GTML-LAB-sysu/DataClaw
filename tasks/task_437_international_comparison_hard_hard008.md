---
id: task_437_international_comparison_hard_hard008
name: international_comparison-hard-hard008
category: international_comparison
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/international_comparison/hard008.json
workspace_files: [
  {
    "source": "database/bilingual_translation_english_chinese.json",
    "dest": "database/bilingual_translation_english_chinese.json"
  },
  {
    "source": "database/enterprise/company_core.csv",
    "dest": "database/enterprise/company_core.csv"
  },
  {
    "source": "database/enterprise/company_operation_status.csv",
    "dest": "database/enterprise/company_operation_status.csv"
  },
  {
    "source": "database/enterprise/company_operation_status_detail.csv",
    "dest": "database/enterprise/company_operation_status_detail.csv"
  },
  {
    "source": "database/enterprise/company_operation_yearly_status.csv",
    "dest": "database/enterprise/company_operation_yearly_status.csv"
  },
  {
    "source": "database/enterprise/company_profile.csv",
    "dest": "database/enterprise/company_profile.csv"
  },
  {
    "source": "database/enterprise/company_profile_as.csv",
    "dest": "database/enterprise/company_profile_as.csv"
  },
  {
    "source": "database/enterprise/company_profile_eu.csv",
    "dest": "database/enterprise/company_profile_eu.csv"
  },
  {
    "source": "database/enterprise/company_profile_na.csv",
    "dest": "database/enterprise/company_profile_na.csv"
  },
  {
    "source": "database/enterprise/company_profile_oc.csv",
    "dest": "database/enterprise/company_profile_oc.csv"
  },
  {
    "source": "database/industry/national_industry_status.csv",
    "dest": "database/industry/national_industry_status.csv"
  },
  {
    "source": "database/industry/national_industry_status_detail.csv",
    "dest": "database/industry/national_industry_status_detail.csv"
  },
  {
    "source": "database/industry/national_industry_yearly_status.csv",
    "dest": "database/industry/national_industry_yearly_status.csv"
  },
  {
    "source": "database/industry/regional_industry_status.csv",
    "dest": "database/industry/regional_industry_status.csv"
  },
  {
    "source": "database/industry/regional_industry_status_detail.csv",
    "dest": "database/industry/regional_industry_status_detail.csv"
  },
  {
    "source": "database/industry/regional_industry_yearly_status.csv",
    "dest": "database/industry/regional_industry_yearly_status.csv"
  },
  {
    "source": "database/internal_metrics.csv",
    "dest": "database/internal_metrics.csv"
  },
  {
    "source": "database/policy/policy_release_status.csv",
    "dest": "database/policy/policy_release_status.csv"
  },
  {
    "source": "database/policy/policy_resource.csv",
    "dest": "database/policy/policy_resource.csv"
  }
]
---

## Prompt

A global consumer defensive portfolio, when screening platform retailers, views fulfillment expenses as having quasi-fixed cost characteristics. For candidate companies, apply the following stress test: ① Fulfillment expense ratio = Fulfillment ÷ Net revenues; ② Stressed net profit margin = company net profit margin - 0.2 × fulfillment expense ratio; ③ Defense gap = stressed net profit margin - median net profit margin of A-share wholesale and retail industry top 10% by revenue in 2022. If stressed net profit margin < 0, do not include in defensive core position; if stressed net profit margin is between 0 and industry median, benchmark hold only; if above industry median, overweight is allowed. Using JD.com (JD) 2022 annual report and local database, calculate and determine the most appropriate conclusion.

Output guidelines:
Answer in order: fulfillment expense ratio (%), stressed net profit margin (%), defense gap (percentage points), most appropriate conclusion. Retain 2 decimal places and return as an array; conclusion must specify position action. If relevant data cannot be found, please answer "No relevant data found".

You may use files under `./database/` and web search.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`[6.02, -0.28, -1.16, "Do not include in defensive core position"]`

Scoring rules:
- The gold answer is a list with N=4 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_3` each as 0 or 1.
- Return `total = (sum(part_i)) / 4` exactly.
- If the model output is missing or cannot be parsed into 4 comparable parts, score all parts 0.

