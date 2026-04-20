<<<<<<< HEAD
from __future__ import annotations

import time

from .incidents import STATE

# MOCK DATA: Bộ tri thức (Knowledge Base) của Shop Thời Trang
CORPUS = {
    "size": ["Bảng size chuẩn: S (dưới 45kg), M (45-55kg), L (55-65kg). Form áo bên shop là form rộng (oversize)."],
    "kích cỡ": ["Bảng size chuẩn: S (dưới 45kg), M (45-55kg), L (55-65kg). Form áo bên shop là form rộng (oversize)."],
    
    "đổi trả": ["Shop hỗ trợ đổi trả trong vòng 7 ngày nếu lỗi do nhà sản xuất hoặc không vừa size. Sản phẩm phải còn nguyên tem mác, chưa qua giặt ủi và không bị dính bẩn."],
    "hoàn tiền": ["Shop hỗ trợ hoàn tiền qua chuyển khoản trong vòng 48h nếu phát sinh lỗi từ phía nhà sản xuất mà không có sản phẩm thay thế."],
    
    "ship": ["Phí ship nội thành là 20k. Ngoại thành và các tỉnh khác là 30k. Đặc biệt freeship cho mọi đơn hàng từ 500k."],
    "giao hàng": ["Thời gian giao hàng dự kiến: Nội thành 1-2 ngày, ngoại thành 3-4 ngày. Có hỗ trợ giao hỏa tốc qua Grab/Ahamove trong vòng 2h."],
    
    "phối đồ": ["Gợi ý mix&match: Áo thun basic rất dễ phối. Bạn có thể mặc cùng quần jeans ống rộng để hack dáng, hoặc phối với chân váy xếp ly mang lại phong cách trẻ trung, năng động."],
    "style": ["Sản phẩm này mang hơi hướng vintage/y2k. Phù hợp nhất khi đi kèm với phụ kiện như túi kẹp nách hoặc mũ lưỡi trai."],
    
    "chất liệu": ["Chất vải bên shop chủ yếu là cotton 100% thấm hút mồ hôi 2 chiều, vải linen thoáng mát hoặc nỉ lót bông dày dặn, cam kết không xù lông sau khi giặt."],
    "giặt": ["Lưu ý bảo quản: Nên lộn trái áo khi giặt, giặt bằng nước lạnh và không phơi trực tiếp dưới ánh nắng gắt để giữ màu áo được lâu nhất."],

    "khuyến mãi": ["Hiện shop đang có chương trình: Nhập mã 'HELLO' giảm 10% cho đơn đầu tiên. Follow shop trên Shopee/Lazada để lấy voucher 30k."],
    "giảm giá": ["Shop bán đúng giá niêm yết ạ. Tuy nhiên nếu bạn mua từ 3 sản phẩm sẽ được giảm 5% tổng hóa đơn nha."],
    
    "thanh toán": ["Shop chấp nhận: COD (thanh toán khi nhận hàng), Chuyển khoản ngân hàng, và ví điện tử (Momo/ZaloPay)."],
    "kiểm hàng": ["Dạ khách luôn được KIỂM TRA HÀNG trước khi thanh toán nên mình cứ yên tâm đặt đồ nhé!"],
    
    "địa chỉ": ["Shop có 2 chi nhánh tại TP.HCM: 123 Lê Văn Sỹ (Q.3) và 456 Quang Trung (Gò Vấp)."],
    "giờ mở cửa": ["Shop mở cửa từ 9:00 sáng đến 10:00 tối tất cả các ngày trong tuần ạ."],
    
    "thông tin mẫu": ["Bạn mẫu trong ảnh cao 1m62, nặng 48kg, hiện đang mặc size S để lên form ôm dáng ạ."],
    "mẫu mặc": ["Mẫu thường mặc size S hoặc M tùy form. Bạn có thể dựa vào thông số này để chọn size tương ứng nhé."],
    
    "còn hàng": ["Dạ hầu hết các mẫu trên kệ đều có sẵn. Tuy nhiên một số item hot có thể hết size nhanh, bạn báo tên mẫu để shop check kho ngay nhé."],
    "đặt trước": ["Với các mẫu Pre-order, thời gian chờ khoảng 7-10 ngày. Shop sẽ giảm ngay 20k cho mỗi sản phẩm đặt trước để cảm ơn bạn đã kiên nhẫn ạ."]
}

def retrieve(message: str) -> list[str]:
    # Giả lập lỗi hệ thống RAG sập (Vector store timeout)
    if STATE["tool_fail"]:
        raise RuntimeError("Lỗi mất kết nối đến cơ sở dữ liệu tri thức của Shop")
    
    # Giả lập RAG phản hồi chậm (Slow API)
    if STATE["rag_slow"]:
        time.sleep(2.5)
        
    lowered = message.lower()
    results = []
    
    # Quét qua tin nhắn của user xem có trúng từ khóa nào không
    for key, docs in CORPUS.items():
        if key in lowered:
            results.extend(docs)
            
    if results:
        # Dùng set() để loại bỏ các câu trả lời trùng lặp nếu user gõ nhiều từ khóa cùng lúc
        return list(set(results))
        
=======
from __future__ import annotations

import time

from .incidents import STATE

# MOCK DATA: Bộ tri thức (Knowledge Base) của Shop Thời Trang
CORPUS = {
    "size": ["Bảng size chuẩn: S (dưới 45kg), M (45-55kg), L (55-65kg). Form áo bên shop là form rộng (oversize)."],
    "kích cỡ": ["Bảng size chuẩn: S (dưới 45kg), M (45-55kg), L (55-65kg). Form áo bên shop là form rộng (oversize)."],
    
    "đổi trả": ["Shop hỗ trợ đổi trả trong vòng 7 ngày nếu lỗi do nhà sản xuất hoặc không vừa size. Sản phẩm phải còn nguyên tem mác, chưa qua giặt ủi và không bị dính bẩn."],
    "hoàn tiền": ["Shop hỗ trợ hoàn tiền qua chuyển khoản trong vòng 48h nếu phát sinh lỗi từ phía nhà sản xuất mà không có sản phẩm thay thế."],
    
    "ship": ["Phí ship nội thành là 20k. Ngoại thành và các tỉnh khác là 30k. Đặc biệt freeship cho mọi đơn hàng từ 500k."],
    "giao hàng": ["Thời gian giao hàng dự kiến: Nội thành 1-2 ngày, ngoại thành 3-4 ngày. Có hỗ trợ giao hỏa tốc qua Grab/Ahamove trong vòng 2h."],
    
    "phối đồ": ["Gợi ý mix&match: Áo thun basic rất dễ phối. Bạn có thể mặc cùng quần jeans ống rộng để hack dáng, hoặc phối với chân váy xếp ly mang lại phong cách trẻ trung, năng động."],
    "style": ["Sản phẩm này mang hơi hướng vintage/y2k. Phù hợp nhất khi đi kèm với phụ kiện như túi kẹp nách hoặc mũ lưỡi trai."],
    
    "chất liệu": ["Chất vải bên shop chủ yếu là cotton 100% thấm hút mồ hôi 2 chiều, vải linen thoáng mát hoặc nỉ lót bông dày dặn, cam kết không xù lông sau khi giặt."],
    "giặt": ["Lưu ý bảo quản: Nên lộn trái áo khi giặt, giặt bằng nước lạnh và không phơi trực tiếp dưới ánh nắng gắt để giữ màu áo được lâu nhất."],

    "khuyến mãi": ["Hiện shop đang có chương trình: Nhập mã 'HELLO' giảm 10% cho đơn đầu tiên. Follow shop trên Shopee/Lazada để lấy voucher 30k."],
    "giảm giá": ["Shop bán đúng giá niêm yết ạ. Tuy nhiên nếu bạn mua từ 3 sản phẩm sẽ được giảm 5% tổng hóa đơn nha."],
    
    "thanh toán": ["Shop chấp nhận: COD (thanh toán khi nhận hàng), Chuyển khoản ngân hàng, và ví điện tử (Momo/ZaloPay)."],
    "kiểm hàng": ["Dạ khách luôn được KIỂM TRA HÀNG trước khi thanh toán nên mình cứ yên tâm đặt đồ nhé!"],
    
    "địa chỉ": ["Shop có 2 chi nhánh tại TP.HCM: 123 Lê Văn Sỹ (Q.3) và 456 Quang Trung (Gò Vấp)."],
    "giờ mở cửa": ["Shop mở cửa từ 9:00 sáng đến 10:00 tối tất cả các ngày trong tuần ạ."],
    
    "thông tin mẫu": ["Bạn mẫu trong ảnh cao 1m62, nặng 48kg, hiện đang mặc size S để lên form ôm dáng ạ."],
    "mẫu mặc": ["Mẫu thường mặc size S hoặc M tùy form. Bạn có thể dựa vào thông số này để chọn size tương ứng nhé."],
    
    "còn hàng": ["Dạ hầu hết các mẫu trên kệ đều có sẵn. Tuy nhiên một số item hot có thể hết size nhanh, bạn báo tên mẫu để shop check kho ngay nhé."],
    "đặt trước": ["Với các mẫu Pre-order, thời gian chờ khoảng 7-10 ngày. Shop sẽ giảm ngay 20k cho mỗi sản phẩm đặt trước để cảm ơn bạn đã kiên nhẫn ạ."]
}

def retrieve(message: str) -> list[str]:
    # Giả lập lỗi hệ thống RAG sập (Vector store timeout)
    if STATE["tool_fail"]:
        raise RuntimeError("Lỗi mất kết nối đến cơ sở dữ liệu tri thức của Shop")
    
    # Giả lập RAG phản hồi chậm (Slow API)
    if STATE["rag_slow"]:
        time.sleep(2.5)
        
    lowered = message.lower()
    results = []
    
    # Quét qua tin nhắn của user xem có trúng từ khóa nào không
    for key, docs in CORPUS.items():
        if key in lowered:
            results.extend(docs)
            
    if results:
        # Dùng set() để loại bỏ các câu trả lời trùng lặp nếu user gõ nhiều từ khóa cùng lúc
        return list(set(results))
        
>>>>>>> 0db4c94cd3d0377e0ddad0e37449d067e7513583
    return ["Hiện tại hệ thống chưa tìm thấy thông tin chi tiết về câu hỏi này. Bạn chờ một lát để nhân viên thật hỗ trợ nhé."]