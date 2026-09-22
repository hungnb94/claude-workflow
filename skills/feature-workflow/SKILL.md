---
name: feature-workflow
description: Quy trình 7 bước chạy bằng subagent cho một story/tính năng - chốt spec, research best practice ngành theo loại project, viết bản mẫu role-model theo best practice, lập kế hoạch thay đổi, triển khai kèm test, review độc lập, rồi tự động sửa toàn bộ lỗi Blocker/Major/Minor tìm được và chuẩn bị ship. Chỉ dùng khi người dùng gõ /feature-workflow, hoặc yêu cầu rõ ràng kiểu "chạy quy trình 7 bước", "chạy quy trình 6 bước", "chạy quy trình story". Không tự kích hoạt cho các yêu cầu tính năng thông thường, và không dùng để điều tra bug đã xảy ra (bug cần bước reproduce + root cause riêng).
---

# Feature / Story Workflow (7 bước, chạy bằng subagent)

Làm story như senior engineer: chốt phạm vi trước khi code, research best practice trước khi chọn
hướng, viết bản mẫu best practice để đối chiếu, mọi thay đổi có test, code được agent khác review, và
mọi phát hiện (Blocker/Major/Minor) được subagent riêng tự sửa nốt - không cần hỏi lại lần hai.

**Câu mở đầu bắt buộc:** "Tôi đang dùng skill feature-workflow, gồm 7 bước."

## Vai trò của bạn: orchestrator

Bạn **không** khảo sát/viết/review code. Bạn: xác định story, tạo `[WORKFLOW_DIR]`; spawn tuần tự 7
subagent đúng thứ tự; sau mỗi bước chỉ đọc `## TÓM TẮT` (không đọc `## CHI TIẾT` - dành cho bước
sau/audit) để quyết định đi tiếp hay dừng hỏi; báo cáo ngắn gọn sau mỗi bước.

Mỗi bước chạy subagent riêng, không thừa hưởng định kiến bước trước. Quan trọng nhất ở Bước 6: không
thấy kế hoạch/impl/role-model, phải tự suy ra hành vi thật của code, **chỉ tìm + phân loại lỗi, không
sửa**. Bước 7 ngược lại - đọc đúng cái Bước 6 ghi để sửa đúng chỗ, không cần "mù" như Bước 6.

## Cổng chặn trước khi chạy

Kiểm tra 3 điều này **trước** khi tạo thư mục hay spawn gì:

- **Bug đã xảy ra**: quy trình thiếu bước reproduce/root cause - nói rõ, đề nghị luồng bug thường
  (reproduce → root cause → fix → test).
- **Story quá nhỏ, 1 bước** (sửa 1-2 dòng, đổi text/config): làm trực tiếp, nói rõ vì sao thừa.
- **Story quá lớn** (chạm quá nhiều module, hoặc Bước 1 ra >~10 AC): đề nghị chẻ nhiều story nhỏ,
  chạy quy trình riêng từng story.

## Tham số & khởi tạo

- `[STORY]` = `$ARGUMENTS` - mô tả người dùng gõ, đường dẫn file `.md`, Jira key, hoặc URL Jira. Rỗng
  thì hỏi story là gì rồi mới chạy.
- `[STORY_SLUG]`: (1) tìm Jira key bằng regex `[A-Z][A-Z0-9]+-[0-9]+` ở **bất kỳ đâu** trong
  `[STORY]`, kể cả URL (`.../browse/FEMDEV-2586` → slug `FEMDEV-2586`) - có key thì slug **chính là
  key**; (2) không có key: kebab-case tối đa 4 từ (`them-bo-loc-ngay`), khớp tên branch
  `feature/<KEY>-<slug>`.
- Có Jira key → dùng skill `acli` lấy title + description ticket làm `[STORY]` thật cho Bước 1; đừng
  bắt Bước 1 tự mở link.
- `[WORKFLOW_DIR]` = `<repo root>/.workflows/[STORY_SLUG]/` - luôn truyền **đường dẫn tuyệt đối**.
- Không truyền "phạm vi code" cho bước nào - mỗi bước tự lấy phạm vi từ output bước trước (Bước 1
  khảo sát ghi `Điểm tích hợp`; Bước 6 lấy diff; Bước 7 lấy phát hiện trong `06-review.md`).
- Spawn subagent chỉ truyền `WORKFLOW_DIR` và `STORY` (chỉ Bước 1) - subagent tự đọc hướng dẫn từ
  definition của mình.

## Cấu trúc output

```text
.workflows/<STORY_SLUG>/
  01-spec.md         <- Bước 1: phạm vi + acceptance criteria + ràng buộc
  02-research.md     <- Bước 2: best practice ngành theo loại project, đối chiếu convention nội bộ
  03-role-model.md   <- Bước 3: code mẫu best practice (THROWAWAY, không phải deliverable)
  04-plan.md         <- Bước 4: hướng đã chọn + danh sách thay đổi
  05-impl.md         <- Bước 5: đã code gì + kết quả test
  06-review.md       <- Bước 6: review + phân loại Blocker/Major/Minor
  07-fix.md          <- Bước 7: sửa toàn bộ Blocker/Major/Minor + ghi chú ship
```

`.workflows/` phải nằm trong `.gitignore` repo đích; chưa có thì nhắc thêm **trước Bước 6** để
artifact quy trình không lẫn vào vùng Bước 6 dò lỗi.

Mỗi file có `## TÓM TẮT` (input bước sau) và `## CHI TIẾT` (audit). Không xoá file cũ - đây là audit
trail.

## Resume / chạy lại

Đầu mỗi lần gọi: `ls [WORKFLOW_DIR]` (im lặng nếu chưa có).

- Chưa có gì → chạy từ Bước 1.
- Có `01..0N` → `AskUserQuestion`: *tiếp tục từ N+1* / *chạy lại Bước N* / *story mới (slug khác)*.
  Không bao giờ ghi đè im lặng.
- Chạy lại một bước: ghi đè đúng file bước đó, **không** xoá file bước sau; nói rõ file sau đã cũ so
  với bước vừa chạy lại.
- Có `03-plan.md` không có `03-role-model.md` → layout cũ (6 bước): hỏi *chạy tiếp layout cũ bằng
  tay* / *chạy lại từ Bước 3 theo layout 7 bước (file 03..06 cũ giữ audit trail, không xoá)*.

## Routing subagent

Mỗi bước dùng custom agent chuyên biệt: role senior/expert, tools phù hợp, model theo độ khó (Opus
Bước 3/4, Sonnet còn lại), context riêng (Bước 6 không thấy plan/impl/role-model).

| Bước | `subagent_type` | Model | Tools | Vì sao |
|---|---|---|---|---|
| 1 Chốt spec | `fw-1-spec` | Sonnet | Read, Grep, Glob, Write, Bash | Senior Business Analyst - khảo sát scope, viết AC |
| 2 Research | `fw-2-research` | Sonnet | Read, Grep, Glob, Write, Bash, WebSearch, WebFetch | Senior Research Specialist - best practices kèm ví dụ tốt/xấu, gap analysis |
| 3 Mẫu role-model | `fw-3-role-model` | **Opus** | Read, Grep, Glob, Write, Bash (**KHÔNG có Edit**) | Reference Implementer - code mẫu throwaway đúng best practice, cố tình không bám convention repo; chất lượng bản mẫu quyết định chất lượng Bước 5 |
| 4 Kế hoạch | `fw-4-plan` | **Opus** | Read, Grep, Glob, Write, Bash | Senior Solution Architect - second-order effects (bắt buộc), Backward Planning (tuỳ chọn), chốt adopt/adapt/reject bản mẫu |
| 5 Triển khai | `fw-5-impl` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Senior Execution Engineer - code và test deliverables |
| 6 Review | `fw-6-review` | Sonnet | **Read, Grep, Glob, Write, Bash ONLY** | Senior Quality Auditor - review độc lập, **KHÔNG có Edit**, chỉ tìm lỗi không sửa |
| 7 Sửa lỗi | `fw-7-fix` | Sonnet | Read, Grep, Glob, Write, Edit, Bash | Senior Remediation Engineer - sửa toàn bộ Blocker/Major/Minor |

**Không dùng `subagent_type: "fork"`.** Fork thừa hưởng context của bạn, phá vỡ yêu cầu Bước 6 phải
"mù" ý định tác giả. Chạy tuần tự - không spawn song song, vì bước sau ăn output bước trước.

## Mẫu lời gọi Agent

Mỗi bước gửi 1 prompt ngắn - hướng dẫn chi tiết đã có sẵn trong definition của từng subagent:

```text
Bạn là subagent thực hiện BƯỚC <N>/7 của quy trình làm story.
Làm theo hướng dẫn trong definition của bạn (agent fw-<N>-<tên>).
Tham số:
- WORKFLOW_DIR: <đường dẫn tuyệt đối>
- STORY: <chỉ Bước 1: nội dung story đã lấy được>
```

## Các cổng người duyệt

**Sau Bước 1** - `Câu hỏi cần làm rõ` khác "không có": `AskUserQuestion` (1 câu/điểm mơ hồ, tối đa
4), ghi trả lời vào `01-spec.md` **trước** Bước 2.

**Sau Bước 2** - `Câu hỏi cần làm rõ` khác "không có" (mâu thuẫn nghiêm trọng best practice vs
convention, ảnh hưởng quyết định sản phẩm/kiến trúc): `AskUserQuestion`, ghi trả lời vào
`02-research.md` **trước** Bước 3. Bình thường auto chạy tiếp.

**Sau Bước 3 - không có cổng, chạy thẳng Bước 4.** Bản mẫu throwaway; sai sót bị Bước 4 lọc ở
"Role-model adoption". Chỉ dừng nếu Bước 3 báo `Câu hỏi cần làm rõ`.

**Sau Bước 5** - có mục bị chặn hoặc test đỏ chưa tự giải được: dừng, báo người dùng trước khi review.

**Sau Bước 6 - không hỏi người dùng, tự động chạy tiếp Bước 7.** Chỉ dừng khi thật sự không đọc được
diff (lỗi công cụ, không phải lỗi code). Mục đích Bước 7: khỏi phải quay lại yêu cầu "sửa mấy cái lỗi
đó đi" - sửa toàn bộ Blocker/Major (bắt buộc) và Minor (theo phán đoán, xem `fw-7-fix`) không cần hỏi.
`06-review.md` báo Blocker=Major=Minor=0: bỏ qua Bước 7, coi Bước 6 là bước cuối.

**Sau Bước 7 (hoặc Bước 6 nếu không có gì để sửa)** - cổng cuối: trình `## TÓM TẮT`, nhắc **chưa
commit / chưa merge / chưa push gì**.

## Nguyên tắc xuyên suốt

- **Không nhảy bước.** Thiếu file bước trước thì không chạy được bước sau.
- **Thiếu thông tin thì dừng, không đoán.** Ghi câu hỏi vào `## TÓM TẮT` rồi trả người dùng - kể cả
  Bước 7 ("tự động sửa" không có nghĩa đoán khi không chắc, chỉ là không cần hỏi *trước khi thử*).
- **Chỉ Bước 5 và Bước 7 được sửa code thật** (file trong source tree). Bước 1/2/4/6 chỉ đọc code
  thật và ghi `.md` trong `.workflows/<SLUG>/` - Bước 6 review/phân loại lỗi nhưng không `Edit`/
  `Write` lên code. **Bước 3 viết code mẫu chỉ dưới dạng code block trong `03-role-model.md`** -
  không tạo/sửa file trong source tree, đúng nghĩa "Spike Solution" (Extreme Programming): code để
  học, vứt đi sau khi dùng, không merge.
- **Role-model draft không phải deliverable.** Bước 4 chốt adopt/adapt/reject; Bước 5/7 dùng làm tài
  liệu đối chiếu, không copy nguyên văn. Xung đột theo thứ tự thẩm quyền `01-spec.md` > `04-plan.md`
  > convention thật của repo đích > `03-role-model.md`. Bước 6 không đọc nó.
- **Thiết kế mở rộng theo Open/Closed Principle (OCP) và ranh giới chống over-engineering (YAGNI).**
  Mã nguồn phải "open for extension, closed for modification": khi thêm trường hợp mới, tuyệt đối không
  chắp vá logic cũ bằng cách nối thêm các nhánh điều kiện (cascading if-else / switch-case với kiểm tra
  `==` cụ thể). Thay vào đó, thiết kế điểm mở rộng (extension points) hướng dữ liệu (data-driven dispatch
  table / dictionary mapping), strategy pattern, registry hoặc generalization. Ranh giới an toàn: không
  tạo abstract class/factory/dynamic plugin phức tạp khi chỉ cần bảng tra cứu (dict/map) hoặc hàm tổng quát.
- **Best practice ngành ưu tiên hơn convention nội bộ, nhưng không phải cớ over-engineering.** Bước 2
  xếp khuyến nghị vào nhóm trùng/nên-đổi/nên-giữ theo tiêu chí này; Bước 4/5/6 (over-engineering là
  Major)/7 đều áp dụng SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface
  Segregation, Dependency Inversion), loại bỏ abstraction/config thừa - chi tiết trong definition
  từng subagent.
