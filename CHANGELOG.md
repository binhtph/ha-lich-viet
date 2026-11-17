# v1.0.0

Phiên bản đầu tiên của Lịch Việt cho Home Assistant.

## Tính năng
- Lịch âm Việt Nam (UTC+7): đổi ngày âm ↔ dương, tháng nhuận, can chi ngày/tháng/năm, con giáp, 24 tiết khí, giờ hoàng đạo.
- Ngày lễ dựng sẵn theo dương lịch và âm lịch, Tết Thanh minh, mùng 1 và rằm hằng tháng; ngày nghỉ lễ tô đỏ.
- Sự kiện gia đình (giỗ, sinh nhật, kỷ niệm) theo âm hoặc dương lịch, tự tính "năm thứ N" hoặc "N tuổi".
- Trang **Lịch Việt** trên sidebar cho mọi người xem:
  - Thẻ hôm nay và đếm ngược Tết.
  - Lưới tháng có icon và tên ngày lễ; ô mùng 1, rằm có màu riêng.
  - Danh sách sắp tới.
  - Quản lý sự kiện gia đình (chỉ admin).
- Ảnh nền phong cảnh từ thư mục ảnh (ưu tiên thư mục theo dịp lễ), kết hợp Unsplash nếu muốn.
- Bản tin buổi sáng qua Telegram và app điện thoại:
  - Sự kiện hôm nay.
  - Nhắc trước ngày lễ, mùng 1, rằm, giỗ.
  - Bật/tắt từng kênh bằng công tắc.
- Entity cho automation: sensor âm lịch, sự kiện hôm nay, sự kiện sắp tới, đếm ngược Tết, tiết khí; binary sensor ngày nghỉ lễ, mùng 1, rằm, có sự kiện; calendar entity.

## Yêu cầu
Home Assistant 2025.6 trở lên (icon riêng của integration hiển thị từ 2026.3).
