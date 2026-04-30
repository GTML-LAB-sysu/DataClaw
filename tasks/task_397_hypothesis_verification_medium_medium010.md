---
id: task_397_hypothesis_verification_medium_medium010
name: hypothesis_verification-medium-medium010
category: hypothesis_verification
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/hypothesis_verification/medium010.json
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

In 2022, based on the 'high input low output' hypothesis in Romer's endogenous growth theory, verify whether state-owned enterprises in the semiconductor industry exhibit the dual anomaly of 'large asset scale but low operating profit margin' and 'high R&D investment but low patent conversion efficiency'. The hypothesis states: when state-owned enterprises rank high in the industry in both asset scale (total assets) and R&D investment (amount), their operating profit margin (operating profit / revenue) and patent conversion efficiency (cumulative China invention patent grants / R&D investment × 100 million) should rank low in the industry. Please count the number of enterprises that simultaneously satisfy the following conditions (state-owned enterprises include central state-owned enterprises, local state-owned enterprises, state-owned enterprises (research institutes), and state-owned enterprises (other)): ① total assets > median total assets of industry-wide state-owned enterprises; ② operating profit margin < median operating profit margin of industry-wide state-owned enterprises; ③ R&D investment amount > median R&D investment amount of industry-wide state-owned enterprises; ④ patent conversion efficiency < median patent conversion efficiency of industry-wide state-owned enterprises.

Output guidelines:
Answer format: numerical value (integer, unit: enterprises). If relevant data cannot be found, please answer "No relevant data found"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Single-answer Correctness (Weight: 100%)

Gold answer JSON:
`3`

Scoring rules:
- Judge semantic equivalence between the model final answer and the gold answer.
- Return `scores` with one key `match` as 1 or 0.
- Return `total` as 1.0 if equivalent, otherwise 0.0.

