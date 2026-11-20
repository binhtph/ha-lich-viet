# v1.2.3

## Thay đổi
- Lời nhắc giỗ và sự kiện gia đình cài theo âm lịch trong bản tin ghi kèm ngày âm (sự kiện cài theo dương lịch thì không), vd. "Còn 3 ngày (T4 23/12 · 15/11 ÂL): Giỗ ông nội (16 năm)", "Ngày mai (15/11 ÂL): Giỗ ông nội (16 năm)".

# v1.2.2

## Thay đổi
- Bản tin buổi sáng viết gọn để đọc đủ trên màn hình khóa:
  - Tiêu đề có thứ viết tắt, ngày dương và ngày âm, vd. `📅 LỊCH VIỆT › T6 20/11 · 12/10 ÂL`.
  - Mỗi mốc một dòng: "Hôm nay: …", "Ngày mai: …", "Còn N ngày (T4 23/12): …". Nhiều sự kiện cùng ngày gộp một dòng.
  - Can chi ngày và năm chuyển xuống dòng cuối.
- Telegram và app điện thoại nhận cùng một tiêu đề và nội dung (Telegram chỉ in đậm tiêu đề).

# v1.2.1

## Thay đổi
- Bản tin gửi qua app điện thoại (`notify.mobile_app_*`): nhấn vào thông báo thì mở thẳng trang **Lịch Việt** (`/lich-viet`). iOS dùng `url`, Android dùng `clickAction`. Tin Telegram không đổi.

# v1.2.0

## Thêm
- **Ngày Văn hóa Việt Nam (24/11)**: ngày nghỉ lễ hưởng nguyên lương từ năm 2026 (Nghị quyết 28/2026/QH16). Ô lịch tô đỏ, có trong danh sách sắp tới, bản tin, calendar entity và `binary_sensor.lich_viet_public_holiday`. Các năm trước 2026 không hiện ngày này.
- README có ảnh chụp màn hình (máy tính, theme tối, điện thoại, hộp thoại thêm sự kiện).

# v1.1.1

## Bảo mật
- Chỉ gửi Unsplash access key tới `https://api.unsplash.com`. Nếu `download_location` trong phản hồi của Unsplash trỏ sang host khác thì bỏ qua, không gửi header `Authorization`. Không theo redirect khi báo lượt tải.

# v1.1.0

## Thêm
- Sự kiện gia đình có tùy chọn **Lặp lại hằng năm / Chỉ một lần** (sự kiện một lần phải nhập năm).
- **Tag số năm** trên lưới tháng, danh sách sắp tới, thẻ ngày và bản tin: sinh nhật ghi "N tuổi", giỗ và kỷ niệm ghi "N năm".

## Thay đổi
- Sự kiện có nhập năm không còn hiện ở những năm trước năm đó (vd. ngày cưới năm sau chỉ hiện từ năm đó). Năm bắt đầu không ghi số, năm sau là "1 năm".
- Hộp thoại thêm sự kiện: mặc định loại **Sinh nhật**, lịch **Dương lịch**. Thứ tự loại: Sinh nhật, Giỗ, Kỷ niệm, Khác. Chọn Giỗ thì tự chuyển sang Âm lịch. Ô tên gợi ý theo loại, vd. "Sinh nhật con".
- Bản tin ghi "tuổi" hay "năm" theo loại sự kiện thay vì đoán theo tên.

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
