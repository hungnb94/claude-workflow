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
  commit hoặc stash trước. Không commit lẫn thay đổi có sẵn của người dùng. Người dùng chọn làm tiếp thì
  theo bước 2 của mục `Làm tiếp` thay cho dòng này.

## Luật chuyển bước

Hội thoại dài sẽ bị tóm tắt và mất chi tiết; file trong `DIR` thì không. Vì vậy:

- Mỗi bước có **Vào** (file phải đọc trước khi làm) và **Ra** (file phải ghi trước khi sang bước sau).
- Dòng đầu của file Ra là `Trạng thái: xong`. Chỉ ghi dòng này khi mọi mục của file đã có nội dung.
- Trước khi làm bước N, đọc file Ra của bước N-1. Thiếu file hoặc thiếu dòng trạng thái thì làm lại bước
  N-1, không đoán nội dung của nó.
- Xong mỗi bước, báo người dùng một dòng: bước nào xong, file nào.
- Giữ context của session chính nhỏ: ở mọi bước, việc tìm kiếm hay đọc nhiều file giao subagent
  `Explore` và chỉ nhận về bản tóm tắt có file:line; output dài của lệnh chỉ giữ dòng tóm tắt và các dòng
  lỗi.
- Trạng thái nằm trong file, không nằm trong chat: tiến độ, việc phát sinh và kết quả từng lần sửa được
  ghi vào file của bước ngay khi có, không đợi cuối bước.

## Làm tiếp

Context đầy hoặc session bị ngắt thì người dùng có thể mở session mới và chạy `/feature-workflow <SLUG>`.
Khi người dùng chọn làm tiếp:

1. Đọc file Ra theo thứ tự `01` tới `04`. Bước làm tiếp là bước đầu tiên có file Ra thiếu hoặc thiếu
   `Trạng thái: xong`. Không dựa vào trí nhớ hay bản tóm tắt hội thoại cho bước đã xong. Làm tiếp từ B1
   mà `$ARGUMENTS` chỉ là slug: hỏi lại người dùng nội dung story.
2. Có thay đổi chưa commit: đó thường là việc dở của một `fw-3-implement` bị ngắt, chưa qua `CHECKS`.
   Đề nghị người dùng stash hoặc bỏ, không commit nó; bước đó làm lại bằng một agent mới. Làm bước này
   trước khi switch nhánh.
3. Đã có `03-implementation.md`: nhánh ghi trong file đó (mặc định `feature/<SLUG>`) phải còn và chứa
   `BASE` (`git merge-base --is-ancestor <BASE> <nhánh>`); switch sang nhánh đó. Không thoả thì dừng và
   hỏi người dùng.
4. Đang ở B3: đọc `Số lô`, `Bảng bước` và `Việc phát sinh` của `03-implementation.md`, cùng
   `git log --oneline BASE..HEAD`. Commit có trên nhánh mà bảng chưa ghi: ghi `xong <commit>` vào dòng
   tương ứng trước. Dòng `hỏng` thì hỏi người dùng làm lại hay dừng. Các dòng `chưa` còn lại giao cho
   `fw-3-implement` mới theo bước 5 của B3, giữ lô đã ghi, mỗi lô một agent. Mọi dòng đã `xong` thì chạy
   bước 7 của B3; các lô sửa diff đã ghi trong `Số lô` được tính vào giới hạn 2 lần sửa của bước đó.
5. Đang ở B4: đọc `04-review-<n>.md` mới nhất và `git log --oneline BASE..HEAD`. Commit sửa chưa ghi vào
   file đó: ghi `xong <commit>` vào phát hiện tương ứng trước, để không sửa một phát hiện hai lần.
   Blocker hoặc Major ghi `hỏng` thì hỏi người dùng làm lại hay dừng; Minor `hỏng` vào "Minor đã bỏ qua"
   của `Báo cáo cuối`, không hỏi. Các phát hiện còn lại chưa ghi gì (bị ngắt giữa bước 2 và bước 3 của
   B4, hoặc lúc agent đang sửa) thì xử lý như bước 3 của B4: Minor không sửa ghi `không sửa: <lý do>`,
   phần còn lại giao cho một `fw-3-implement` mới.
6. Mọi file Ra đều `xong`: vòng review mới nhất là vòng 1 và có Blocker hoặc Major thì chạy vòng 2 của B4;
   còn lại chạy `Bằng chứng xong` rồi `Báo cáo cuối`. `04-review-<n>.md` mới nhất đã có mục
   `## Bằng chứng cuối` thì làm tiếp vòng sửa trong đó; các lần sửa đã ghi được tính vào giới hạn lần
   sửa của `Bằng chứng xong`. Commit trên nhánh mà mục đó chưa ghi thì ghi vào lần sửa tương ứng trước,
   rồi:
   - Lần sửa bị ngắt (còn mục chưa `xong` hay `hỏng`): các mục đó giao cho một `fw-3-implement` mới,
     vẫn là lần sửa đó, rồi chạy lại bằng một `fw-3-evidence` mới.
   - Lần sửa đã xong mà chưa chạy lại: chạy lại bằng một `fw-3-evidence` mới.
   - Lần chạy mới nhất có lệnh đỏ hoặc AC `không đạt` mà chưa có lần sửa: sửa như `Bằng chứng xong`
     nếu chưa hết giới hạn, hết thì dừng và báo người dùng.
   - Lần chạy mới nhất không có lệnh đỏ hay AC `không đạt`: có commit sửa mà chưa có
     `### Review lần sửa` thì chạy review đó như `Bằng chứng xong`; rồi
     sang `Báo cáo cuối`, không chạy lại.
7. Lần chạy `Bằng chứng xong` bị ngắt (thư mục trong `DIR/evidence/` mà chưa có `RUN_DIR` nào đã ghi trỏ
   tới): bỏ qua thư mục dở đó, không xoá, vì chỉ `RUN_DIR` của lần chạy mới được tính; rồi chạy lại
   `Bằng chứng xong` bằng một `fw-3-evidence` mới.

## Bằng chứng xong

"Xong", "xanh", "đã sửa" chỉ đúng khi vừa chạy lại; kết quả cũ hay lời tự đánh giá không tính. Mục này
chỉ chạy ở cuối, sau B4 và trước `Báo cáo cuối`, kể cả khi B4 không sửa gì: một lần, cộng các lần chạy
lại sau mỗi lần sửa của chính mục này. B3 và B4 không chạy nó.

- Sau thay đổi cuối cùng, spawn một agent `fw-3-evidence` mới (trong plugin: `workflow:fw-3-evidence`),
  không dùng `subagent_type: "fork"`. Truyền `REQUIREMENTS` (đường dẫn tuyệt đối tới
  `01-requirements.md`), `BASE`, `CHECKS` (các lệnh trong `Lệnh build và test`, hoặc `không có`) và
  `EVIDENCE_DIR` = `DIR/evidence/`. Session chính không tự chạy lệnh kiểm, chỉ chép bảng agent trả.
- Ghi lần chạy vào mục `## Bằng chứng cuối` của `04-review-<n>.md` mới nhất: từng lệnh, exit code, dòng
  tóm tắt chép từ output, `HEAD` lúc chạy, `RUN_DIR` agent trả, và bảng trạng thái AC agent trả. Agent
  ghi `không có lệnh kiểm` thì nói rõ trong báo cáo cuối là chưa có lần chạy nào.
- Trạng thái AC: `đạt`, `không đạt`, `chờ người ký`, `chưa kiểm: <lý do>`. `đạt` mà file dẫn tới không
  nằm trong `RUN_DIR` của lần chạy này (kiểm bằng `ls`) thì ghi `chưa kiểm: không có file bằng
  chứng`; file ở thư mục khác không tính.
- Trạng thái AC chỉ ghi vào `## Bằng chứng cuối` và báo cáo cuối, không ghi vào `01-requirements.md`;
  file đó không đổi sau B1.
- Có lệnh đỏ hoặc AC `không đạt`: không báo xong. Quay lại code như B3: spawn một `fw-3-implement` mới,
  truyền như bước 5 của B3 với `STEP` là các lệnh đỏ và AC `không đạt` (mỗi mục kèm dòng lỗi và file bằng
  chứng), dòng đầu `LOẠI: bằng chứng`. Trước khi spawn, ghi `HEAD` lúc đó vào `## Bằng chứng cuối` làm mốc
  của lần sửa. Ghi lần sửa và các dòng agent trả (`<#> xong <hash>`,
  `<#> hỏng <lý do>`) vào mục `## Bằng chứng cuối`, rồi chạy lại mục này bằng một `fw-3-evidence` mới
  sau khi kiểm diff của lần sửa: đọc `git diff <mốc>..HEAD` và kiểm như bước 7 của B3 (không test hay
  assertion nào bị xoá, skip hay nới lỏng, không file nào nằm ngoài yêu cầu). Diff có vấn đề: ghi vào
  `## Bằng chứng cuối`, không chạy lại, dừng và báo người dùng, không báo xong.
  Agent sửa trả có mục `<#> hỏng` thì vẫn chạy lại để có kết quả mới; lần sửa đó vẫn tính vào giới hạn.
  Sau 2 lần sửa vẫn đỏ thì dừng và báo người dùng lỗi kèm output.
  `chưa kiểm` và `chờ người ký` không chặn, chỉ đổi lời báo cuối.
- Review lần sửa: commit của vòng sửa có sau B4 nên reviewer chưa thấy. Vòng sửa dừng ở lần chạy không có
  lệnh đỏ hay AC `không đạt`, và có ít nhất một commit sửa: spawn một `fw-4-review` mới, truyền như bước 1
  của B4 nhưng `BASE` là mốc của lần sửa đầu tiên, để reviewer chỉ xem các commit sửa. Ghi kết quả vào
  `### Review lần sửa` trong `## Bằng chứng cuối`. Không sửa tiếp các phát hiện này, vì không có vòng
  review thứ 3: còn Blocker hoặc Major thì không báo xong, dừng và báo người dùng kèm các phát hiện đó;
  Minor vào "Minor đã bỏ qua" của `Báo cáo cuối`. Không có commit sửa nào thì không spawn.
- `fw-3-implement` của vòng sửa trả `lỗi` mà không có dòng `<#>` nào: dừng và báo người dùng như bước 6
  của B3.
- Agent trả `lỗi` vì working tree bẩn: liệt kê thay đổi, đề nghị người dùng stash hoặc bỏ, không commit
  nó; chỉ chạy lại bằng agent mới khi working tree đã sạch. Lỗi khác: chạy lại một lần bằng agent mới;
  vẫn lỗi thì dừng và báo người dùng.
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
- Mỗi câu có 3-4 lựa chọn đặt ở các điểm khác nhau trên một trục mà câu đó thật sự xoay quanh (phạm vi,
  mức hoàn thiện, hành vi khi lỗi): từ gọn nhất, qua cách theo đúng chuẩn và convention đã đọc, tới bền
  nhất. Không đưa hai lựa chọn chỉ khác nhau về chi tiết. Câu thật sự chỉ có 2 lựa chọn thì ghi 2 và nói
  vì sao. Lựa chọn nói về yêu cầu (người dùng thấy gì, làm tới đâu), không về cách code: việc đó của B2.
- Mỗi câu đủ để trả lời mà không phải đi tìm thêm thông tin:

```markdown
❓ **Q1** - **<tiêu đề>**

- Bối cảnh: phần nào của hệ thống, hiện đang chạy ra sao (dẫn file:line hoặc màn hình), giải thích
  thuật ngữ bằng lời thường.
- Các lựa chọn: (a) gọn nhất ..., (b) theo chuẩn đã đọc ..., (c) bền nhất ..., (d) ...
- Impact so với hiện tại: mỗi lựa chọn đổi gì với người dùng và với code đang có, có thể gây bug gì.

➡️ Đề xuất: <lựa chọn>, vì <lý do>.
```

Trước khi trình bản tóm tắt, mỗi AC phải đủ các cột của bảng AC trong **Ra**. AC có từ như "giống",
"đúng", "đẹp", "không bị đè" mà không có cách đo thì viết lại thành điều kiện đo được (con số, mốc so,
kịch bản kiểm).

Khi không còn quyết định nào mở, trình bản tóm tắt yêu cầu và chờ người dùng xác nhận. Bản tóm tắt có
dòng nền tảng và chuẩn đã nhận diện; người dùng sửa thì dùng chuẩn họ chọn, tìm đường dẫn tuyệt đối của
nó theo bước 2 của `standards-lookup.md`. Chưa xác nhận thì không sang B2.

**Ra:** `01-requirements.md` gồm: mục tiêu; bảng AC theo khung dưới; ngoài phạm vi; các quyết định
(câu hỏi và câu trả lời); impact và rủi ro bug; file hoặc khu vực liên quan; mục `Lệnh build và test`
(mọi lệnh build, test và check của repo); ràng buộc bất biến người dùng nêu, nếu có; mục `Chuẩn áp dụng`
ghi những gì `standards-lookup.md` bảo ghi (nền tảng, đường dẫn tuyệt đối tới chuẩn hoặc `không có`, thứ
tự ưu tiên).

```markdown
| # | AC | Phép kiểm | Môi trường | Bằng chứng | Người chấm |
|---|---|---|---|---|---|
| 1 | <điều kiện đo được> | <lệnh / script so với mốc / người kiểm theo kịch bản> | <nơi chạy> | <file sẽ có> | <máy / verify / người ký> |
```

`Phép kiểm` là một trong `lệnh`, `script so với mốc`, `người kiểm theo kịch bản`. `Người chấm` là một
trong `máy`, `verify`, `người ký`. Bảng AC còn ô trống thì chưa ghi `Trạng thái: xong` và chưa sang B2.

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
   nếu có, nhánh, `BASE` = `git rev-parse HEAD`, dòng `Số lô`, `Bảng bước` và `Việc phát sinh` theo khung
   dưới. Làm lại B3 mà `03-implementation.md` đã có `BASE` thì giữ `BASE` cũ, không ghi đè, để review vẫn
   thấy các commit đã có.

   ```markdown
   Số lô: <n> - <lý do>

   ## Bảng bước

   | # | Mục tiêu | File dự kiến | Lô | Trạng thái |
   |---|---|---|---|---|
   | 1 | <một thay đổi, một commit> | <file> | 1 | chưa |

   ## Việc phát sinh

   - <việc ngoài phạm vi thấy trong lúc code, chưa làm>
   ```

5. Chia các dòng của `Bảng bước` thành lô và ghi vào cột `Lô` và dòng `Số lô` trước khi spawn. Mặc định
   1 lô cho mọi dòng: việc nhỏ thì một agent vừa nhanh vừa chính xác. Chia 2-3 lô khi việc nhiều: các
   phần không chung file, hoặc một agent không đọc hết context cho mọi dòng. Tối đa 3 lô.

   Lần lượt với từng lô còn dòng `chưa`, spawn một agent `fw-3-implement` mới (trong plugin:
   `workflow:fw-3-implement`). Mỗi lô một agent. Lô sau chỉ bắt đầu khi lô trước trả về; không chạy hai
   agent cùng lúc, không dùng `subagent_type: "fork"`: agent code trong context mới, chỉ biết những gì
   được truyền. Truyền:
   - `STEP`: các dòng `chưa` của lô, mỗi dòng giữ số `#`, mục tiêu và file dự kiến; dòng đầu
     `LOẠI: bảng bước`.
   - `REQUIREMENTS`: đường dẫn tuyệt đối tới `01-requirements.md`.
   - `DESIGN`: đường dẫn tuyệt đối tới `02-solution.md` kèm heading của phương án đã chọn, hoặc tới
     `03-implementation.md` kèm heading thiết kế nếu đã tự viết ở bước 3.
   - `STANDARDS`: các đường dẫn trong `Chuẩn áp dụng`, hoặc `không có`.
   - `COMMENT_POLICY`: `<Base directory của skill này>/../solution-brainstorm/comment-policy.md`.
   - `COMMIT_STYLE`: `<Base directory của skill này>/../atomic-commit/SKILL.md`.
   - `CHECKS`: các lệnh trong `Lệnh build và test`, hoặc `không có`.

   Agent làm lần lượt từng dòng: code, có test cho hành vi mới nếu repo có test, chạy `CHECKS`, xanh mới
   tự commit dòng đó (chỉ `git add -- <file>`, không `--no-verify`), rồi sang dòng sau.
6. Agent trả về thì ghi ngay từng dòng trong `Bảng bước` theo đúng dòng agent trả: `<#> xong <hash>` ghi
   `xong <commit>`, `<#> hỏng <lý do>` ghi `hỏng <lý do>`, `<#> chưa` giữ `chưa`. Chép các việc trong
   `Việc phát sinh` của nó vào mục cùng tên của `03-implementation.md`; không làm luôn việc ngoài phạm vi.
   Có dòng `hỏng` hoặc agent trả `lỗi`: dừng, không chạy lô sau, báo người dùng lỗi và những gì đã thử.
7. Mọi dòng đã `xong`: đọc `git log --oneline BASE..HEAD` và `git diff BASE..HEAD`, kiểm không test hay
   assertion nào bị xoá, skip hay nới lỏng và không file nào nằm ngoài yêu cầu. B3 không chạy
   `Bằng chứng xong`: mục đó chạy một lần trước `Báo cáo cuối`. Diff có vấn đề: thêm dòng vào
   `Bảng bước`, ghi vào một lô mới (số lô kế tiếp) và cập nhật `Số lô`; lô sửa này không tính vào giới
   hạn 3 lô. Ghi lô đó trong `Số lô` là lô sửa diff kèm lần sửa (ví dụ `lô 2: sửa diff lần 1`).
   Sửa bằng một `fw-3-implement` mới, truyền như bước 5 với `STEP` là các dòng mới, rồi làm lại bước
   này; sau 2 lần vẫn chưa ổn (đếm các lô sửa diff trong `Số lô`) thì dừng và báo người dùng.
   Commit trộn nhiều thay đổi thì không sửa được vì không viết lại commit: ghi vào `Việc phát sinh` và
   nói trong báo cáo cuối. Không tự
   sửa code trong session chính. Ghi `Trạng thái: xong` khi mọi dòng `xong`, diff đã kiểm và `CHECKS` của
   agent code xanh.

**Ra:** `03-implementation.md` gồm: phương án đã chọn và điểm; đánh giá maintain và mở rộng; thiết kế nếu
phải tự viết; nhánh; `BASE`; dòng `Số lô`; `Bảng bước` với mọi dòng `xong`; `Việc phát sinh`; danh sách
commit (`git log --oneline BASE..HEAD`).

## B4. Review và sửa

**Vào:** `03-implementation.md`.

1. Spawn agent `fw-4-review` (trong plugin: `workflow:fw-4-review`). Chỉ truyền `REQUIREMENTS` (đường
   dẫn tuyệt đối tới `01-requirements.md`), `BASE`, `COMMENT_POLICY` (đường dẫn tuyệt đối), và
   `STANDARDS` (các đường dẫn trong `Chuẩn áp dụng`, hoặc `không có`). Không
   truyền `02-solution.md` hay `03-implementation.md`, không dùng `subagent_type: "fork"`: reviewer phải
   đánh giá code mà không biết ý định của người viết.
2. Ghi kết quả vào `04-review-<n>.md` (n là số vòng) ngay khi reviewer trả về, trước khi sửa.
3. Mỗi vòng spawn đúng một `fw-3-implement` mới cho mọi Blocker, Major và Minor nhỏ (sửa nhỏ, không mở
   rộng phạm vi) của vòng đó, chỉ khi danh sách đó không rỗng (rỗng thì không spawn),
   truyền như bước 5 của B3 với `STEP` là danh sách các phát hiện đó (mỗi mục kèm số `#` reviewer đặt,
   file:line, vấn đề, gợi ý sửa), dòng đầu `LOẠI: phát hiện`; không đánh số lại. Minor khác ghi
   `không sửa: <lý do>` vào mục `## Minor` của `04-review-<n>.md`.
   Agent sửa mỗi phát hiện bằng một commit mới, test xanh. Agent trả về thì
   ghi ngay vào `04-review-<n>.md` từng phát hiện theo đúng dòng agent trả:
   `<#> xong <hash>` ghi `xong <commit>`, `<#> hỏng <lý do>` ghi `hỏng <lý do>`. Blocker hoặc Major
   `hỏng`: dừng và hỏi người dùng làm lại hay dừng. Minor `hỏng` chỉ ghi, không dừng. Agent trả `lỗi` mà
   không có dòng nào cho các phát hiện: dừng và báo người dùng như bước 6 của B3. Sửa xong thì kiểm diff
   của các commit sửa (không test hay assertion nào bị xoá, skip hay nới lỏng); diff có vấn đề thì ghi
   vào `04-review-<n>.md` và nêu trong báo cáo cuối. Vòng này không chạy `Bằng chứng xong`, và
   không thêm dòng vào `Bảng bước` của `03-implementation.md` đã xong.
4. Chạy vòng 2 chỉ khi vòng 1 có Blocker hoặc Major. Không có vòng 3: còn Blocker hoặc Major sau vòng 2
   thì báo người dùng.

**Ra:** `04-review-<n>.md` gồm: các phát hiện của reviewer, và với mỗi phát hiện: đã sửa (commit nào),
`hỏng` (lý do) hay không sửa (lý do); Minor ghi trong mục `## Minor` theo khung, cột `#` giữ đúng số
`#` reviewer đặt (cũng là số trong `STEP`):

   ```markdown
   ## Minor

   | # | file:line | Vấn đề | Trạng thái |
   |---|---|---|---|
   | <# của reviewer> | <file:line> | <vấn đề> | xong <commit> |
   ```

Trạng thái Minor: `xong <commit>`, `hỏng <lý do>`, `không sửa: <lý do>`.

## Không làm

Không push, không tạo PR, không merge, không viết lại commit đã có. Session chính không tự sửa code: mọi
thay đổi code do `fw-3-implement` làm, mỗi lần một agent.

## Báo cáo cuối

Chạy theo mục `Bằng chứng xong`, kể cả khi B4 không sửa gì, rồi báo người dùng: nhánh, `BASE`, danh
sách commit, bằng chứng của lần chạy đó, bảng trạng thái AC, các commit sửa của `Bằng chứng xong` (từ
mốc lần sửa đầu tới `HEAD`) và kết quả `### Review lần sửa`, Blocker hoặc Major còn lại, Minor đã bỏ qua
(các dòng `hỏng` và `không sửa` trong mục `## Minor` của các `04-review-<n>.md`, và Minor của
`### Review lần sửa`), `Việc phát sinh`,
đường dẫn `DIR`, và lệnh `git push -u origin <nhánh>` để họ tự push.
Còn AC `chưa kiểm` hoặc `chờ người ký` thì báo "chờ kiểm N AC" kèm danh sách AC đó và
lý do, không báo xong.
