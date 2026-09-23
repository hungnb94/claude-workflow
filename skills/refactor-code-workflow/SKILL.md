---
name: refactor-code-workflow
description: Quy trình 7 bước chạy bằng subagent cho refactor an toàn, không đổi hành vi quan sát được - chốt vùng thay đổi và hành vi cần giữ, research kỹ thuật characterization/Golden Master, lập kế hoạch seam và micro-step, đóng băng hành vi bằng characterization test trước khi sửa, refactor theo bước vi mô giữ test xanh, review độc lập với Behavior Preservation Audit phát hiện test bị nới lỏng, rồi tự động sửa. Chỉ dùng khi người dùng gõ /refactor-code-workflow, hoặc yêu cầu rõ ràng kiểu "chạy quy trình refactor an toàn", "refactor không đổi hành vi". Không tự kích hoạt cho yêu cầu refactor thông thường, không dùng khi có tính năng/hành vi mới cần thêm (nhường feature-workflow), và không dùng để điều tra bug đã xảy ra (cần luồng reproduce → root cause riêng).
---

# Refactor Code Workflow (7 bước, chạy bằng subagent)

Tái cấu trúc code như một Legacy Code Engineer kỷ luật: khoanh vùng thay đổi và đóng băng hành vi
quan sát được cần giữ trước khi sửa gì (characterization test / Golden Master), lập kế hoạch seam và
chuỗi bước vi mô, refactor theo micro-step giữ test luôn xanh, và có review độc lập chuyên phát hiện
"test bị nới lỏng để hợp lý hoá hành vi mới" - rủi ro lớn nhất khi để AI agent tự refactor không giám
sát.

**Câu mở đầu bắt buộc:** "Tôi đang dùng skill refactor-code-workflow, gồm 7 bước."

## Vai trò của bạn: orchestrator

Bạn **không** khảo sát/viết test/refactor/review. Bạn: xác định `[TASK]`, tạo `[WORKFLOW_DIR]`; spawn
tuần tự 7 subagent đúng thứ tự; sau mỗi bước chỉ đọc `## TÓM TẮT` để quyết định đi tiếp hay dừng hỏi;
báo cáo ngắn gọn sau mỗi bước.

Mỗi bước chạy subagent riêng, không thừa hưởng định kiến bước trước. Quan trọng nhất ở Bước 6: không
thấy `03-plan.md`/`05-refactor.md`, chỉ thấy oracle cố định (`04-baseline/` snapshot) để phát hiện test
loosening một cách khách quan, **chỉ tìm + phân loại lỗi, không sửa**. Bước 7 ngược lại - đọc đúng cái
Bước 6 ghi để sửa đúng chỗ.

## Cổng chặn trước khi chạy

Kiểm tra 4 điều này **trước** khi tạo thư mục hay spawn gì. Lý do nền tảng: **"Two Hats"** (Kent
Beck) - đội "mũ refactor" thì không đổi hành vi, đội "mũ đổi hành vi" thì không refactor; trộn hai mũ
làm mất oracle (không còn biết cái gì là hành vi cũ cần giữ, cái gì là hành vi mới được phép đổi).

- **Có tính năng/hành vi mới cần thêm**: quy trình này giả định hành vi **không đổi** - dùng skill
  `feature-workflow` thay. Nếu mục tiêu thật là "dọn code trước rồi thêm tính năng" (Kent Beck:
  "make the change easy, then make the easy change"): chạy `refactor-code-workflow` cho phần dọn dẹp
  trước, rồi `feature-workflow` cho phần tính năng sau, đừng gộp một lần.
- **Bug đã xảy ra cần điều tra**: quy trình thiếu bước reproduce/root cause - nói rõ, đề nghị luồng
  bug thường (reproduce → root cause → fix → test).
- **Refactor quá nhỏ** (sửa 1-2 dòng, đổi tên biến đơn lẻ, không cần characterization test): làm trực
  tiếp, nói rõ vì sao 7 bước là thừa.
- **Refactor quá lớn** (chạm quá nhiều module cùng lúc): không từ chối - yêu cầu chia thành increment
  theo Branch by Abstraction (bên trong codebase) hoặc Strangler Fig (ranh giới/module), mỗi lần chạy
  quy trình này chỉ làm **một increment**.

## Kỷ luật an toàn

Bảng truy vết 7 kỷ luật → bước thực thi cụ thể:

| Kỷ luật | Định nghĩa ở | Thực thi ở | Kiểm chứng ở |
|---|---|---|---|
| Characterization test trước khi sửa (Golden Master khi chưa có test) | `rcw-3-plan` (Test Points) | `rcw-4-protect` | Cổng orchestrator sau Bước 4 + `rcw-6-review` |
| Seam tách dependency không sửa tại chỗ | `rcw-1-spec` (ứng viên), `rcw-3-plan` (chốt) | `rcw-4-protect` | `rcw-6-review` |
| Khoanh vùng nhỏ nhất, không refactor lan | `rcw-1-spec` (Vùng thay đổi) | `rcw-5-refactor` | `rcw-6-review` (Major nếu ngoài vùng) |
| Không trộn bugfix/refactor/feature (Two Hats) | Cổng chặn + `rcw-1-spec` | `rcw-4-protect`/`rcw-5-refactor` (pin, không sửa) | `rcw-6-review` (Blocker nếu đổi hành vi) |
| Micro-step, test xanh sau mỗi bước | `rcw-3-plan` (Micro-step Sequence) | `rcw-5-refactor` (revert ngay nếu đỏ) | Cổng orchestrator sau Bước 5 + `rcw-6-review` chạy lại test |
| Branch by Abstraction / Strangler Fig cho thay đổi lớn | Cổng chặn + `rcw-3-plan` (track=large) | `rcw-5-refactor` (một increment/lần) | `rcw-6-review` (Blocker nếu đường cũ không còn chạy) |
| Coverage mở rộng dần, đo bằng diff coverage không giảm | `rcw-4-protect` (đo trước, mở đầu) | `rcw-4-protect` (đo trước), `rcw-5-refactor` (đo sau) | `rcw-6-review` (Major nếu giảm) + `rcw-7-fix` |

## Tham số & khởi tạo

- `[TASK]` = `$ARGUMENTS` - mô tả người dùng gõ, đường dẫn file `.md`, Jira key, hoặc URL Jira. Rỗng
  thì hỏi nhiệm vụ là gì rồi mới chạy.
- `[TASK_SLUG]`: (1) tìm Jira key bằng regex `[A-Z][A-Z0-9]+-[0-9]+` ở bất kỳ đâu trong `[TASK]`, kể
  cả URL - có key thì slug **chính là key**; (2) không có key: kebab-case tối đa 4 từ.
- Có Jira key → dùng skill `acli` lấy title + description ticket làm `[TASK]` thật cho Bước 1.
- `[WORKFLOW_DIR]` = `<repo root>/.workflows/[TASK_SLUG]/` - luôn truyền **đường dẫn tuyệt đối**.
- Spawn subagent chỉ truyền `WORKFLOW_DIR` và `TASK` (chỉ Bước 1) - subagent tự đọc hướng dẫn từ
  definition của mình.

## Cấu trúc output

```text
.workflows/<TASK_SLUG>/
  01-spec.md       <- Bước 1: vùng thay đổi, hành vi quan sát được cần giữ, test hiện có, AC
  02-research.md   <- Bước 2: refactoring moves, kỹ thuật test legacy, công cụ sẵn có trong repo đích
  03-plan.md       <- Bước 3: track micro|large, test points, seams, trình tự micro-step
  04-protect.md    <- Bước 4: characterization test đã thêm + Baseline Manifest
  04-baseline/     <- Bước 4: snapshot nguyên văn mọi file test baseline (oracle cố định)
  05-refactor.md   <- Bước 5: nhật ký micro-step + kết quả test sau mỗi bước
  06-review.md     <- Bước 6: review + Blocker/Major/Minor + Behavior Preservation Audit
  07-fix.md        <- Bước 7: sửa phát hiện + gợi ý tách commit test:/refactor:
```

`04-baseline/` giữ đường dẫn tương đối của file test gốc (vd `04-baseline/tests/test_x.py`) - không
phải file `.md` output của bước nên không cần `## TÓM TẮT`/`## CHI TIẾT`.

`.workflows/` phải nằm trong `.gitignore` repo đích; chưa có thì nhắc thêm **trước Bước 4** (từ Bước 4
bắt đầu có snapshot test và sửa code thật, artifact quy trình không được lẫn vào vùng Bước 6 dò lỗi).

Mỗi file `.md` có `## TÓM TẮT` (input bước sau) và `## CHI TIẾT` (audit). Không xoá file cũ - đây là
audit trail.

## Resume / chạy lại

Đầu mỗi lần gọi: `ls [WORKFLOW_DIR]` (im lặng nếu chưa có).

- Chưa có gì → chạy từ Bước 1.
- Có `01..0N` → `AskUserQuestion`: *tiếp tục từ N+1* / *chạy lại Bước N* / *nhiệm vụ mới (slug
  khác)*. Không bao giờ ghi đè im lặng.
- Chạy lại một bước: ghi đè đúng file bước đó, **không** xoá file bước sau; nói rõ file sau đã cũ.
- Chạy lại Bước 4: ghi đè `04-baseline/` và báo rõ Bước 5-7 đã cũ so với baseline mới, cần chạy lại
  từ Bước 5.

## Routing subagent

| Bước | `subagent_type` | Model | Tools | Vì sao |
|---|---|---|---|---|
| 1 Chốt spec | `rcw-1-spec` | Sonnet | Read, Grep, Glob, Write, Bash | Business Analyst - khoanh vùng thay đổi, pin hành vi cần giữ |
| 2 Research | `rcw-2-research` | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | Research Specialist - refactoring moves, Golden Master, công cụ sẵn có |
| 3 Kế hoạch | `rcw-3-plan` | **Opus** | Read, Grep, Glob, Write, Bash | Solution Architect - chọn seam/track, second-order effects (bắt buộc) |
| 4 Protect | `rcw-4-protect` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Characterization Test Engineer - đóng băng hành vi trước khi sửa |
| 5 Refactor | `rcw-5-refactor` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Refactoring Engineer - micro-step, revert ngay nếu đỏ |
| 6 Review | `rcw-6-review` | Sonnet | **Read, Grep, Glob, Write, Bash ONLY** | Quality Auditor - Behavior Preservation Audit, **KHÔNG có Edit** |
| 7 Sửa lỗi | `rcw-7-fix` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Remediation Engineer - restore oracle khi phát hiện test loosening |

**Không dùng `subagent_type: "fork"`.** Fork thừa hưởng context của bạn, phá vỡ yêu cầu Bước 6 phải
độc lập với ý định tác giả (context isolation). Chạy tuần tự - không spawn song song.

## Mẫu lời gọi Agent

```text
Bạn là subagent thực hiện BƯỚC <N>/7 của quy trình refactor.
Làm theo hướng dẫn trong definition của bạn (agent rcw-<N>-<tên>).
Tham số:
- WORKFLOW_DIR: <đường dẫn tuyệt đối>
- TASK: <chỉ Bước 1: nội dung nhiệm vụ đã lấy được>
```

## Các cổng người duyệt

**Sau Bước 1** - `Câu hỏi cần làm rõ` khác "không có" (gồm cả trường hợp phát hiện đây thực chất là
feature/bug, hoặc test hiện có đang **red**): `AskUserQuestion`, ghi trả lời vào `01-spec.md` **trước**
Bước 2. Test đang red thì không refactor trên nền đỏ - phải xử lý trước.

**Sau Bước 2** - `Câu hỏi cần làm rõ` khác "không có": `AskUserQuestion`, ghi vào `02-research.md`
**trước** Bước 3. Bình thường auto chạy tiếp.

**Sau Bước 3** - `Track: large` → `AskUserQuestion` xác nhận increment đã chọn trước khi chạy Bước 4;
`Track: micro` → chạy tiếp không cần hỏi.

**Sau Bước 4** - `Baseline xanh trên code chưa đổi` ≠ YES, hoặc có `Mục bị chặn`: dừng, không sang
Bước 5. Đây là cổng cứng nhất của workflow - không có oracle xanh thì không được refactor.

**Sau Bước 5** - `Trạng thái = BLOCKED`, hoặc `Baseline test bị sửa` có mục không phải cơ học: dừng,
báo người dùng trước khi review.

**Sau Bước 6 - không hỏi người dùng, tự động chạy tiếp Bước 7.** `06-review.md` báo Blocker=Major=
Minor=0: bỏ qua Bước 7, coi Bước 6 là bước cuối.

**Sau Bước 7 (hoặc Bước 6 nếu không có gì để sửa)** - cổng cuối: trình `## TÓM TẮT`, nhắc **chưa
commit / chưa merge / chưa push gì**.

## Nguyên tắc xuyên suốt

- **Không nhảy bước.** Thiếu file bước trước thì không chạy được bước sau.
- **Thiếu thông tin thì dừng, không đoán.** Ghi câu hỏi vào `## TÓM TẮT` rồi trả người dùng.
- **Chỉ Bước 4, Bước 5 và Bước 7 được sửa file trong source tree.** Bước 1/2/3/6 chỉ đọc code thật và
  ghi `.md`/snapshot trong `.workflows/<SLUG>/` - Bước 6 review/phân loại lỗi nhưng không `Edit` lên
  code hay test thật.
- **Baseline test (`04-baseline/`) là oracle cố định.** Sau khi snapshot ở Bước 4, không file nào
  trong source tree tương ứng được sửa assertion/expected value ngoại trừ cập nhật tham chiếu cơ học
  (rename/move import) - vi phạm là Blocker ở Bước 6, phải restore ở Bước 7.
- **Two Hats.** Refactor và đổi hành vi là hai "mũ" khác nhau, không đội cùng lúc - phát hiện bug/nhu
  cầu tính năng trong lúc refactor thì ghi `Phát hiện ngoài phạm vi`, không tự sửa.
- **OCP + YAGNI**: mở rộng qua bảng tra cứu dữ liệu/registry/strategy, không chắp vá cascading
  if-elif `==`; không tạo abstraction thừa cho nhu cầu chưa xuất hiện.
- **Công cụ ngoài (mutation testing, coverage tool nâng cao) chỉ tận dụng nếu repo đích đã có sẵn**
  (Zero-dependency) - không phải yêu cầu cứng của workflow này.
