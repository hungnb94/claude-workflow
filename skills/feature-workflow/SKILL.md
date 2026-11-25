---
name: feature-workflow
description: Làm trọn một story hoặc tính năng, từ lúc chốt yêu cầu tới khi code đã được review độc lập và commit local. Dùng khi người dùng gõ /feature-workflow, yêu cầu rõ kiểu "chạy quy trình feature", "chạy quy trình story". Không dùng cho yêu cầu tính năng thông thường, sửa vài dòng, hay điều tra bug đã xảy ra.
---

# Feature Workflow (4 bước)

Làm một story theo 4 bước cố định: chốt yêu cầu, tìm giải pháp, code, review rồi sửa. Mỗi bước ghi một
file, và bước sau chỉ chạy khi đã đọc được file của bước trước.

Câu mở đầu: "Tôi đang dùng skill feature-workflow, gồm 4 bước."

## Khởi tạo

- `STORY` = `$ARGUMENTS`. Rỗng thì hỏi người dùng muốn làm gì, không đoán.
- Story là một bug đã xảy ra, hoặc chỉ cần sửa 1-2 dòng: nói ra và hỏi có muốn làm trực tiếp, không qua
  quy trình không.
- Có Jira key (kể cả nằm trong URL): dùng skill `jira-lookup` lấy title và description làm
  `STORY`.
- `SLUG`: Jira key nếu có; không có thì kebab-case tối đa 4 từ.
- `DIR` = `<repo root>/.workflows/<SLUG>/`, luôn dùng đường dẫn tuyệt đối. `git check-ignore -q .workflows/`
  báo chưa ignore thì thêm dòng `.workflows/` vào `.git/info/exclude`, không sửa `.gitignore`.
- `DIR` đã có file, hoặc nhánh `feature/<SLUG>` đã tồn tại: hỏi người dùng muốn đặt slug mới, hay chạy
  lại từ đầu (ghi đè file; nhánh cũ do người dùng tự xoá hoặc đổi tên trước). Chạy lại mà
  `03-implementation.md` cũ có `BASE` và `BASE..HEAD` còn commit trên nhánh hiện tại: liệt kê các commit
  đó và hỏi người dùng giữ hay bỏ trước khi ghi đè. Không làm tiếp giữa chừng, không ghi đè im lặng.
- `git status --porcelain` có thay đổi chưa commit (ngoài `.workflows/`): liệt kê và hỏi người dùng
  commit hoặc stash trước. Không commit lẫn thay đổi có sẵn của người dùng.

## Luật chuyển bước

Hội thoại dài sẽ bị tóm tắt và mất chi tiết; file trong `DIR` thì không. Vì vậy:

- Mỗi bước có **Vào** (file phải đọc trước khi làm) và **Ra** (file phải ghi trước khi sang bước sau).
- Dòng đầu của file Ra là `Trạng thái: xong`. Chỉ ghi dòng này khi mọi mục của file đã có nội dung.
- Trước khi làm bước N, đọc file Ra của bước N-1. Thiếu file hoặc thiếu dòng trạng thái thì làm lại bước
  N-1, không đoán nội dung của nó.
- Xong mỗi bước, báo người dùng một dòng: bước nào xong, file nào.

## B1. Chốt yêu cầu

**Vào:** `STORY`.

Trước câu hỏi đầu tiên, tra chuẩn nền tảng theo `standards-lookup.md` (đường dẫn:
`<Base directory của skill này>/../solution-brainstorm/standards-lookup.md`) và đọc chuẩn tìm được.

Phỏng vấn người dùng theo cây quyết định, như skill grilling: mỗi vòng hỏi mọi câu đã đủ điều kiện để
hỏi, chờ trả lời rồi mới tính vòng sau. Người trả lời có thể gần như không biết gì về code, nên:

- Tự tra mọi sự thật có trong code (dùng subagent `Explore` khi phải đọc rộng). Chỉ hỏi những gì người
  dùng phải quyết định.
- Tối đa 5 câu mỗi vòng. Trả lời "yes" là chấp nhận đề xuất.
- Mỗi câu đủ để trả lời mà không phải đi tìm thêm thông tin:

```markdown
❓ **Q1** - **<tiêu đề>**

- Bối cảnh: phần nào của hệ thống, hiện đang chạy ra sao (dẫn file:line hoặc màn hình), giải thích
  thuật ngữ bằng lời thường.
- Các lựa chọn: (a) ..., (b) ...
- Impact so với hiện tại: mỗi lựa chọn đổi gì với người dùng và với code đang có, có thể gây bug gì.

➡️ Đề xuất: <lựa chọn>, vì <lý do>.
```

Khi không còn quyết định nào mở, trình bản tóm tắt yêu cầu và chờ người dùng xác nhận. Bản tóm tắt có
dòng nền tảng và chuẩn đã nhận diện; người dùng sửa thì dùng chuẩn họ chọn. Chưa xác nhận thì không sang
B2.

**Ra:** `01-requirements.md` gồm: mục tiêu; acceptance criteria kiểm được; ngoài phạm vi; các quyết định
(câu hỏi và câu trả lời); impact và rủi ro bug; file hoặc khu vực liên quan; lệnh build và test của repo;
ràng buộc bất biến người dùng nêu, nếu có; mục `Chuẩn áp dụng` ghi những gì `standards-lookup.md` bảo
ghi (nền tảng, đường dẫn tuyệt đối tới chuẩn hoặc `không có`, thứ tự ưu tiên).

## B2. Tìm giải pháp

**Vào:** `01-requirements.md`.

Gọi Skill `solution-brainstorm` (trong plugin: `workflow:solution-brainstorm`). Dòng đầu của args là
`CALLER: feature-workflow`; tiếp theo là tóm tắt yêu cầu và đường dẫn tuyệt đối tới `01-requirements.md`.
Không dừng hỏi người dùng sau bước này.

**Ra:** `02-solution.md` gồm: bảng điểm, các phương án chi tiết, và khuyến nghị, chép từ output của
brainstorm.

## B3. Chọn giải pháp và code

**Vào:** `02-solution.md`, và `01-requirements.md` để lấy acceptance criteria, ràng buộc, `Chuẩn áp dụng`
và lệnh test.

1. Chọn phương án có Total cao nhất mà cả tiêu chí #4 (Extensibility) và #7 (Maintainability) đều ≥ 4.
   Không phương án nào đạt thì dừng và hỏi người dùng.
2. Viết 3-5 câu đánh giá vì sao phương án này giữ dự án dễ maintain và dễ mở rộng về lâu dài, và chỗ nào
   có thể thành nợ.
3. Phương án đã chọn chưa có phần chi tiết (layers/files, skeleton) trong `02-solution.md`: tự viết phần
   đó trước khi code.
4. Đang ở nhánh mặc định hoặc detached HEAD thì `git switch -c feature/<SLUG>`. Trước commit đầu tiên,
   ghi ngay vào `03-implementation.md` (chưa có dòng trạng thái): phương án, đánh giá, thiết kế ở bước 3
   nếu có, nhánh, và `BASE` = `git rev-parse HEAD`. Làm lại B3 mà `03-implementation.md` đã có `BASE`
   thì giữ `BASE` cũ, không ghi đè, để review vẫn thấy các commit đã có.
5. Code từng bước nhỏ, mỗi bước một thay đổi. Hành vi mới có test nếu repo có test. Chạy build và test;
   xanh mới commit. Message theo skill `atomic-commit`; chỉ `git add -- <file>`, không `--no-verify`.
6. Đọc lại các file trong `Chuẩn áp dụng` trước khi code, và code theo chúng.
7. Comment theo `comment-policy.md` (đường dẫn: `<Base directory của skill này>/../solution-brainstorm/comment-policy.md`).
8. Test đỏ mà sửa 2 lần vẫn đỏ: dừng, báo người dùng lỗi và những gì đã thử.

**Ra:** `03-implementation.md` gồm: phương án đã chọn và điểm; đánh giá maintain và mở rộng; thiết kế nếu
phải tự viết; nhánh; `BASE`; danh sách commit (`git log --oneline BASE..HEAD`); lệnh test và kết quả.

## B4. Review và sửa

**Vào:** `03-implementation.md`.

1. Spawn agent `fw-4-review` (trong plugin: `workflow:fw-4-review`). Chỉ truyền `REQUIREMENTS` (đường
   dẫn tuyệt đối tới `01-requirements.md`), `BASE`, `COMMENT_POLICY` (đường dẫn tuyệt đối), và
   `STANDARDS` (các đường dẫn trong `Chuẩn áp dụng`, hoặc `không có`). Không
   truyền `02-solution.md` hay `03-implementation.md`, không dùng `subagent_type: "fork"`: reviewer phải
   đánh giá code mà không biết ý định của người viết.
2. Ghi kết quả vào `04-review-<n>.md` (n là số vòng).
3. Sửa hết Blocker và Major. Sửa Minor khi sửa nhỏ và không mở rộng phạm vi. Mỗi lần sửa là một commit
   mới, test xanh. Phát hiện nào không sửa thì ghi lý do.
4. Chạy vòng 2 chỉ khi vòng 1 có Blocker hoặc Major. Không có vòng 3: còn Blocker hoặc Major sau vòng 2
   thì báo người dùng.

**Ra:** `04-review-<n>.md` gồm: các phát hiện của reviewer, và với mỗi phát hiện: đã sửa (commit nào) hay
không sửa (lý do).

## Không làm

Không push, không tạo PR, không merge, không viết lại commit đã có. Không giao việc viết code cho
subagent.

## Báo cáo cuối

Báo người dùng: nhánh, `BASE`, danh sách commit, kết quả test, Blocker hoặc Major còn lại, Minor đã bỏ
qua, đường dẫn `DIR`, và lệnh `git push -u origin <nhánh>` để họ tự push.
