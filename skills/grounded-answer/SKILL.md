---
name: grounded-answer
description: Trả lời câu hỏi chỉ dựa trên tài liệu (file, thư mục hiện tại hoặc connector như Google Drive, Confluence), gắn nhãn từng ý là có trong tài liệu kèm trích dẫn, không chắc chắn, hay không biết, và tách kiến thức ngoài ra riêng. Use when / Dùng khi người dùng gõ /grounded-answer, hoặc muốn hỏi đáp từ tài liệu, docs, spec, policy, wiki mà không bịa, ví dụ "tài liệu nói gì về X", "theo docs thì Y thế nào", "answer from these docs". Do not use / Không dùng cho câu hỏi kiến thức chung không cần tài liệu, viết hay sửa tài liệu, tóm tắt cả tài liệu, hoặc tìm code để sửa lỗi.
argument-hint: "[file | thư mục | connector] <câu hỏi>"
disable-model-invocation: true
---

# Grounded Answer

Trả lời câu hỏi chỉ từ tài liệu. Mỗi ý của câu hỏi có đúng một nhãn: ✅ Trả lời, ⚠️ Không chắc chắn, hoặc ❌
Không biết. Lý do: không có skill này, Claude hay lấy kiến thức ngoài mà nói như tài liệu có ghi, nói chắc
điều chỉ suy ra, và bỏ qua ý không trả lời được.

Trả lời bằng ngôn ngữ người hỏi dùng. Skill này chỉ đọc, không sửa file nào.

## Khi nào đọc file khác

- [`templates.md`](templates.md) (cùng thư mục, `${CLAUDE_SKILL_DIR}/templates.md`): đọc ở Bước 4, trước khi
  viết câu trả lời. File này giữ định nghĩa ba nhãn, câu cố định cho ❌, khung trả lời và ví dụ mẫu.

## Quy trình

### Bước 1. Lấy câu hỏi và nguồn

Input: `$ARGUMENTS`.

- `$ARGUMENTS` rỗng, hoặc chỉ có tên nguồn mà không có câu hỏi: hỏi người dùng muốn hỏi gì rồi dừng. Không tự
  đặt câu hỏi, không đoán.
- Tách nguồn ra khỏi câu hỏi. Nguồn là một trong ba loại: file hoặc thư mục được nêu, connector được nêu
  (Google Drive, Confluence, Notion…), hoặc không nêu gì.

### Bước 2. Đọc nguồn

- Có nêu file hoặc thư mục: chỉ đọc đúng nguồn đó. Không đọc thêm file khác. Thư mục được nêu thì tìm theo
  cách ở mục không nêu nguồn bên dưới, nhưng chỉ trong thư mục đó.
- File hoặc thư mục được nêu không tồn tại (ví dụ gõ sai tên): báo rõ cho người dùng rồi dừng. Không chuyển
  sang đọc thư mục hiện tại hay nguồn khác.
- Có nêu connector: chỉ dùng tool của connector đó. Connector chưa cài, chưa đăng nhập hoặc gọi lỗi thì báo
  rõ cho người dùng rồi dừng. Không chuyển sang đọc thư mục hiện tại hay nguồn khác.
- Không nêu nguồn: tìm trong thư mục hiện tại, kể cả thư mục con. Dùng Grep và Glob với từ khoá của từng ý,
  chỉ đọc những đoạn trúng, không đọc cả cây thư mục. Nhiều file trúng hoặc thư mục lớn thì giao subagent
  `Explore` có sẵn tìm và trả về đoạn trích nguyên văn kèm `file:dòng`, để context không bị đầy. File Glob
  thấy mà Grep không đọc được (PDF, docx…) thì đọc bằng Read; Read vẫn không đọc được thì ghi vào "Chưa kiểm".
- Ghi lại mọi file hoặc trang đã đọc, và những gì không kiểm được (file không mở được, kết quả bị cắt, thư
  mục bỏ qua).

### Bước 3. Tách ý, trích dẫn trước

- Tách câu hỏi thành các ý nhỏ, mỗi ý hỏi một điều.
- Với mỗi ý, chép nguyên văn các đoạn liên quan kèm vị trí (`file:dòng`, hoặc tên trang và mục trong
  connector) trước khi kết luận. Tìm đủ mọi chỗ nhắc tới ý đó, vì hai nguồn có thể nói khác nhau.

### Bước 4. Gắn nhãn và viết câu trả lời

Đọc `templates.md`, rồi gắn nhãn từng ý theo định nghĩa ở đó và viết theo khung trả lời của nó. Giữ ba điều:

- Mỗi ý đúng một nhãn. Phân vân giữa ✅ và ⚠️ thì chọn ⚠️.
- Nguồn mâu thuẫn: ⚠️, trích cả hai bên, không tự chọn bên nào.
- Kiến thức ngoài tài liệu không nằm trong phần trả lời có nhãn. Nó chỉ được nằm ở dòng riêng "Ngoài tài
  liệu (chưa kiểm)" dưới ý ❌ hoặc ⚠️, và chỉ khi thật sự hữu ích.

## Báo cáo

Cuối câu trả lời, liệt kê:

- Nguồn đã đọc: từng file hoặc trang.
- Chưa kiểm: nguồn hoặc phần không đọc được hay đã bỏ qua, hoặc "không có".
