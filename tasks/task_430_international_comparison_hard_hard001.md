---
id: task_430_international_comparison_hard_hard001
name: international_comparison-hard-hard001
category: international_comparison
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/international_comparison/hard001.json
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

Against the backdrop of China's strong push for semiconductor industry self-sufficiency and many regions issuing special support policies, what are the R&D expenses and operating revenue disclosed in United Microelectronics Corporation (UMC)'s 2022 annual report (in New Taiwan Dollars)? What is the R&D investment ratio calculated therefrom? In the domestic semiconductor industry, the top 10% by operating revenue are classified as leading enterprises. By how many percentage points does UMC's R&D investment ratio differ from the median R&D investment ratio of these leading enterprises?

Output guidelines:
Please answer in order: (1) UMC 2022 R&D expenses (hundred million NTD, 2 decimal places); (2) UMC 2022 operating revenue (hundred million NTD, 2 decimal places); (3) UMC R&D investment ratio (%, 2 decimal places); (4) Difference between UMC's R&D investment ratio and the median R&D investment ratio of domestic semiconductor industry leading enterprises (top 10% by revenue) (percentage points, 2 decimal places, negative if lower；return as an array). If relevant data cannot be found, please answer "No relevant data found".

You may use files under `./database/` and web search.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`[129.53, 2787.05, 4.65, -1.16]`

Scoring rules:
- The gold answer is a list with N=4 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_3` each as 0 or 1.
- Return `total = (sum(part_i)) / 4` exactly.
- If the model output is missing or cannot be parsed into 4 comparable parts, score all parts 0.

