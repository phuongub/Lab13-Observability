# Mock Debug & Q&A — Uniqlo Fashion Chatbot (Observability Lab)

## Context hệ thống

* Use case: Chatbot tư vấn thời trang cho Uniqlo
* Kiến trúc: FastAPI + Agent + Logging + Tracing + Dashboard
* Observability stack:

  * Logging (JSON logs + PII redaction)
  * Tracing (Langfuse + custom span logs)
  * Metrics + Dashboard (Streamlit)
  * Alerts (SLO-based)

---

# 1. Câu hỏi về tổng quan hệ thống

### Hệ thống của nhóm bạn làm gì?

Chatbot hỗ trợ tư vấn thời trang:

* chọn size
* phối đồ
* tư vấn chất liệu
* chính sách đổi trả, vận chuyển

---

### Vì sao cần observability cho chatbot?

Vì chatbot có:

* latency từ LLM
* chi phí (token)
* chất lượng khó đo
* nhiều step (retrieval + LLM)

→ cần logging + tracing để debug & monitor

---

# 2. Debug scenario (rất hay bị hỏi)

---

## Case 1: User hỏi nhưng trả lời sai

### Ví dụ:

> “Tôi cao 1m6 nặng 50kg mặc size gì?”

### Debug flow:

1. Check log:

```json
"feature": "qa"
"route": "/chat"
```

2. Check trace:

* api_gateway → chat_service → model_inference

3. Check retrieval:

```json
"doc_count": 0
```

Nguyên nhân: không retrieve được context

---

## Case 2: Latency tăng cao

### Debug:

Dashboard:

* Latency P95 tăng

Trace:

```text
model_inference → 2000ms
```

Nguyên nhân:

* LLM chậm
* prompt dài

---

## Case 3: Cost tăng bất thường

Dashboard:

```text
Max Cost / min ↑
```

Trace:

```json
tokens_in ↑
tokens_out ↑
```

Nguyên nhân:

* prompt quá dài
* user spam

---

## Case 4: Error 500

Log:

```json
"event": "request_failed"
```

Trace:

* dừng ở chat_service

Debug:

* xem exception
* kiểm tra agent.run()

---

# 3. Bảo mật & PII

---

## Bạn xử lý dữ liệu nhạy cảm như thế nào?

Trong log:

```json
"user_id_hash": "abc123"
```

Không lưu:

* số điện thoại
* địa chỉ

Nếu có:

```text
0912345678 → [REDACTED]
```

---

# 4. Dashboard

---

## Dashboard có gì?

6 panels:

1. Latency
2. Traffic
3. Error rate
4. Cost
5. Tokens
6. Quality proxy

---

## Route breakdown là gì?

Phân phối request theo endpoint:

```text
/chat → 80%
/health → 10%
/metrics → 10%
```

---

# 5. Alerts

---

## Alert hoạt động thế nào?

Config:

```yaml
latency_p95_ms:
  threshold: 2000
```

Dashboard:

```text
High latency
```

---

## Khi alert xảy ra thì làm gì?

Runbook:

* check trace
* check model latency
* check traffic spike

---

# 6. Tracing

---

## Trace là gì?

Một request end-to-end:

```text
api_gateway
  → chat_service
    → model_inference
```

---

## Bạn trace như thế nào?

* Langfuse (`@observe()`)
* custom span logs:

```text
trace_id
span_id
service
```

---

## Nếu Langfuse không hoạt động thì sao?

fallback:

* dùng log-based tracing trong dashboard

---

# 7. Load test & Incident

---

## Bạn test hệ thống như thế nào?

```bash
python scripts/load_test.py -c 5
```

---

## Incident injection là gì?

giả lập lỗi:

```bash
POST /incidents/slow_response/enable
```

→ latency tăng → alert trigger

---

# 8. Trade-off (rất hay hỏi)

---

## Logging nhiều có vấn đề gì?

* tăng cost
* tăng storage

---

## Tracing có ảnh hưởng performance không?

Có, nhưng:

* chấp nhận được
* cần sampling trong production

---

# 9. Demo script (bạn nên nói)

---

### Step 1:

“Đây là dashboard, hiển thị 6 metrics chính.”

### Step 2:

“Chúng tôi gửi request → trace được tạo”

### Step 3:

“Mỗi request có trace_id → có thể debug end-to-end”

### Step 4:

“Khi có vấn đề, chúng tôi dùng:

* dashboard → detect
* trace → root cause”

---

# 10. Câu hỏi khó (bonus)

---

## Làm sao scale hệ thống này?

* stateless API
* load balancing
* external storage (Redis, DB)

---

## Làm sao giảm cost?

* prompt optimization
* caching
* model selection

---

## Làm sao đo chất lượng chatbot?

dùng proxy:

* length
* keyword match
* feedback user

---

# Kết luận

Hệ thống của nhóm:

* có observability đầy đủ
* debug được end-to-end
* sẵn sàng production-level (ở mức demo)

---
