from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .incidents import STATE


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    def generate(self, prompt: str) -> FakeResponse:
        # Thời gian AI suy nghĩ (để tracing ghi nhận được latency)
        time.sleep(0.15)
        
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(60, 180)
        
        # Sự cố: AI bị "ngáo", sinh ra quá nhiều text gây tốn chi phí
        if STATE["cost_spike"]:
            output_tokens *= 4
            
        lowered_prompt = prompt.lower()
        answer = ""

        # Logic: Xử lý trường hợp RAG không tìm thấy thông tin
        if "không tìm thấy thông tin" in lowered_prompt or "chưa tìm thấy" in lowered_prompt:
            answer = "Dạ chào bạn, mình là trợ lý ảo của shop. Hiện tại câu hỏi này hơi khó với mình hoặc sản phẩm bạn hỏi chưa có trên hệ thống, bạn vui lòng để lại số điện thoại hoặc nhắn tin trực tiếp để nhân viên chăm sóc khách hàng hỗ trợ bạn ngay nha! 💕"
            return FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)

        # Logic: Trả lời dựa trên các keyword quét được từ prompt (bao gồm cả RAG Context và User Question)
        answer = "Dạ, "
        
        if "size" in lowered_prompt or "kích cỡ" in lowered_prompt:
            answer += "form đồ bên shop chuẩn lắm ạ. Bạn xem qua bảng size ở trên, hoặc nhắn trực tiếp chiều cao, cân nặng để em tư vấn size vừa y cho mình nhé."
            
        elif "đổi trả" in lowered_prompt or "hoàn tiền" in lowered_prompt:
            answer += "shop luôn hỗ trợ đổi trả và hoàn tiền nhanh chóng nếu hàng có vấn đề ạ. Mình cứ yên tâm mua sắm nha, nhớ quay video bóc hàng giúp shop là được ạ!"
            
        elif "ship" in lowered_prompt or "giao hàng" in lowered_prompt:
            answer += "bên em có hỗ trợ ship COD và giao hỏa tốc nội thành luôn đó ạ. Đặc biệt đơn từ 500k là được freeship toàn quốc luôn nha."
            
        elif "phối đồ" in lowered_prompt or "style" in lowered_prompt:
            answer += "item này bên shop bán siêu chạy vì cực kỳ dễ phối đồ luôn ạ. Mặc đi chơi hay đi làm đều mang lại giao diện xuất sắc."
            
        elif "chất liệu" in lowered_prompt or "giặt" in lowered_prompt:
            answer += "về chất vải thì shop cam kết lên form đẹp, thấm hút mồ hôi và không lo bai nhão khi giặt máy đâu ạ."
            
        elif "khuyến mãi" in lowered_prompt or "giảm giá" in lowered_prompt or "voucher" in lowered_prompt:
            answer += "shop đang có chương trình ưu đãi rất hời ạ! Bạn nhớ nhập mã giảm giá khi thanh toán hoặc chốt từ 3 món để được hệ thống tự động giảm thêm nha."
            
        elif "thanh toán" in lowered_prompt or "kiểm hàng" in lowered_prompt:
            answer += "bên em cho khách đồng kiểm trước khi nhận hàng luôn ạ. Bạn có thể thanh toán tiền mặt (COD), chuyển khoản hay ví điện tử đều được nhé."
            
        elif "địa chỉ" in lowered_prompt or "giờ mở cửa" in lowered_prompt or "ở đâu" in lowered_prompt:
            answer += "shop có các chi nhánh mở cửa cả ngày luôn ạ. Nếu tiện đường, bạn cứ ghé 123 Lê Văn Sỹ (Q.3) hoặc 456 Quang Trung (Gò Vấp) thử đồ trực tiếp nha, ở ngoài nhiều mẫu xinh lắm ạ!"
            
        elif "mẫu mặc" in lowered_prompt or "thông tin mẫu" in lowered_prompt:
            answer += "bạn có thể tham khảo số đo của bạn mẫu ở trên để dễ hình dung form áo nha. Nếu mình khác form mẫu, nhắn shop để shop tư vấn thêm ạ."
            
        elif "còn hàng" in lowered_prompt or "đặt trước" in lowered_prompt:
            answer += "đa số mẫu trên kệ là hàng có sẵn, chốt đơn là shop gửi đi liền ạ. Nếu là mẫu Pre-order (đặt trước) thì shop sẽ giảm thêm 20k cho mình bù thời gian đợi nha!"
            
        else:
            answer += "thông tin chi tiết như tài liệu trên ạ. Bạn còn băn khoăn hay muốn xem thêm ảnh thật của mẫu nào thì cứ nhắn em nhé!"

        return FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)