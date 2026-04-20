# Alert Rules and Runbooks

## 1. High latency P95
- Severity: P2
- Trigger: `latency_p95 > 4000 for 15m`
- Impact: response chậm → giảm trải nghiệm user, tăng abandonment
- First checks:
  1. Mở trace chậm nhất trong 1h gần nhất
  2. So sánh thời gian RAG vs LLM
  3. Check xem có bật `rag_slow` trong incidents không
- Mitigation:
  - giảm kích thước prompt
  - giới hạn input/query length
  - fallback sang retrieval đơn giản hơn

## 2. Critical latency spike
- Severity: P1
- Trigger: `latency_p95 > 6000 for 5m`
- Impact: hệ thống gần như unusable → user drop mạnh
- First checks:
  1. Check toàn bộ trace có latency cao bất thường
  2. Xác định bottleneck (LLM / RAG / external API)
  3. Kiểm tra infra (CPU/memory nếu có)
- Mitigation:
  - restart service
  - scale thêm instance
  - disable feature gây chậm

## 3. High error rate
- Severity: P1
- Trigger: `error_rate_pct > 5 for 5m`
- Impact: nhiều request fail → user không nhận được kết quả
- First checks:
  1. Group log theo `error_type`
  2. Inspect trace bị fail
  3. Xác định lỗi từ LLM, RAG hay schema
- Mitigation:
  - rollback thay đổi gần nhất
  - disable component lỗi
  - retry với fallback model

## 4. Low response quality
- Severity: P2
- Trigger: `quality_avg < 0.7 for 15m`
- Impact: câu trả lời sai → giảm trust, giảm retention
- First checks:
  1. So sánh output với expected_answers
  2. Check retrieval có đúng context không
  3. Inspect trace để xem LLM output
- Mitigation:
  - cải thiện retrieval (top-k, filter)
  - refine prompt
  - fallback sang template trả lời đơn giản

## 5. Cost spike
- Severity: P2
- Trigger: `avg_cost_usd > 2x_baseline for 15m`
- Impact: chi phí tăng nhanh → vượt budget
- First checks:
  1. Phân tích trace theo feature/model
  2. So sánh tokens_in và tokens_out
  3. Check incident `cost_spike`
- Mitigation:
  - giảm token input/output
  - route request đơn giản sang model rẻ hơn
  - bật caching cho prompt