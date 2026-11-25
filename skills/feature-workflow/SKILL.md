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
- `SLUG`: Jira key nếu có; `STORY` trùng tên một thư mục trong `.workflows/` thì dùng tên đó; còn lại
  kebab-case tối đa 4 từ.
- `DIR` = `<repo root>/.workflows/<SLUG>/`, luôn dùng đường dẫn tuyệt đối. `git check-ignore -q .workflows/`
  báo chưa ignore thì thêm dòng `.workflows/` vào `.git/info/exclude`, không sửa `.gitignore`.
- `DIR` đã có file, hoặc nhánh `feature/<SLUG>` đã tồn tại: hỏi người dùng muốn làm tiếp (theo mục
  `Làm tiếp`), đặt slug mới, hay chạy lại từ đầu (ghi đè file; nhánh cũ do người dùng tự xoá hoặc đổi tên
  trước). Chạy lại mà `03-implementation.md` cũ có `BASE` và `BASE..HEAD` còn commit trên nhánh hiện tại:
  liệt kê các commit đó và hỏi người dùng giữ hay bỏ trước khi ghi đè. Không ghi đè im lặng.
- `git status --porcelain` có thay đổi chưa commit (ngoài `.workflows/`): liệt kê và hỏi người dùng
  commit hoặc stash trước. Không commit lẫn thay đổi có sẵn của người dùng.

## Luật chuyển bước

Hội thoại dài sẽ bị tóm tắt và mất chi tiết; file trong `DIR` thì không. Vì vậy:

- Mỗi bước có **Vào** (file phải đọc trước khi làm) và **Ra** (file phải ghi trước khi sang bước sau).
- Dòng đầu của file Ra là `Trạng thái: xong`. Chỉ ghi dòng này khi mọi mục của file đã có nội dung.
- Trước khi làm bước N, đọc file Ra của bước N-1. Thiếu file hoặc thiếu dòng trạng thái thì làm lại bước
  N-1, không đoán nội dung của nó.
- Xong mỗi bước, báo người dùng một dòng: bước nào xong, file nào.
- Trạng thái nằm trong file, không nằm trong chat: tiến độ, việc phát sinh và kết quả từng lần sửa được
  ghi vào file của bước ngay khi có, không đợi cuối bước.

## Làm tiếp

Context đầy hoặc session bị ngắt thì người dùng có thể mở session mới và chạy `/feature-workflow <SLUG>`.
Khi người dùng chọn làm tiếp:

1. Đọc file Ra theo thứ tự `01` tới `04`. Bước làm tiếp là bước đầu tiên có file Ra thiếu hoặc thiếu
   `Trạng thái: xong`. Không dựa vào trí nhớ hay bản tóm tắt hội thoại cho bước đã xong.
2. Đã có `03-implementation.md`: nhánh `feature/<SLUG>` phải còn và chứa `BASE`
   (`git merge-base --is-ancestor <BASE> feature/<SLUG>`); switch sang nhánh đó. Không thoả thì dừng và
   hỏi người dùng.
3. Đọc `Bảng bước` và `Việc phát sinh` của `03-implementation.md`, cùng `git log --oneline BASE..HEAD`.
   Commit có trên nhánh mà bảng chưa ghi: cập nhật dòng đó trước. Làm tiếp từ dòng đầu tiên chưa `xong`.
4. Đang ở B4: đọc `04-review-<n>.md` mới nhất, làm tiếp từ phát hiện đầu tiên chưa ghi đã sửa hay không
   sửa.

## Bằng chứng xong

"Xong", "xanh", "đã sửa" chỉ đúng khi vừa chạy lại; kết quả cũ hay lời tự đánh giá không tính. Trước khi
ghi `Trạng thái: xong` của `03-implementation.md`, và trước báo cáo cuối:

- Chạy lại mọi lệnh trong `Lệnh build và test` của `01-requirements.md`, sau thay đổi cuối cùng. Mục đó
  không có lệnh nào thì ghi `không có lệnh kiểm`, và nói rõ trong báo cáo cuối là chưa có lần chạy nào.
- Ghi từng lệnh, exit code, dòng tóm tắt chép từ output, và `HEAD` lúc chạy.
- Có lệnh đỏ: không ghi trạng thái xong, không báo xong; báo lỗi kèm output.
- Không viết "should pass", "looks correct" khi không kèm output. Lint sạch không thay build hay test. Kết
  quả test của reviewer không thay lần chạy này.

## B1. Chốt yêu cầu

**Vào:** `STORY`.

Trước câu hỏi đầu tiên, nhận diện nền tảng qua `platforms.md` theo `standards-lookup.md` (đường dẫn:
`<Base directory của skill này>/../solution-brainstorm/standards-lookup.md`; không có thì Glob
`**/solution-brainstorm/standards-lookup.md`), rồi đọc chuẩn tìm được.

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
dòng nền tảng và chuẩn đã nhận diện; người dùng sửa thì dùng chuẩn họ chọn, tìm đường dẫn tuyệt đối của
nó theo bước 2 của `standards-lookup.md`. Chưa xác nhận thì không sang B2.

**Ra:** `01-requirements.md` gồm: mục tiêu; acceptance criteria kiểm được; ngoài phạm vi; các quyết định
(câu hỏi và câu trả lời); impact và rủi ro bug; file hoặc khu vực liên quan; mục `Lệnh build và test`
(mọi lệnh build, test và check của repo); ràng buộc bất biến người dùng nêu, nếu có; mục `Chuẩn áp dụng`
ghi những gì `standards-lookup.md` bảo ghi (nền tảng, đường dẫn tuyệt đối tới chuẩn hoặc `không có`, thứ
tự ưu tiên).

## B2. Tìm giải pháp

**Vào:** `01-requirements.md`.

Gọi Skill `solution-brainstorm` (trong plugin: `workflow:solution-brainstorm`). Dòng đầu của args là
`CALLER: feature-workflow`; tiếp theo là tóm tắt yêu cầu và đường dẫn tuyệt đối tới `01-requirements.md`.
Không dừng hỏi người dùng sau bước này.

**Ra:** `02-solution.md` gồm: bảng các phương án giữ lại kèm Total, bảng điểm theo tiêu chí, các phương án
chi tiết, và khuyến nghị, chép từ output của brainstorm.

## B3. Chọn giải pháp và code

**Vào:** `02-solution.md`, và `01-requirements.md` để lấy acceptance criteria, ràng buộc, `Chuẩn áp dụng`
và mục `Lệnh build và test`.

1. Chọn phương án có Total cao nhất mà cả tiêu chí #4 (Extensibility) và #7 (Maintainability) đều ≥ 4.
   Không phương án nào đạt thì dừng và hỏi người dùng.
2. Viết 3-5 câu đánh giá vì sao phương án này giữ dự án dễ maintain và dễ mở rộng về lâu dài, và chỗ nào
   có thể thành nợ.
3. Phương án đã chọn chưa có phần chi tiết (layers/files, skeleton) trong `02-solution.md`: tự viết phần
   đó trước khi code.
4. Đang ở nhánh mặc định hoặc detached HEAD thì `git switch -c feature/<SLUG>`. Trước commit đầu tiên,
   ghi ngay vào `03-implementation.md` (chưa có dòng trạng thái): phương án, đánh giá, thiết kế ở bước 3
   nếu có, nhánh, `BASE` = `git rev-parse HEAD`, `Bảng bước` và `Việc phát sinh` theo khung dưới. Làm lại
   B3 mà `03-implementation.md` đã có `BASE` thì giữ `BASE` cũ, không ghi đè, để review vẫn thấy các
   commit đã có.

   ```markdown
   ## Bảng bước

   | # | Mục tiêu | File dự kiến | Trạng thái |
   |---|---|---|---|
   | 1 | <một thay đổi, một commit> | <file> | chưa |

   ## Việc phát sinh

   - <việc ngoài phạm vi thấy trong lúc code, chưa làm>
   ```

5. Code từng bước nhỏ, mỗi bước một thay đổi. Hành vi mới có test nếu repo có test. Chạy các lệnh trong
   `Lệnh build và test`; xanh mới commit. Message theo skill `atomic-commit`; chỉ `git add -- <file>`, không `--no-verify`.
   Commit xong thì ghi ngay trạng thái của dòng đó trong `Bảng bước`: `xong <commit>` hoặc
   `hỏng <lý do>`. Việc ngoài phạm vi thấy giữa chừng thì ghi vào `Việc phát sinh`, không làm luôn.
6. Đọc lại các file trong `Chuẩn áp dụng` trước khi code, cùng những file tham chiếu mà bảng của chuẩn
   chỉ tới cho thay đổi sắp code, và code theo chúng.
7. Comment theo `comment-policy.md` (đường dẫn: `<Base directory của skill này>/../solution-brainstorm/comment-policy.md`).
8. Test đỏ mà sửa 2 lần vẫn đỏ: dừng, báo người dùng lỗi và những gì đã thử.

**Ra:** `03-implementation.md` gồm: phương án đã chọn và điểm; đánh giá maintain và mở rộng; thiết kế nếu
phải tự viết; nhánh; `BASE`; `Bảng bước` với mọi dòng `xong`; `Việc phát sinh`; danh sách commit
(`git log --oneline BASE..HEAD`); bằng chứng theo mục `Bằng chứng xong`.

## B4. Review và sửa

**Vào:** `03-implementation.md`.

1. Spawn agent `fw-4-review` (trong plugin: `workflow:fw-4-review`). Chỉ truyền `REQUIREMENTS` (đường
   dẫn tuyệt đối tới `01-requirements.md`), `BASE`, `COMMENT_POLICY` (đường dẫn tuyệt đối), và
   `STANDARDS` (các đường dẫn trong `Chuẩn áp dụng`, hoặc `không có`). Không
   truyền `02-solution.md` hay `03-implementation.md`, không dùng `subagent_type: "fork"`: reviewer phải
   đánh giá code mà không biết ý định của người viết.
2. Ghi kết quả vào `04-review-<n>.md` (n là số vòng) ngay khi reviewer trả về, trước khi sửa.
3. Sửa hết Blocker và Major. Sửa Minor khi sửa nhỏ và không mở rộng phạm vi. Mỗi lần sửa là một commit
   mới, test xanh; ghi ngay vào `04-review-<n>.md` phát hiện đó đã sửa ở commit nào. Phát hiện nào không
   sửa thì ghi lý do.
4. Chạy vòng 2 chỉ khi vòng 1 có Blocker hoặc Major. Không có vòng 3: còn Blocker hoặc Major sau vòng 2
   thì báo người dùng.

**Ra:** `04-review-<n>.md` gồm: các phát hiện của reviewer, và với mỗi phát hiện: đã sửa (commit nào) hay
không sửa (lý do).

## Không làm

Không push, không tạo PR, không merge, không viết lại commit đã có. Không giao việc viết code cho
subagent.

## Báo cáo cuối

Chạy lại theo mục `Bằng chứng xong`, kể cả khi B4 không sửa gì (bằng chứng của B3 không thay lần chạy
này), rồi báo người dùng: nhánh, `BASE`, danh sách commit, bằng chứng của lần chạy đó, Blocker hoặc Major còn lại, Minor đã bỏ qua, `Việc phát sinh`, đường dẫn `DIR`, và lệnh
`git push -u origin <nhánh>` để họ tự push.
