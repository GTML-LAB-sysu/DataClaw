---
id: task_440_international_comparison_hard_hard011
name: international_comparison-hard-hard011
category: international_comparison
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/international_comparison/hard011.json
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

When an industrial internet fund evaluation distribution platform transforms toward high value-added services, it adopts a two-step method: ? Intangible input excess = company's R&D investment ratio - median R&D investment ratio of the A-share wholesale and retail industry in 2022; ? Transformation score = net service revenue ratio + intangible input excess. Only when net service revenue ratio >= 5 and transformation score >= 5 can a company enter the platform-based overweight list; otherwise, it enters the watch list. Based on ZKH's 2022 annual report and local database, calculate and determine the most appropriate conclusion.

Output guidelines:
Answer in order: Net service revenue ratio (%), intangible input excess (percentage points), transformation score, and the most appropriate conclusion. Retain 2 decimal places for numerical values and return as an array. The conclusion must clearly indicate whether to enter the platform-based overweight list or the watch list. If relevant data cannot be found, respond with "Relevant data not found".

You may use files under `./database/` and web search.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`["2.16", "2.49", "4.65", "Watch list"]`

Scoring rules:
- The gold answer is a list with N=4 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_3` each as 0 or 1.
- Return `total = (sum(part_i)) / 4` exactly.
- If the model output is missing or cannot be parsed into 4 comparable parts, score all parts 0.

