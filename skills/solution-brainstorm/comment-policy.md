# Comment policy

Nguồn duy nhất cho quy tắc comment trong code do workflow viết hoặc sửa. Đọc bởi `/solution-brainstorm`
(skeleton và bước implement ngay sau brainstorm) và các agent `fw-3`, `fw-5`, `fw-6`, `fw-7`. Sửa quy tắc
ở đây, không chép lại vào skill hay agent.

## Mặc định

Không comment. Trước khi định viết comment: đổi tên biến/hàm, tách hàm, đơn giản hoá logic để code tự
giải thích. Chỉ khi vẫn còn điều code không thể hiện được thì mới comment.

## Được giữ (chỉ WHY)

- Ràng buộc ẩn: thứ tự gọi bắt buộc, giới hạn của API/thiết bị, yêu cầu thread.
- Workaround: lý do và điều kiện để gỡ bỏ.
- Tham chiếu bug, issue, spec, RFC khi quyết định không hiển nhiên.
- Doc API công khai và license header khi convention của dự án đích yêu cầu.
- Marker `// pseudo` trong skeleton của `/solution-brainstorm` khi không chắc API.

## Không viết

- Comment lặp lại code (`// increment i`, `// return result`, `// constructor`).
- Nhãn, banner, phân đoạn (`// ===== Helpers =====`, `// region`).
- Changelog trong code (`// fixed ...`, `// sửa lỗi ...`, `// added for ...`) - lịch sử đã có ở git.
- Tên tác giả, ngày tháng.
- Commented-out code.
- TODO không có issue đi kèm.
- Doc comment chỉ nhắc lại tên hàm và tham số trên code nội bộ.

## Ví dụ

```kotlin
// Xấu: lặp code
// Check if user is adult
if (user.age >= 18) { ... }

// Tốt: tên tự giải thích, không cần comment
if (user.isAdult) { ... }

// Tốt: WHY mà code không thể hiện
// Firmware v2 drops packets under 20 ms apart (issue #312)
delay(MIN_PACKET_GAP)
```

## Phạm vi

Chỉ áp dụng cho code bạn viết hoặc sửa. Không xoá comment có sẵn ngoài phạm vi thay đổi. Không áp
dụng cho báo cáo markdown trong `.workflows/`.

## Mức độ khi review

| Mức | Khi nào |
|---|---|
| Major | Commented-out code, hoặc comment thừa lặp lại có hệ thống (từ 3 chỗ trong diff) |
| Minor | Comment thừa lẻ tẻ |

Comment WHY đúng mục "Được giữ" thì không phải finding.
