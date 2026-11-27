# Grounded Answer - Nhãn và khung trả lời

Đọc bởi `grounded-answer` ở Bước 4. Đổi nhãn, câu cố định hay khung thì sửa ở đây.

## Ba nhãn

Mỗi ý có đúng một nhãn. Tên nhãn dịch sang ngôn ngữ người hỏi, biểu tượng giữ nguyên.

| Nhãn | Khi nào | Bắt buộc có |
|---|---|---|
| ✅ Trả lời | Tài liệu nói thẳng điều được hỏi, không cần suy ra | Trích nguyên văn trong ngoặc kép, kèm `file:dòng` hoặc vị trí trong connector (tên trang, mục) |
| ⚠️ Không chắc chắn | Phải suy ra; câu trong tài liệu mơ hồ; hoặc các nguồn mâu thuẫn | Lý do một câu, và đoạn trích liên quan kèm vị trí. Mâu thuẫn thì trích cả hai bên và không chọn bên nào |
| ❌ Không biết | Các nguồn đã đọc không đề cập | Câu cố định: "Không thấy trong các nguồn đã đọc." (tiếng Anh: "Not found in the sources read.") |

- ❌ nói về các nguồn đã đọc, không khẳng định là thông tin không tồn tại ở đâu cả.
- Câu trả lời của ✅ chỉ nhắc lại điều đoạn trích nói. Thêm bất kỳ điều gì đoạn trích không nói thì ý đó là ⚠️.

## Dòng "Ngoài tài liệu (chưa kiểm)"

- Chỉ đặt dưới ý ❌ hoặc ⚠️, và chỉ khi bạn thật sự biết điều hữu ích cho người hỏi.
- Không bao giờ đặt dưới ý ✅.
- Bắt đầu bằng đúng nhãn `Ngoài tài liệu (chưa kiểm):` (tiếng Anh: `Outside the documents (unverified):`).
- Không dùng nó để chọn bên khi nguồn mâu thuẫn.

## Khung trả lời

```markdown
**1. <ý thứ nhất>** - ✅ Trả lời
<câu trả lời ngắn>
> "<trích nguyên văn>" - `<file>:<dòng>`

**2. <ý thứ hai>** - ⚠️ Không chắc chắn
Lý do: <suy ra | mơ hồ | mâu thuẫn>, <giải thích một câu>.
> "<trích nguyên văn>" - `<file>:<dòng>`

Ngoài tài liệu (chưa kiểm): <chỉ khi thật sự hữu ích>

**3. <ý thứ ba>** - ❌ Không biết
Không thấy trong các nguồn đã đọc.
Ngoài tài liệu (chưa kiểm): <chỉ khi thật sự hữu ích>

---
Nguồn đã đọc: `<file>`, `<file>`
Chưa kiểm: <nguồn hoặc phần bỏ qua, hoặc "không có">
```

## Ví dụ

Câu hỏi: "Mỗi năm được nghỉ phép bao nhiêu ngày, có được làm từ xa không, công ty có hỗ trợ gửi xe không, và thử việc kéo dài bao lâu?"
Nguồn: `handbook.md`, `onboarding.md`.

```markdown
**1. Số ngày nghỉ phép** - ✅ Trả lời
Mỗi năm được 12 ngày nghỉ phép có lương.
> "Nhân viên chính thức được 12 ngày nghỉ phép có lương mỗi năm" - `handbook.md:15`

**2. Làm từ xa** - ⚠️ Không chắc chắn
Lý do: mơ hồ, tài liệu không nói ai được duyệt và bao nhiêu ngày.
> "Làm việc từ xa được xem xét tùy theo tính chất công việc" - `handbook.md:22`

**3. Hỗ trợ gửi xe** - ❌ Không biết
Không thấy trong các nguồn đã đọc.
Ngoài tài liệu (chưa kiểm): nhiều công ty ghi chính sách gửi xe trong thông báo của bộ phận hành chính, nên có thể hỏi bộ phận này.

**4. Thời gian thử việc** - ⚠️ Không chắc chắn
Lý do: mâu thuẫn, hai file ghi hai thời hạn khác nhau.
> "Thời gian thử việc là 2 tháng" - `handbook.md:8`
> "Thời gian thử việc kéo dài 60 ngày làm việc" - `onboarding.md:5`

---
Nguồn đã đọc: `handbook.md`, `onboarding.md`
Chưa kiểm: không có
```

Ý 4 không chọn 2 tháng hay 60 ngày làm việc. Ý 3 có dòng "Ngoài tài liệu" vì có một gợi ý thật sự hữu ích, và dòng đó nằm dưới nhãn ❌, tách khỏi câu "Không thấy trong các nguồn đã đọc."
