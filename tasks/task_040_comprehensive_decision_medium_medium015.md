---
id: task_040_comprehensive_decision_medium_medium015
name: comprehensive_decision-medium-medium015
category: comprehensive_decision
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/comprehensive_decision/medium015.json
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

List the 2022 indicators for which Shandong Province's financial industry enterprise averages are below the national financial industry medians.

Output guidelines:
The answer must list all qualifying indicator names, separated by semicolons. If relevant data cannot be found, respond with "No relevant data found".

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`["Year-on-year R&D personnel growth rate", "Year-on-year operating profit growth rate", "Year-on-year net profit growth rate", "Year-on-year employee growth rate", "Capitalized R&D expenditure", "Year-on-year capitalized R&D expenditure growth rate", "Annual PCT patent applications", "Annual PCT invention patent applications", "Provincial/ministerial science and technology progress award", "Participation in drafting national standards", "Participation in drafting industry standards", "Annual Chinese patent applications", "Annual Chinese invention patent applications", "Annual Chinese patent grants", "Cumulative Chinese invention patent applications", "Annual Chinese invention patent grants", "Cumulative PCT patent applications", "Cumulative PCT invention patent applications", "Cumulative Chinese patent applications", "Cumulative Chinese invention patent grants", "Cumulative patent citations", "R&D personnel ratio", "R&D personnel count", "Year-on-year R&D expenditure growth rate", "Cumulative Chinese invention patent lapses", "Company market value", "Asset-liability ratio", "Total employee count"]`

Scoring rules:
- The gold answer is a list with N=28 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_27` each as 0 or 1.
- Return `total = (sum(part_i)) / 28` exactly.
- If the model output is missing or cannot be parsed into 28 comparable parts, score all parts 0.

