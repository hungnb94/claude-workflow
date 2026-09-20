---
name: generic-task-workflow
description: Quy trình 6 bước chạy bằng subagent cho một nhiệm vụ KHÔNG phải viết/sửa code — deliverable chính là nội dung hoặc kế hoạch (viết tài liệu, nghiên cứu thị trường, lập kế hoạch dự án, soạn báo cáo, thiết kế quy trình vận hành...). Chốt spec, research best practice phù hợp loại nhiệm vụ, lập kế hoạch phần việc/deliverable cần tạo, tạo deliverable thật, review độc lập, rồi tự động sửa toàn bộ lỗi Blocker/Major/Minor tìm được và chuẩn bị công bố/gửi. Dùng khi người dùng gõ /generic-task-workflow, hoặc yêu cầu rõ ràng kiểu "chạy quy trình 6 bước cho việc lập kế hoạch/viết báo cáo/nghiên cứu này". KHÔNG dùng khi deliverable chính là code/script — nhường cho skill feature-workflow; KHÔNG dùng để điều tra/khắc phục sự cố đã xảy ra (thiếu bước reproduce + root cause riêng); KHÔNG dùng cho nhiệm vụ chỉ 1 bước nhỏ, không cần research/plan.
---

# Generic Task Workflow (6 bước, chạy bằng subagent)

Quy trình để làm một nhiệm vụ phi-code như một chuyên gia cẩn trọng: chốt phạm vi trước khi tạo bất
kỳ deliverable nào, research best practice phù hợp đúng LOẠI nhiệm vụ trước khi chọn hướng, mọi
deliverable đều được đối chiếu lại với acceptance criteria, deliverable được review bởi một agent khác
với agent đã tạo ra nó, và toàn bộ phát hiện (Blocker/Major/Minor) từ review đó được một subagent riêng
tự sửa nốt — không cần người dùng phải yêu cầu lại lần hai.

**Câu mở đầu bắt buộc:** "Tôi đang dùng skill generic-task-workflow, gồm 6 bước."

## Vai trò của bạn: orchestrator

Bạn **không** trực tiếp khảo sát, không tự tạo deliverable, không tự review. Bạn:

1. Xác định nhiệm vụ, tạo `[WORKFLOW_DIR]`.
2. Spawn tuần tự 6 subagent, mỗi bước một subagent, đúng thứ tự.
3. Sau mỗi bước: đọc **chỉ** phần `## TÓM TẮT` của file output, quyết định đi tiếp / dừng hỏi người dùng. Đừng đọc `## CHI TIẾT` — nó dành cho bước sau và cho người audit.
4. Báo cáo lại cho người dùng ngắn gọn sau mỗi bước.

Lý do tách subagent: mỗi bước nhận đúng lượng ngữ cảnh nó cần và không thừa hưởng định kiến của bước
trước. Đặc biệt quan trọng ở Bước 5 — subagent review không được thấy kế hoạch/quá trình thực hiện, nó
phải suy ra chất lượng thật của deliverable từ chính deliverable, và **chỉ được tìm + phân loại lỗi,
không được sửa**. Bước 6 thì ngược lại: nó cần đọc đúng cái Bước 5 đã ghi (toàn bộ Blocker/Major/Minor

+ đề xuất hướng sửa) để sửa đúng chỗ, không cần "mù" như Bước 5.

## Cổng chặn trước khi chạy

Kiểm tra 4 điều này **trước** khi tạo thư mục hay spawn gì:

+ **Nhiệm vụ chính là viết/sửa code** (deliverable chính là code, script, hay thay đổi trong một
  codebase): quy trình này không phù hợp — dùng skill `feature-workflow` thay. Nói rõ và gợi ý
  chuyển skill.
+ **Việc đã xảy ra cần điều tra/khắc phục** (có sự cố/kết quả sai đang tồn tại, cần tìm nguyên nhân):
  quy trình này thiếu bước reproduce và tìm root cause. Nói rõ và đề nghị làm theo luồng điều tra sự cố
  thường (reproduce → root cause → khắc phục → xác minh).
+ **Nhiệm vụ quá nhỏ, 1 bước** (không có nhiều phần deliverable phụ thuộc nhau, không cần research hay
  lập kế hoạch): làm trực tiếp, không cần 6 bước. Nói rõ vì sao quy trình này thừa cho việc nhỏ này.
+ **Nhiệm vụ quá lớn** (dự kiến ra quá nhiều phần deliverable độc lập, hoặc Bước 1 ra hơn ~10 tiêu chí
  hoàn thành): đề nghị chẻ thành nhiều nhiệm vụ nhỏ, chạy quy trình riêng cho từng nhiệm vụ.

## Tham số & khởi tạo

+ `[TASK]` = `$ARGUMENTS` — mô tả người dùng gõ, đường dẫn file `.md`, Jira key, hoặc URL Jira.
  Nếu rỗng: hỏi người dùng nhiệm vụ là gì rồi mới chạy.
+ `[TASK_SLUG]`:
  1. Tìm Jira key bằng regex `[A-Z][A-Z0-9]+-[0-9]+` ở **bất kỳ đâu** trong `[TASK]`, kể cả trong URL.
  Có key thì slug **chính là key**, không nối thêm mô tả.
  2. Không có key: kebab-case tối đa 4 từ (`nghien-cuu-thi-truong`).
  Slug ngắn để đường dẫn gõ được bằng tay.
+ Nhận diện được Jira key → dùng skill `acli` lấy title + description của ticket. Nội dung đó là
  `[TASK]` thật truyền cho Bước 1; đừng bắt Bước 1 tự mở link.
+ `[WORKFLOW_DIR]` = `<repo hoặc thư mục làm việc hiện tại>/.workflows/[TASK_SLUG]/` — luôn truyền
  **đường dẫn tuyệt đối** cho subagent, vì subagent có working dir riêng.
Không truyền "phạm vi nhiệm vụ" cho bất kỳ bước nào. Bước 1 tự khảo sát và ghi ra `Điểm tích hợp`
(tài liệu/dữ liệu/hệ thống liên quan tới loại nhiệm vụ); Bước 2 đọc mục đó để research best practice
phù hợp loại nhiệm vụ; Bước 3 đọc spec + research để chọn hướng; Bước 4 đọc danh sách phần việc/
deliverable cần tạo; Bước 5 lấy chính deliverable cuối cùng làm phạm vi; Bước 6 lấy chính danh sách
phát hiện (Blocker/Major/Minor) trong `05-review.md` làm phạm vi.

**Lưu ý:** Khi spawn subagent,
chỉ cần truyền `WORKFLOW_DIR` và `TASK` (chỉ Bước 1). Subagent sẽ tự đọc hướng dẫn từ chính definition
file của nó — **không cần file prompt riêng biệt**.

## Cấu trúc output

```text
.workflows/<TASK_SLUG>/
  01-spec.md      <- Bước 1: phạm vi nhiệm vụ + acceptance criteria + ràng buộc
  02-research.md  <- Bước 2: best practice phù hợp loại nhiệm vụ, đối chiếu convention nội bộ
  03-plan.md      <- Bước 3: hướng đã chọn + danh sách phần việc/deliverable cần tạo
  04-impl.md      <- Bước 4: đã tạo deliverable gì + kết quả verify
  05-review.md    <- Bước 5: review + phân loại Blocker/Major/Minor
  06-fix.md       <- Bước 6: sửa toàn bộ Blocker/Major/Minor + ghi chú chuẩn bị công bố/gửi
```

Mỗi file luôn có `## TÓM TẮT` (ngắn, là input của bước sau) và `## CHI TIẾT` (để audit).
Không xoá file cũ — đây là audit trail, số thứ tự cho biết đang ở bước nào.

## Resume / chạy lại

Đầu mỗi lần gọi: `ls [WORKFLOW_DIR]` (im lặng nếu chưa tồn tại).

+ Chưa có gì → chạy từ Bước 1.
+ Đã có `01..0N` → dùng `AskUserQuestion`: *tiếp tục từ Bước N+1* / *chạy lại Bước N* / *bắt đầu nhiệm
  vụ mới (slug khác)*. Không bao giờ ghi đè im lặng.
+ Chạy lại một bước thì ghi đè đúng file của bước đó và **không** xoá file các bước sau; nói rõ với
  người dùng rằng các file sau đã cũ so với bước vừa chạy lại.

## Routing subagent

Mỗi bước dùng custom agent chuyên biệt với role senior/expert, tools phù hợp, và model đã chọn:

| Bước | `subagent_type` | Model | Tools | Vì sao |
|---|---|---|---|---|
| 1 Chốt spec | `gtw-1-spec` | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | Senior Business Analyst - khảo sát scope, viết AC |
| 2 Research | `gtw-2-research` | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | Senior Research Specialist - tìm best practices, gap analysis |
| 3 Kế hoạch | `gtw-3-plan` | **Opus** | Read, Grep, Glob, Write, Bash | Senior Solution Architect - cần reasoning phức tạp cho Backward Planning và second-order effects |
| 4 Thực hiện | `gtw-4-impl` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Senior Execution Engineer - tạo deliverables, verify |
| 5 Review | `gtw-5-review` | Sonnet | **Read, Grep, Glob, Write, Bash ONLY** | Senior Quality Auditor - review độc lập |
| 6 Sửa lỗi | `gtw-6-fix` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Senior Remediation Engineer - sửa toàn bộ Blocker/Major/Minor |

**Lợi ích của custom agents:**

+ **Model selection**: Opus cho Bước 3 (reasoning phức tạp), Sonnet cho các bước khác (execution hiệu quả)
+ **Tool isolation**: Bước 5 bị cấm Edit để đảm bảo review độc lập, không vô tình sửa deliverable
+ **Role clarity**: Mỗi agent có senior role rõ ràng, signals expertise level cho subagent
+ **Context isolation**: Mỗi agent chạy trong context riêng, đặc biệt Bước 5 không thấy plan/impl notes

**Không dùng `subagent_type: "fork"` cho bất kỳ bước nào.** Fork thừa hưởng context của bạn, phá vỡ
đúng cái mà quy trình này mua: Bước 5 phải "mù" ý định của tác giả.

Các bước tuần tự — không spawn song song, vì bước sau ăn output bước trước.

## Mẫu lời gọi Agent

Mỗi bước gửi một prompt ngắn. Hướng dẫn chi tiết đã có sẵn trong definition của từng subagent:

```text
Bạn là subagent thực hiện BƯỚC <N>/6 của quy trình làm nhiệm vụ.
Làm theo hướng dẫn trong definition của bạn (agent gtw-<N>-<tên>).
Tham số:
- WORKFLOW_DIR: <đường dẫn tuyệt đối>
- TASK: <chỉ Bước 1: nội dung nhiệm vụ đã lấy được>
```

## Các cổng người duyệt

**Sau Bước 1** — nếu `Câu hỏi cần làm rõ` khác "không có": dùng `AskUserQuestion` (một câu hỏi cho mỗi
điểm mơ hồ, tối đa 4). Ghi câu trả lời bổ sung vào `01-spec.md` **trước** khi chạy Bước 2.

**Sau Bước 2** — nếu `Câu hỏi cần làm rõ` khác "không có" (mâu thuẫn nghiêm trọng giữa best practice và
convention nội bộ, ảnh hưởng quyết định sản phẩm/kiến trúc): dùng `AskUserQuestion`. Ghi câu trả lời
vào `02-research.md` **trước** khi chạy Bước 3. Bình thường (không có câu hỏi) thì auto chạy tiếp Bước
3, không cần hỏi người dùng có đồng ý với khuyến nghị research hay không.

**Sau Bước 4** — có mục bị chặn hoặc chưa tự giải được: dừng, báo người dùng trước khi review.

**Sau Bước 5 — không hỏi người dùng, tự động chạy tiếp Bước 6.** Bước 5 chỉ review, không sửa gì — nên
chỉ dừng lại khi thật sự không đọc được deliverable (lỗi công cụ, không phải lỗi trong deliverable).
Mục đích của Bước 6 là loại bỏ việc người dùng phải quay lại yêu cầu "sửa mấy cái lỗi đó đi": Bước 6
sửa toàn bộ Blocker/Major (bắt buộc) và Minor (theo phán đoán, xem definition của gtw-6-fix) mà không cần
hỏi. Nếu `05-review.md` báo tổng Blocker = Major = Minor = 0: bỏ qua Bước 6 (không có gì để sửa), coi
Bước 5 là bước cuối, đi thẳng tới phần báo cáo cuối như dưới.

**Sau Bước 6 (hoặc sau Bước 5 nếu không có Minor)** — đây là cổng cuối: trình `## TÓM TẮT`, nhắc rõ
**chưa publish / chưa gửi / chưa công bố deliverable — bạn cần tự làm bước này**.

## Nguyên tắc xuyên suốt

+ **Không nhảy bước.** Thiếu file của bước trước thì không chạy được bước sau.
+ **Thiếu thông tin thì dừng, không đoán.** Ghi câu hỏi vào `## TÓM TẮT` rồi trả về cho người dùng. Áp
  dụng cho mọi bước kể cả Bước 6 — "tự động sửa" không có nghĩa là đoán khi thật sự không chắc, chỉ có
  nghĩa là không cần hỏi người dùng *trước khi thử*.
+ **Chỉ Bước 4 và Bước 6 được sửa deliverable.** Bước 1, 2, 3 và 5 chỉ đọc/khảo sát và ghi file `.md` —
  Bước 5 review và phân loại lỗi nhưng không được dùng `Edit`/`Write` lên deliverable, chỉ ghi ra
  `05-review.md`.
+ **Best practice phù hợp loại nhiệm vụ ưu tiên hơn convention nội bộ, nhưng không phải cái cớ
  over-engineering.** Bước 2 (research) xếp mỗi khuyến nghị vào nhóm trùng / mâu thuẫn-nên-đổi /
  mâu thuẫn-nên-giữ theo đúng tiêu chí này; Bước 3 (chọn hướng), Bước 4 (tạo deliverable), Bước 5
  (review) và Bước 6 (sửa) đều phải dùng tiêu chí tương đương SOLID khi nhiệm vụ thuần nội dung/kế
  hoạch (mỗi phần deliverable có đúng một mục đích, không lặp lại thông tin ở nhiều nơi, không thêm
  phần không ai yêu cầu, đúng cấu trúc lập luận), hoặc SOLID đầy đủ (Single Responsibility, Open/Closed,
  Liskov Substitution, Interface Segregation, Dependency Inversion) khi `01-spec.md` xác nhận nhiệm vụ
  có phần kiến trúc/code thật — chi tiết nằm trong definition của từng subagent.
