---
name: android-standards-workflow
disable-model-invocation: true
description: Lớp priming chuẩn Android/Kotlin (Coroutine, Flow, SOLID, Clean Architecture, MVVM, migrate Java->Kotlin) rồi chạy feature-workflow 7 bước với các chuẩn đó làm ràng buộc. Chỉ chạy khi người dùng gõ /android-standards-workflow.
---

# Android Standards Workflow (priming + feature-workflow)

Lớp phủ chuẩn Android/Kotlin trước khi chạy quy trình 7 bước - **không** thay thế, không làm lại logic của skill `feature-workflow`.

**Câu mở đầu bắt buộc:** "Tôi đang dùng skill android-standards-workflow: nạp chuẩn Android/Kotlin rồi chạy feature-workflow."

## Cổng chặn

- `$ARGUMENTS` rỗng hoặc chỉ khoảng trắng: hỏi người dùng feature/task là gì, **không bịa, không gọi feature-workflow** cho tới khi có câu trả lời. Lý do: sau khi nối khối ràng buộc ở Bước 3, args không bao giờ rỗng nữa nên cổng hỏi mặc định của feature-workflow không còn tác dụng.
- Không thấy dấu hiệu dự án Android (không có `build.gradle`/`build.gradle.kts`/`settings.gradle*` hoặc `AndroidManifest.xml`): báo cho người dùng và hỏi có muốn tiếp tục không.
- Các cổng khác (bug đã xảy ra, story quá nhỏ/quá lớn): để **feature-workflow** tự xử lý, không lặp lại ở đây.

## Bước 1 - Nạp chuẩn

Xác định `[STANDARDS_PATH]` = đường dẫn tuyệt đối của `standards.md` cùng thư mục skill này (dùng dòng "Base directory for this skill" mà Claude Code cung cấp khi nạp skill; không có thì Glob `**/android-standards-workflow/standards.md`). `Read` toàn bộ `standards.md` để làm ngữ cảnh nền cho mọi quyết định tiếp theo. Không đọc được thì dừng và báo lỗi - không chạy tiếp mà thiếu chuẩn.

## Bước 2 - Nhận biết quy ước dự án đang mở

Glob `AGENTS.md`, `CLAUDE.md`, `docs/adr/`, `docs/architecture*` ở repo root đang mở; đọc lướt để nhận biết điểm nào dự án đã chốt khác chuẩn ở Bước 1. Không sửa các file này, không chép nội dung vào args - `feature-workflow` Bước 1 sẽ tự khảo sát convention khi chạy.

## Bước 3 - Gọi feature-workflow

Dùng **Skill tool** với `skill: "feature-workflow"` (không thấy thì thử `workflow:feature-workflow`). Ghép `args` theo đúng mẫu sau - task của người dùng đứng **đầu, nguyên văn** (để slug và việc dò Jira key của feature-workflow dựa đúng trên phần này), khối ràng buộc đứng cuối:

```text
<nguyên văn $ARGUMENTS của người dùng>

---
Ràng buộc bất biến (từ /android-standards-workflow):
- Mọi bước tuân theo chuẩn Android/Kotlin tại [STANDARDS_PATH] - đọc trực tiếp file này.
- Thứ tự ưu tiên: quy ước đã chốt của dự án (AGENTS.md, CLAUDE.md, docs/adr) > file chuẩn trên > best practice chung.
- Bước 1 ghi nguyên văn 2 dòng trên vào mục "Ràng buộc bất biến" của 01-spec.md.
- Nếu STORY được thay bằng nội dung Jira ticket, nối nguyên khối này vào cuối STORY.
```

Quy tắc khi ghép: thay `[STANDARDS_PATH]` bằng đường dẫn tuyệt đối thật đã xác định ở Bước 1; khối ràng buộc không được chứa token dạng `ABC-123` (trùng regex dò Jira key của feature-workflow); không chép nội dung `standards.md` vào args - chỉ trỏ đường dẫn.

## Sau khi gọi

`feature-workflow` tiếp quản toàn bộ (resume, cổng duyệt, 7 bước Research/Plan/Impl/Review/Fix). Skill này không tự spawn subagent, không tự làm lại Research/Plan/Impl/Review/Fix. Nếu Skill tool không tìm thấy `feature-workflow`: báo người dùng cài plugin `workflow@claude-workflow`, không tự mô phỏng quy trình 7 bước.
