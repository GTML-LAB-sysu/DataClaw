---
id: task_442_international_comparison_hard_hard013
name: international_comparison-hard-hard013
category: international_comparison
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/international_comparison/hard013.json
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

A quasi-infrastructure growth portfolio allows allocation to data center operators during accounting loss periods, but requires a significant operating profit buffer. For candidate companies, apply the following rules: ① Profit conversion penalty = |net profit margin| ÷ adjusted EBITDA margin × 100; ② Policy diffusion ratio = number of data center, Eastern Data Western Computing, or computing power related policies ÷ number of provincial-level administrative regions covered by non-national policies; ③ Infrastructure capacity score = adjusted EBITDA margin - profit conversion penalty + 5 × policy diffusion ratio. If profit conversion penalty < 35 and infrastructure capacity score > 25, the company may be listed for satellite overweight 1.00%; otherwise, benchmark allocation only. Based on GDS Holdings (GDS) 2022 annual report and local database, calculate and determine the most appropriate conclusion.

Output guidelines:
Answer in order: Profit conversion penalty, policy diffusion ratio, infrastructure capacity score, and the most appropriate conclusion. Retain 2 decimal places for numerical values and return as an array. The conclusion must clearly indicate position action. If relevant data cannot be found, respond with "Relevant data not found".

You may use files under `./database/` and web search.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`[29.77, 1.25, 22.08, "Benchmark allocation only"]`

Scoring rules:
- The gold answer is a list with N=4 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_3` each as 0 or 1.
- Return `total = (sum(part_i)) / 4` exactly.
- If the model output is missing or cannot be parsed into 4 comparable parts, score all parts 0.

