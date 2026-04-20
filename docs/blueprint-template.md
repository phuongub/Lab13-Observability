# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: C401 - B4
- [REPO_URL]: `https://github.com/phuongub/Lab13-Observability.git`
- [MEMBERS]:
  - Member A: Phạm Nguyễn Tiến Mạnh | Role: Logging & PII
  - Member B: Trịnh Uyên Chi | Role: Tracing & Enrichment
  - Member C: Nguyễn Hoàng Nghĩa | Role: SLO & Alerts
  - Member D: Trần Việt Phương | Role: Load Test & Incident Injection
  - Member E: Nguyễn Thị Thùy Trang | Role: Dashboard & Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: /100
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]:   

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: ![correlation](screenshot/image-1.png)
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: ![REDACTION](screenshot/image.png)
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 860.2 ms |
| Error Rate | < 2% | 28d | 0.62% |
| Cost Budget | < $2.5/day | 1d | $0.2529 |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: (e.g., rag_slow)
- [SYMPTOMS_OBSERVED]: 
- [ROOT_CAUSE_PROVED_BY]: (List specific Trace ID or Log Line)
- [FIX_ACTION]: 
- [PREVENTIVE_MEASURE]: 

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]: Phạm Nguyễn Tiến Mạnh
- [TASKS_COMPLETED]: 
  - Hoàn thiện cấu hình logging trong logging_config.py để chuẩn hóa log JSONL, tự bổ sung các field bắt buộc như service, correlation_id, route, method, user_id_hash, session_id, feature, model.
  - Triển khai PII scrubbing trong pii.py và logging_config.py để che email, số điện thoại, CCCD, credit card, bearer token, API key và password trước khi ghi vào logs.jsonl
- [EVIDENCE_LINK]: 
  - Commit hash:
`128c34a3cab9ec90e903ed6c4696b49c2a67d150`
`c96a1cc3bbfac0abde44d17d4fdabfb701dc6336`
  - Commit link:
`https://github.com/phuongub/Lab13-Observability/commit/128c34a3cab9ec90e903ed6c4696b49c2a67d150`
`https://github.com/phuongub/Lab13-Observability/commit/c96a1cc3bbfac0abde44d17d4fdabfb701dc6336`

### [MEMBER_B_NAME]: Trịnh Uyên Chi
- [TASKS_COMPLETED]: 
  - Hoàn thiện CorrelationIdMiddleware trong middleware.py để tự động khởi tạo, gắn thẻ correlation_id, dọn dẹp context và đo lường thời gian xử lý (latency) cho từng request.
  - Cấu hình bind_contextvars trong main.py để theo dấu ngữ cảnh (user_id_hash bảo mật, session_id, feature, model, env)
  - Viết lại mock_rag.py và mock_llm.py theo chủ đề Chatbot hỗ trợ tư vấn quần áo cho shop thời trang.
  - Xây dựng tệp dữ liệu test (test_queries.jsonl) bao phủ toàn bộ các tình huống người dùng thực tế để phục vụ cho việc Load Test và kiểm tra luồng Tracing.
  - Chạy kịch bản load_test.py và xác nhận dữ liệu log/tracing xuất ra đầy đủ, mượt mà và không bị nghẽn (HTTP 200).
- [EVIDENCE_LINK]: 
  - Commit hash:
`4e07b36405cf2a00f28196d84ad6b227cd8385c9`
`cad5c2f8baf8c1b1115cb5f6c86e2f0aac9f4b16`
  - Commit link:
`https://github.com/VinUni-AI20k/Lab13-Observability/commit/4e07b36405cf2a00f28196d84ad6b227cd8385c9`
`https://github.com/VinUni-AI20k/Lab13-Observability/commit/cad5c2f8baf8c1b1115cb5f6c86e2f0aac9f4b16`

### [MEMBER_C_NAME]: Nguyễn Hoàng Nghĩa
- [TASKS_COMPLETED]: 
  - Xác định các Service Level Objectives (SLOs) cho các chỉ số hệ thống quan trọng
  - Thiết kế và triển khai các quy tắc cảnh báo trong file config/alert_rules.yaml
  - Căn chỉnh ngưỡng cảnh báo phù hợp với mục tiêu SLO (cảnh báo sớm trước khi vi phạm SLO) và xây dựng tài liệu hướng dẫn xử lý cảnh báo trong docs/alerts.md
- [EVIDENCE_LINK] 
  - Commit hash: `43f4f50fd7adc3e54794efe008de05b1769a79ee`
  - Commit link:
`https://github.com/VinUni-AI20k/Lab13-Observability/commit/43f4f50fd7adc3e54794efe008de05b1769a79ee`

### [MEMBER_D_NAME]: Trần Việt Phương 
- [TASKS_COMPLETED]: Incident injection, load test.Bổ sung 3 incidents tương ứng với các Alert cơ bản.  File đã sửa: scripts/inject_incident.py; app/incidents.py, data/incidents.json. 
- [EVIDENCE_LINK]: 
  - Commit hash: `2c8d01b8f1f7a35da2095a212ea2da87a1f80eda`
  - Commit link: `https://github.com/phuongub/Lab13-Observability/tree/2c8d01b8f1f7a35da2095a212ea2da87a1f80eda87a1f80eda`

### [MEMBER_E_NAME] Nguyễn Thị Thùy Trang
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
