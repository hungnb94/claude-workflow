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

Câu hỏi: "Hạn hoàn tiền bao lâu, phí ship có được miễn không, có bảo hành quốc tế không, và hỗ trợ mấy giờ?"
Nguồn: `policy.md`, `faq.md`.

```markdown
**1. Hạn hoàn tiền** - ⚠️ Không chắc chắn
Lý do: mâu thuẫn, hai file ghi hai mốc khác nhau.
> "Hạn hoàn tiền là 30 ngày kể từ ngày mua" - `policy.md:4`
> "Hạn hoàn tiền là 45 ngày" - `faq.md:7`

**2. Miễn phí vận chuyển** - ⚠️ Không chắc chắn
Lý do: mơ hồ, tài liệu không nói là trường hợp nào.
> "Phí vận chuyển có thể được miễn trong một số trường hợp" - `policy.md:9`

**3. Bảo hành quốc tế** - ❌ Không biết
Không thấy trong các nguồn đã đọc.

**4. Giờ hỗ trợ** - ✅ Trả lời
Hỗ trợ từ 8h đến 17h, thứ Hai đến thứ Sáu.
> "Bộ phận hỗ trợ làm việc từ 8h đến 17h, thứ Hai đến thứ Sáu" - `faq.md:12`

---
Nguồn đã đọc: `policy.md`, `faq.md`
Chưa kiểm: không có
```

Ý 1 không chọn 30 hay 45 ngày. Ý 3 không thêm dòng "Ngoài tài liệu" vì không có gì thật sự hữu ích để nói.
