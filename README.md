# Lịch Việt cho Home Assistant (`lich_viet`)

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Release](https://img.shields.io/github/v/release/binhtph/ha-lich-viet)](https://github.com/binhtph/ha-lich-viet/releases)
[![Validate](https://github.com/binhtph/ha-lich-viet/actions/workflows/validate.yml/badge.svg)](https://github.com/binhtph/ha-lich-viet/actions/workflows/validate.yml)
[![Tests](https://github.com/binhtph/ha-lich-viet/actions/workflows/tests.yml/badge.svg)](https://github.com/binhtph/ha-lich-viet/actions/workflows/tests.yml)
[![License](https://img.shields.io/github/license/binhtph/ha-lich-viet)](LICENSE)

[![Mở trong HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=binhtph&repository=ha-lich-viet&category=integration)

Integration này thêm lịch âm Việt Nam, ngày lễ và sự kiện gia đình vào Home Assistant, kèm một **trang Lịch Việt trên sidebar** cho mọi người trong nhà cùng xem. Phần tính lịch viết thuần Python, không cần thư viện ngoài. Giao diện là một file JavaScript dùng thẳng, không cần build.

- **Đổi ngày âm ↔ dương** theo thuật toán thiên văn của Hồ Ngọc Đức, tính theo múi giờ Việt Nam (UTC+7), đúng cả những năm Việt Nam ăn Tết khác Trung Quốc (1985, 2007, 2030). Có tháng nhuận, can chi của ngày/tháng/năm, con giáp, 24 tiết khí và giờ hoàng đạo.
- **Ngày lễ dựng sẵn**, mỗi lễ có icon và màu riêng; ngày nghỉ lễ chính thức tô đỏ.
  - Dương lịch: Tết Dương lịch, 3/2, 14/2, 8/3, 30/4, 1/5, 19/5, 1/6, 28/6, 27/7, Quốc khánh, 20/10, 20/11, 22/12, Giáng sinh.
  - Âm lịch: Tết Nguyên Đán (mùng 1–3), Rằm tháng Giêng, Hàn thực, Giỗ Tổ, Phật Đản, Đoan Ngọ, Vu Lan, Trung thu, Hạ nguyên, ông Công ông Táo, Giao thừa.
  - Tết Thanh minh (tính theo tiết khí), và mùng 1, rằm hằng tháng (kể cả tháng nhuận).
- **Sự kiện gia đình**: sinh nhật, giỗ, kỷ niệm, theo dương hoặc âm lịch, có nhắc trước N ngày.
  - Chọn **lặp lại hằng năm** hoặc **chỉ một lần** (sự kiện một lần phải nhập năm).
  - Nhập năm thì có **tag số năm**: sinh nhật 21/12/1994 năm 2026 hiện "32 tuổi"; giỗ, kỷ niệm hiện "N năm". Đúng năm bắt đầu (ngày sinh, ngày cưới) không ghi số; năm sau là "1 năm".
  - Lùi lịch về **trước năm đã nhập** thì không thấy sự kiện. Ngày cưới nhập năm sau thì chỉ hiện từ năm đó trở đi. Sự kiện âm lịch so theo năm âm.
  - Giỗ ngày 30 âm mà năm đó tháng thiếu thì tính vào ngày 29. Sinh nhật 29/2 thì năm không nhuận tính vào 28/2.
- **Ảnh nền phong cảnh** lấy từ thư mục ảnh của bạn (ưu tiên thư mục theo dịp lễ), kết hợp ảnh Unsplash nếu muốn.
- **Bản tin buổi sáng** gửi qua Telegram và app điện thoại. Mỗi kênh có công tắc bật/tắt riêng.

## Cài đặt

**HACS:** bấm nút **Mở trong HACS** ở đầu trang (hoặc HACS → ⋮ → Custom repositories → dán link repo, chọn loại *Integration*) → Download → khởi động lại Home Assistant. Khi repo đã có trong kho mặc định của HACS, chỉ cần tìm tên integration trong HACS.

**Thủ công:** chép `custom_components/lich_viet` vào `/config/custom_components/`, rồi khởi động lại Home Assistant.

Sau đó vào **Settings → Devices & services → Add integration → "Vietnamese Lunar Calendar"**, rồi bấm Submit. Không cần nhập gì; mục **Lịch Việt** sẽ xuất hiện trên sidebar.

## Trang Lịch Việt (sidebar)

- **Thẻ hôm nay**: ngày dương, ngày âm, can chi, tiết khí, giờ hoàng đạo, tháng âm đủ hay thiếu, đếm ngược tới Tết.
- **Lưới tháng**: tuần bắt đầu từ thứ Hai. Ngày âm nằm ở góc ô (mùng 1 ghi đủ "1/10"). Icon màu đánh dấu ngày lễ.
- **Bấm vào một ngày** để xem chi tiết ngày đó; bấm "Hôm nay" để quay về.
- **Sắp tới**: các ngày lễ và sự kiện trong 45 ngày tới.
- **Sự kiện gia đình**: ai cũng xem được, chỉ tài khoản **admin** thêm/sửa/xóa được (xóa phải bấm xác nhận hai lần).
- **Ảnh nền**: các thẻ trong suốt kiểu kính mờ, tự theo theme sáng/tối của HA. Nút "Đổi ảnh" để lấy ảnh khác; góc dưới ghi tên địa danh hoặc tác giả ảnh Unsplash.
- Dùng tốt trên điện thoại: các thẻ tự xếp dọc, lưới lịch gọn lại.

## Ảnh nền

Ảnh đặt trong `/media/lich_viet/` (đổi được trong Configure → Ảnh nền). Khi cài, integration tự tạo sẵn các thư mục:

| Thư mục | Dùng khi |
|---|---|
| `chung/` | Ngày thường |
| `tet/` | 7 ngày trước đến 7 ngày sau Tết |
| `trung_thu/` | 5 ngày trước Trung thu |
| `quoc_khanh/` | 1/9 – 3/9 |
| `giai_phong/` | 29/4 – 1/5 |
| `giang_sinh/` | 20/12 – 26/12 |
| `vu_lan/` | Ngày trước và ngày Vu Lan |

- **Tải ảnh lên**: dùng **Media → Local media → lich_viet** ngay trong HA, hoặc Samba/File editor.
- **Tên file thành tên địa danh**: `Vịnh Hạ Long.jpg` hiện "Vịnh Hạ Long"; `sa-pa.jpg` hiện "Sa pa". Đặt tên có dấu cho đẹp.
- **Kích thước ảnh**: nên dùng ảnh khoảng 1920–2560 px chiều ngang, dưới 1 MB, để trang mở nhanh trên điện thoại.
- **Unsplash (tùy chọn)**:
  - Đăng ký Access Key miễn phí tại unsplash.com/developers, dán vào Configure → Ảnh nền.
  - Ảnh chỉ lấy từ Unsplash khi thư mục trống, trừ khi bật tùy chọn trộn ảnh.
  - Integration gọi API tối đa một lần mỗi ngày (lấy 30 ảnh), và ghi tên tác giả theo yêu cầu của Unsplash.
- **Cách chọn ảnh**:
  - "Mỗi ngày một ảnh": cả nhà thấy cùng một ảnh trong ngày.
  - "Mỗi lần mở trang": ảnh ngẫu nhiên.
  - Nút "Đổi ảnh": đổi luôn ảnh của hôm nay.

## Cấu hình (Configure)

| Mục | Nội dung |
|---|---|
| Thông báo | Kênh Telegram (notify entity của bot), app điện thoại (`mobile_app_*`), giờ gửi bản tin, chỉ gửi khi có sự kiện, nhắc trước ngày lễ bao nhiêu ngày, nhắc trước mùng 1 và rằm bao nhiêu ngày (mặc định 1) |
| Ảnh nền | Bật/tắt, cách đổi ảnh, thư mục ảnh, Unsplash key và từ khóa, trộn ảnh, độ đặc của các thẻ |

Bản tin buổi sáng có:
- Ngày âm lịch và can chi của ngày.
- Sự kiện hôm nay (kể cả mùng 1, rằm).
- Lời nhắc giỗ/sinh nhật theo số ngày cài riêng cho từng sự kiện.
- Lời nhắc ngày lễ trước N ngày.
- Lời nhắc trước mùng 1 và rằm, ví dụ "Rằm tháng 11: ngày mai (Thứ Tư 23/12)". Rằm trùng ngày lễ có tên (Rằm tháng Giêng, Phật Đản, Vu Lan, Trung thu, Hạ nguyên) được nhắc theo mục ngày lễ, không nhắc trùng hai lần.

Mặc định chỉ gửi khi có sự kiện hoặc lời nhắc.

## Entity

| Entity | Ý nghĩa |
|---|---|
| `sensor.lich_viet_lunar_date` | "Mùng 9 tháng 10"; thuộc tính có ngày/tháng/năm âm, tháng nhuận, can chi, con giáp, tiết khí, giờ hoàng đạo |
| `sensor.lich_viet_events_today` | Tên các sự kiện hôm nay ("Không có" nếu trống) |
| `sensor.lich_viet_next_event` | Ngày lễ hoặc sự kiện gần nhất, kèm số ngày còn lại |
| `sensor.lich_viet_days_until_tet` | Số ngày còn lại tới Tết |
| `sensor.lich_viet_solar_term` | Tiết khí hiện tại và tiết kế tiếp |
| `binary_sensor.lich_viet_public_holiday` | Hôm nay là ngày nghỉ lễ |
| `binary_sensor.lich_viet_first_lunar_day` | Hôm nay là mùng 1 |
| `binary_sensor.lich_viet_full_moon_day` | Hôm nay là ngày rằm |
| `binary_sensor.lich_viet_has_event` | Hôm nay có sự kiện |
| `calendar.lich_viet_calendar` | Toàn bộ ngày lễ và sự kiện; xem được trong mục Lịch (Calendar) của HA, dùng làm trigger cho automation |
| `switch.lich_viet_*` | Bật/tắt bản tin buổi sáng và từng kênh gửi |
| `button.lich_viet_send_report_now` | Gửi thử bản tin ngay |

Tên hiển thị là tiếng Việt; entity_id sinh theo tiếng Anh.

### Ví dụ automation: nhắc lịch ăn chay

Automation này nhắc **20:00 tối hôm trước** ("Ngày mai ăn chay") và **06:00 sáng** ngày ăn chay. Ngày ăn chay khai báo trong `ngay_chay` theo ngày âm lịch:

| Lịch ăn chay | `ngay_chay` |
|---|---|
| 2 ngày (mùng 1, rằm) | `[1, 15]` |
| 4 ngày | `[1, 14, 15, 30]` |
| 10 ngày | `[1, 8, 14, 15, 18, 23, 24, 28, 29, 30]` |

Số `30` nghĩa là ngày cuối tháng âm: tháng thiếu (29 ngày) thì tự tính vào ngày 29.

```yaml
alias: Nhắc lịch ăn chay
description: Nhắc tối hôm trước và sáng ngày ăn chay theo lịch âm
mode: single
triggers:
  - trigger: time
    at: "20:00:00"
    id: toi_hom_truoc
  - trigger: time
    at: "06:00:00"
    id: sang_hom_nay
variables:
  ngay_chay: [1, 15]
  hom_nay: "{{ state_attr('sensor.lich_viet_lunar_date', 'ngay') | int(0) }}"
  so_ngay: "{{ state_attr('sensor.lich_viet_lunar_date', 'so_ngay_trong_thang') | int(30) }}"
  la_toi: "{{ trigger.id == 'toi_hom_truoc' }}"
  ngay_xet: "{{ (1 if hom_nay == so_ngay else hom_nay + 1) if la_toi else hom_nay }}"
  cuoi_thang: "{{ (hom_nay + 1 == so_ngay) if la_toi else (hom_nay == so_ngay) }}"
  la_ngay_chay: "{{ hom_nay > 0 and (ngay_xet in ngay_chay or (30 in ngay_chay and cuoi_thang)) }}"
  ten_ngay: >-
    {{ 'mùng 1' if ngay_xet == 1 else 'rằm' if ngay_xet == 15
       else 'ngày cuối tháng' if cuoi_thang else 'ngày ' ~ ngay_xet }}
conditions:
  - condition: template
    value_template: "{{ la_ngay_chay }}"
actions:
  - action: notify.notify
    data:
      title: "🥗 Lịch ăn chay"
      message: >-
        {{ 'Ngày mai' if la_toi else 'Hôm nay' }} là {{ ten_ngay }} âm lịch, nhớ ăn chay.
```

Đổi `notify.notify` thành kênh bạn dùng, ví dụ `notify.mobile_app_<tên_điện_thoại>`. Muốn gửi Telegram thì dùng action `telegram_bot.send_message`.

## Kiểm thử (dành cho người phát triển)

```bash
pip install -r requirements_test.txt
pytest                       # Python: lịch âm, ngày lễ, integration HA
npm install && npm test      # Giao diện sidebar (jsdom)
```

Phần tính lịch được kiểm thử bằng các cách sau:
- Đối chiếu ngày Tết 1985–2030 và tháng nhuận 2000–2030.
- Chuyển đổi âm ↔ dương khứ hồi cho mọi ngày từ 1900 đến 2150.
- Chạy cùng thuật toán với UTC+8 và so với bảng lịch chính thức của Trung Quốc (thư viện `lunardate`) cho mọi ngày 1979–2090.
- Đối chiếu các ngày lễ đã biết: Giỗ Tổ, Trung thu, Vu Lan, Phật Đản, ông Táo, Giao thừa.

## Giới hạn

- Thuật toán thiên văn là gần đúng. Ngoài khoảng 1979–2090, hiếm khi có tháng mà thời điểm trăng mới rơi sát nửa đêm, khiến ngày đầu tháng lệch 1 ngày.
- Ngày nghỉ bù và kỳ nghỉ Tết theo quyết định của Chính phủ từng năm không được tính; chỉ đánh dấu các ngày lễ cố định.

## Giấy phép

MIT. Xem file [LICENSE](LICENSE).
