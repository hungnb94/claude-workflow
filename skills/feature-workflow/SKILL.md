---
name: feature-workflow
description: Quy trình 6 bước chạy bằng subagent cho một story/tính năng - chốt spec, research best practice ngành theo loại project, lập kế hoạch thay đổi, triển khai kèm test, review độc lập, rồi tự động sửa toàn bộ lỗi Blocker/Major/Minor tìm được và chuẩn bị ship. Chỉ dùng khi người dùng gõ /feature-workflow, hoặc yêu cầu rõ ràng kiểu "chạy quy trình 6 bước", "chạy quy trình story". Không tự kích hoạt cho các yêu cầu tính năng thông thường, và không dùng để điều tra bug đã xảy ra (bug cần bước reproduce + root cause riêng).
---

# Feature / Story Workflow (6 bước, chạy bằng subagent)

Quy trình để làm một story như senior engineer: chốt phạm vi trước khi viết code, research best
practice ngành cho đúng loại tác vụ trước khi chọn hướng, mọi thay đổi có test, code được review bởi
một agent khác với agent đã viết nó, và toàn bộ phát hiện (Blocker/Major/Minor) từ review đó được
một subagent riêng tự sửa nốt — không cần người dùng phải yêu cầu lại lần hai.

**Câu mở đầu bắt buộc:** "Tôi đang dùng skill feature-workflow, gồm 6 bước."

## Vai trò của bạn: orchestrator

Bạn **không** trực tiếp khảo sát code, không viết code, không review. Bạn:

1. Xác định story, tạo `[WORKFLOW_DIR]`.
2. Spawn tuần tự 6 subagent, mỗi bước một subagent, đúng thứ tự.
3. Sau mỗi bước: đọc **chỉ** phần `## TÓM TẮT` của file output, quyết định đi tiếp / dừng hỏi người dùng. Đừng đọc `## CHI TIẾT` — nó dành cho bước sau và cho người audit.
4. Báo cáo lại cho người dùng ngắn gọn sau mỗi bước.

Lý do tách subagent: mỗi bước nhận đúng lượng ngữ cảnh nó cần và không thừa hưởng định kiến của bước trước. Đặc biệt quan trọng ở Bước 5 — subagent review không được thấy kế hoạch/impl, nó phải suy ra hành vi thật của code, và **chỉ được tìm + phân loại lỗi, không được sửa**. Bước 6 thì ngược lại: nó cần đọc đúng cái Bước 5 đã ghi (toàn bộ Blocker/Major/Minor + đề xuất hướng sửa) để sửa đúng chỗ, không cần "mù" như Bước 5.

## Cổng chặn trước khi chạy

Kiểm tra 3 điều này **trước** khi tạo thư mục hay spawn gì:

- **Bug đã xảy ra** (có lỗi/crash/hành vi sai đang tồn tại): quy trình này thiếu bước reproduce và tìm root cause. Nói rõ và đề nghị làm theo luồng bug thường (reproduce → root cause → fix → test).
- **Story quá lớn** (dự kiến chạm quá nhiều module, hoặc Bước 1 ra hơn ~10 acceptance criteria): đề nghị chẻ thành nhiều story nhỏ, chạy quy trình riêng cho từng story.

## Tham số & khởi tạo

- `[STORY]` = `$ARGUMENTS` — mô tả người dùng gõ, đường dẫn file `.md`, Jira key, hoặc URL Jira.
  Nếu rỗng: hỏi người dùng story là gì rồi mới chạy.
- `[STORY_SLUG]`:
  1. Tìm Jira key bằng regex `[A-Z][A-Z0-9]+-[0-9]+` ở **bất kỳ đâu** trong `[STORY]`, kể cả trong URL.
  `https://biorithm.atlassian.net/browse/FEMDEV-2586` → slug là `FEMDEV-2586`.
  Có key thì slug **chính là key**, không nối thêm mô tả.
  2. Không có key: kebab-case tối đa 4 từ (`them-bo-loc-ngay`).
  Slug ngắn để đường dẫn gõ được bằng tay và khớp tên branch `feature/<KEY>-<slug>`.
- Nhận diện được Jira key → dùng skill `acli` lấy title + description của ticket. Nội dung đó là `[STORY]` thật truyền cho Bước 1; đừng bắt Bước 1 tự mở link.
- `[WORKFLOW_DIR]` = `<repo root>/.workflows/[STORY_SLUG]/` — luôn truyền **đường dẫn tuyệt đối** cho subagent, vì subagent có working dir riêng.
Không truyền "phạm vi code" cho bất kỳ bước nào. Bước 1 tự khảo sát và ghi ra `Điểm tích hợp`;
Bước 2 đọc mục đó để research best practice; Bước 3 đọc spec + research để chọn hướng; Bước 4 đọc
danh sách thay đổi; Bước 5 lấy chính diff làm phạm vi; Bước 6 lấy chính danh sách phát hiện
(Blocker/Major/Minor) trong `05-review.md` làm phạm vi.

**Lưu ý:** Khi spawn subagent,
chỉ cần truyền `WORKFLOW_DIR` và `STORY` (chỉ Bước 1). Subagent sẽ tự đọc hướng dẫn từ chính definition
file của nó — **không cần file prompt riêng biệt**.

## Cấu trúc output

```
.workflows/<STORY_SLUG>/
  01-spec.md      <- Bước 1: phạm vi + acceptance criteria + ràng buộc
  02-research.md  <- Bước 2: best practice ngành theo loại project, đối chiếu convention nội bộ
  03-plan.md      <- Bước 3: hướng đã chọn + danh sách thay đổi
  04-impl.md      <- Bước 4: đã code gì + kết quả test
  05-review.md    <- Bước 5: review + phân loại Blocker/Major/Minor
  06-fix.md       <- Bước 6: sửa toàn bộ Blocker/Major/Minor + ghi chú ship
```

Mỗi file luôn có `## TÓM TẮT` (ngắn, là input của bước sau) và `## CHI TIẾT` (để audit).
Không xoá file cũ — đây là audit trail, số thứ tự cho biết đang ở bước nào.

## Resume / chạy lại

Đầu mỗi lần gọi: `ls [WORKFLOW_DIR]` (im lặng nếu chưa tồn tại).

- Chưa có gì → chạy từ Bước 1.
- Đã có `01..0N` → dùng `AskUserQuestion`: *tiếp tục từ Bước N+1* / *chạy lại Bước N* / *bắt đầu story mới (slug khác)*. Không bao giờ ghi đè im lặng.
- Chạy lại một bước thì ghi đè đúng file của bước đó và **không** xoá file các bước sau; nói rõ với người dùng rằng các file sau đã cũ so với bước vừa chạy lại.

## Routing subagent

Mỗi bước dùng custom agent chuyên biệt với role senior/expert, tools phù hợp, và model đã chọn:

| Bước | `subagent_type` | Model | Tools | Vì sao |
|---|---|---|---|---|
| 1 Chốt spec | `fw-1-spec` | Sonnet | Read, Grep, Glob, Write, Bash | Senior Business Analyst - khảo sát scope, viết AC |
| 2 Research | `fw-2-research` | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | Senior Research Specialist - tìm best practices, gap analysis |
| 3 Kế hoạch | `fw-3-plan` | **Opus** | Read, Grep, Glob, Write, Bash | Senior Solution Architect - cần reasoning phức tạp cho Backward Planning và second-order effects |
| 4 Triển khai | `fw-4-impl` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Senior Execution Engineer - code và test deliverables |
| 5 Review | `fw-5-review` | Sonnet | **Read, Grep, Glob, Write, Bash ONLY** | Senior Quality Auditor - review độc lập, **KHÔNG có Edit** để đảm bảo chỉ tìm lỗi, không sửa code |
| 6 Sửa lỗi | `fw-6-fix` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Senior Remediation Engineer - sửa toàn bộ Blocker/Major/Minor |

**Lợi ích của custom agents:**
- **Model selection**: Opus cho Bước 3 (reasoning phức tạp), Sonnet cho các bước khác (execution hiệu quả)
- **Tool isolation**: Bước 5 bị cấm Edit để đảm bảo review độc lập, không vô tình sửa code
- **Role clarity**: Mỗi agent có senior role rõ ràng, signals expertise level cho subagent
- **Context isolation**: Mỗi agent chạy trong context riêng, đặc biệt Bước 5 không thấy plan/impl notes

**Không dùng `subagent_type: "fork"` cho bất kỳ bước nào.** Fork thừa hưởng context của bạn, phá vỡ đúng cái mà quy trình này mua: Bước 5 phải "mù" ý định của tác giả.

Các bước tuần tự — không spawn song song, vì bước sau ăn output bước trước.

## Mẫu lời gọi Agent

Mỗi bước gửi một prompt ngắn. Hướng dẫn chi tiết đã có sẵn trong definition của từng subagent:

```
Bạn là subagent thực hiện BƯỚC <N>/6 của quy trình làm story.
Làm theo hướng dẫn trong definition của bạn (agent fw-<N>-<tên>).
Tham số:
- WORKFLOW_DIR: <đường dẫn tuyệt đối>
- STORY: <chỉ Bước 1: nội dung story đã lấy được>
```

File prompt theo bước: `01-spec.md`, `02-research.md`, `03-plan.md`, `04-impl.md`, `05-review.md`, `06-fix.md`.

## Các cổng người duyệt

**Sau Bước 1** — nếu `Câu hỏi cần làm rõ` khác "không có": dùng `AskUserQuestion` (một câu hỏi cho mỗi điểm mơ hồ, tối đa 4). Ghi câu trả lời bổ sung vào `01-spec.md` **trước** khi chạy Bước 2.

**Sau Bước 2** — nếu `Câu hỏi cần làm rõ` khác "không có" (mâu thuẫn nghiêm trọng giữa best practice và convention nội bộ, ảnh hưởng quyết định sản phẩm/kiến trúc): dùng `AskUserQuestion`. Ghi câu trả lời vào `02-research.md` **trước** khi chạy Bước 3. Bình thường (không có câu hỏi) thì auto chạy tiếp Bước 3, không cần hỏi người dùng có đồng ý với khuyến nghị research hay không.

**Sau Bước 4** — có mục bị chặn hoặc test đỏ mà subagent không tự giải được: dừng, báo người dùng trước khi review.

**Sau Bước 5 — không hỏi người dùng, tự động chạy tiếp Bước 6.** Bước 5 chỉ review, không sửa gì —
nên chỉ dừng lại khi thật sự không đọc được diff (lỗi công cụ, không phải lỗi trong code). Mục đích
của Bước 6 là loại bỏ việc người dùng phải quay lại yêu cầu "sửa mấy cái lỗi đó đi": Bước 6 sửa
toàn bộ Blocker/Major (bắt buộc) và Minor (theo phán đoán, xem `06-fix.md` prompt) mà không cần hỏi.
Nếu `05-review.md` báo tổng Blocker = Major = Minor = 0: bỏ qua Bước 6 (không có gì để sửa), coi
Bước 5 là bước cuối, đi thẳng tới phần báo cáo cuối như dưới.

**Sau Bước 6 (hoặc sau Bước 5 nếu không có Minor)** — đây là cổng cuối: trình `## TÓM TẮT`, nhắc rõ **chưa commit / chưa merge / chưa push gì**.

## Nguyên tắc xuyên suốt

- **Không nhảy bước.** Thiếu file của bước trước thì không chạy được bước sau.
- **Thiếu thông tin thì dừng, không đoán.** Ghi câu hỏi vào `## TÓM TẮT` rồi trả về cho người dùng. Áp dụng cho mọi bước kể cả Bước 6 — "tự động sửa" không có nghĩa là đoán khi thật sự không chắc, chỉ có nghĩa là không cần hỏi người dùng *trước khi thử*.
- **Chỉ Bước 4 và Bước 6 được sửa code.** Bước 1, 2, 3 và 5 chỉ đọc code và ghi file `.md` — Bước 5 review
  và phân loại lỗi nhưng không được dùng `Edit`/`Write` lên code, chỉ ghi ra `05-review.md`.
- **Best practice ngành ưu tiên hơn convention nội bộ, nhưng không phải cái cớ over-engineering.**
  Bước 2 (research) xếp mỗi khuyến nghị vào nhóm trùng / mâu thuẫn-nên-đổi / mâu thuẫn-nên-giữ theo
  đúng tiêu chí này; Bước 3 (chọn hướng), Bước 4 (viết code), Bước 5 (review, đánh giá SOLID/over-
  engineering là Major) và Bước 6 (sửa) đều phải áp dụng SOLID (Single Responsibility, Open/Closed,
  Liskov Substitution, Interface Segregation, Dependency Inversion) và loại bỏ abstraction/interface/
  config thừa so với nhu cầu thật của story — chi tiết nằm trong từng file prompt tương ứng.
