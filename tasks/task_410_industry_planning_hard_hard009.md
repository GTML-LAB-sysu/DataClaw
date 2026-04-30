---
id: task_410_industry_planning_hard_hard009
name: industry_planning-hard-hard009
category: industry_planning
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/industry_planning/hard009.json
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

以2022年铁路、船舶、航空航天和其他运输设备制造业的省级（限定为铁路、船舶、航空航天和其他运输设备制造业辖内企业数量达到3家以上的中国大陆省级行政区，港澳台数据不纳入）数据为基准，模拟如下政策分化对行业格局的冲击：已出台船舶与海洋工程装备产业专项发展政策的省份，其企业营业收入增速在未来三年将在现有中位水平上额外叠加5个百分点；而没有落地此类专项政策的省份，受制于政策真空，营业收入增速将萎缩至现有水平的70%（增速以各省企业营业收入同比增减幅中位数为准）。按各省调整后的增速进行3年复合增长推算，对比2022年与2025年的省际营收排名变动，请从无政策省份中找出：哪个省份享受政策红利而获得最大幅度的排名上升？它一共上升了几位？该省2025年的预测营业收入总量为多少亿元？

Output guidelines:
依次回答省份名称、排名下降名数（整数）、该省2025年预计营业收入总额。营业收入总额保留2位小数，单位为亿元。如["广东省", 2, 512.34]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`["山东省", 2, 697.09]`

Scoring rules:
- The gold answer is a list with N=3 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_2` each as 0 or 1.
- Return `total = (sum(part_i)) / 3` exactly.
- If the model output is missing or cannot be parsed into 3 comparable parts, score all parts 0.

