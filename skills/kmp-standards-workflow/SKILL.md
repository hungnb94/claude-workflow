---
name: kmp-standards-workflow
disable-model-invocation: true
description: Lớp priming chuẩn Kotlin Multiplatform (tổ chức shared code/source set, expect/actual, Gradle multiplatform, coroutines/Flow đa target, performance Android/iOS/JVM/Native) rồi chạy feature-workflow 7 bước với các chuẩn đó làm ràng buộc. Chỉ chạy khi người dùng gõ /kmp-standards-workflow.
---

# KMP Standards Workflow (priming + feature-workflow)

Lớp phủ chuẩn Kotlin Multiplatform trước khi chạy quy trình 7 bước - **không** thay thế, không làm lại logic của skill `feature-workflow`.

**Câu mở đầu bắt buộc:** "Tôi đang dùng skill kmp-standards-workflow: nạp chuẩn Kotlin Multiplatform rồi chạy feature-workflow."

## Cổng chặn

- `$ARGUMENTS` rỗng hoặc chỉ khoảng trắng: hỏi người dùng feature/task là gì, **không bịa, không gọi feature-workflow** cho tới khi có câu trả lời. Lý do: sau khi nối khối ràng buộc ở Bước 3, args không bao giờ rỗng nữa nên cổng hỏi mặc định của feature-workflow không còn tác dụng.
- Không thấy dấu hiệu dự án KMP: không có file Gradle (`settings.gradle.kts`, `build.gradle.kts`, `*.gradle`, `gradle/libs.versions.toml`) chứa plugin `kotlin("multiplatform")` / `org.jetbrains.kotlin.multiplatform` / alias `kotlin-multiplatform`, **và** không có thư mục source set KMP (`src/commonMain`, hoặc `src/<target>Main` như `androidMain`/`iosMain`/`jvmMain` đi cùng `commonMain`): báo cho người dùng và hỏi có muốn tiếp tục không. Một trong hai tín hiệu là đủ để qua cổng; thiếu `AndroidManifest.xml` không phải tín hiệu âm vì dự án KMP có thể không có Android target.
- Các cổng khác (bug đã xảy ra, story quá nhỏ/quá lớn): để **feature-workflow** tự xử lý, không lặp lại ở đây.

## Bước 1 - Nạp chuẩn

Xác định `[STANDARDS_PATH]` = đường dẫn tuyệt đối của `standards.md` cùng thư mục skill này (dùng dòng "Base directory for this skill" mà Claude Code cung cấp khi nạp skill; không có thì Glob `**/kmp-standards-workflow/standards.md`). `Read` toàn bộ `standards.md` để làm ngữ cảnh nền cho mọi quyết định tiếp theo. Không đọc được thì dừng và báo lỗi - không chạy tiếp mà thiếu chuẩn.

## Bước 2 - Nhận biết quy ước dự án đang mở

Glob `AGENTS.md`, `CLAUDE.md`, `docs/adr/`, `docs/architecture*` ở repo root đang mở; đọc lướt để nhận biết điểm nào dự án đã chốt khác chuẩn ở Bước 1. Không sửa các file này, không chép nội dung vào args - `feature-workflow` Bước 1 sẽ tự khảo sát convention khi chạy.

## Bước 3 - Gọi feature-workflow

Dùng **Skill tool** với `skill: "feature-workflow"`. Ghép `args` theo đúng mẫu sau - task của người dùng đứng **đầu, nguyên văn** (để slug và việc dò Jira key của feature-workflow dựa đúng trên phần này), khối ràng buộc đứng cuối:

```text
<nguyên văn $ARGUMENTS của người dùng>

---
Ràng buộc bất biến (từ /kmp-standards-workflow):
- Mọi bước tuân theo chuẩn Kotlin Multiplatform tại [STANDARDS_PATH] - đọc trực tiếp file này.
- Thứ tự ưu tiên: quy ước đã chốt của dự án (AGENTS.md, CLAUDE.md, docs/adr) > file chuẩn trên > best practice chung.
- Bước 1 ghi nguyên văn 2 dòng trên vào mục "Ràng buộc bất biến" của 01-spec.md.
- Nếu STORY được thay bằng nội dung Jira ticket, nối nguyên khối này vào cuối STORY.
```

Quy tắc khi ghép: thay `[STANDARDS_PATH]` bằng đường dẫn tuyệt đối thật đã xác định ở Bước 1; khối ràng buộc không được chứa token dạng `ABC-123` (trùng regex dò Jira key của feature-workflow); không chép nội dung `standards.md` vào args - chỉ trỏ đường dẫn.

## Sau khi gọi

`feature-workflow` tiếp quản toàn bộ (resume, cổng duyệt, 7 bước Research/Plan/Impl/Review/Fix). Skill này không tự spawn subagent, không tự làm lại Research/Plan/Impl/Review/Fix. Nếu Skill tool không tìm thấy `feature-workflow`: báo người dùng cài plugin `workflow@claude-workflow`, không tự mô phỏng quy trình 7 bước.
