---
name: kmp-standards
description: Kotlin Multiplatform coding standards (source set and shared code layout, expect/actual, Gradle multiplatform, coroutines and Flow across targets, Android/iOS/JVM/Native performance, multiplatform tests). Use when writing, reviewing, or planning code in a Kotlin Multiplatform project, when the user asks for "chuẩn KMP" or KMP best practice, or when a workflow names it as the platform standards. Do not use for an Android-only app without the Kotlin multiplatform plugin (use android-standards).
---

# Chuẩn Kotlin Multiplatform

Chuẩn để viết, lên phương án và review code Kotlin Multiplatform. Mọi ví dụ (interface `Clock`, tên
plugin, tên module...) là minh hoạ generic, không gắn với module, lớp hay target của một dự án cụ thể.

Quy ước KMP **đã chốt** của dự án đang mở thắng (`AGENTS.md`, `CLAUDE.md`, `docs/adr/`, tài liệu kiến
trúc), rồi tới chuẩn này, rồi tới best practice chung của cộng đồng Kotlin/JetBrains. Khi mâu thuẫn thì
theo dự án và nói rõ điều đó; không tự đổi quy ước dự án. Dự án chưa chốt điểm nào thì dùng chuẩn này
làm mặc định.

## Luật bắt buộc

- Chỉ áp cho code mới và code task đang chạm. Không tái cấu trúc module hay source set hàng loạt.
- Tách module `shared` khỏi app module (liên quan AGP 9) chỉ là gợi ý cho dự án khởi tạo mới; không bắt
  dự án đã chốt cấu trúc khác phải migrate.

## Đọc thêm khi cần

| Task | Đọc |
|---|---|
| Cần nguồn của một luật (số `[n]` cuối dòng) | `references.md` |

## 1. Tổ chức source set và shared code

- Dùng "default hierarchy template": code dùng cho một nhóm target (ví dụ mọi target Apple) đặt ở intermediate source set (`appleMain`/`iosMain`), không lặp lại ở từng `iosArm64Main`/`iosSimulatorArm64Main` riêng lẻ. [1]
- `commonMain` chỉ chứa logic Kotlin thuần và dependency multiplatform; không import API riêng platform (`android.*`, `platform.UIKit.*`, `java.*` ngoài phần có trong stdlib). [2]
- Chiều phụ thuộc một chiều: platform source set phụ thuộc vào `commonMain`, không có chiều ngược lại; UI native từng platform tiêu thụ module shared. [1]
- Share có chủ đích: ưu tiên share domain/data/business logic; chỉ share UI khi dự án đã chốt dùng Compose Multiplatform (quy ước dự án thắng). [2]
- Khi thêm target mới vào khối `kotlin { }`, kiểm tra lại source set trung gian nào được default hierarchy template tự tạo thêm để đặt code share đúng chỗ, tránh vừa lặp code ở `platformMain` riêng lẻ vừa có source set trung gian bỏ trống. [1]

## 2. expect/actual và API riêng từng platform

- Dùng `expect` khai báo trong `commonMain`, mỗi platform source set cung cấp `actual` cùng package; compiler tự kiểm tra đủ implementation - phù hợp cho hàm/property nhỏ, không giữ trạng thái. [3]
- Logic phức tạp hoặc cần test: định nghĩa interface trong `commonMain`, cung cấp implementation khác nhau ở platform source set, inject qua DI framework dự án đang dùng - không trộn hai cơ chế inject song song. [4]
- Trước khi tự viết platform code, kiểm tra thư viện multiplatform có sẵn cho nhu cầu phổ biến (network, logging...) trên klibs.io. [5]
- Đặt `expect`/`actual` theo từng package/domain rõ ràng thay vì gom nhiều `expect` không liên quan vào một file lớn - compiler báo lỗi thiếu `actual` theo từng khai báo, việc chia nhỏ giúp dễ dò khi thêm target mới. [3]

```kotlin
// commonMain
interface Clock {
    fun nowMillis(): Long
}

// androidMain / iosMain
class AndroidClock : Clock { override fun nowMillis() = System.currentTimeMillis() }
class IosClock : Clock { override fun nowMillis() = NSDate().timeIntervalSince1970.toLong() * 1000 }
```

## 3. Gradle multiplatform

- Tập trung version/dependency vào `gradle/libs.versions.toml`, dùng nhất quán `libs.*` cho mọi module - version catalog là bắt buộc, không phải "nice to have". [6]
- Đóng gói build logic dùng chung (khai báo target, compiler options, cấu hình Android library) thành convention plugin trong `build-logic` (included build); module tiêu thụ chỉ cần `plugins { id(...) }`. [6,7]
- Khai báo target tường minh, chỉ giữ target thật sự ship; bỏ `iosX64` khỏi tập build XCFramework nếu không cần chạy trên iOS Simulator Intel-based Mac. [8]
- Không dùng `allprojects`/`subprojects` để cấu hình chéo giữa các module. [6]
- Bật `org.gradle.caching`/`org.gradle.configuration-cache`/`org.gradle.parallel` để rút ngắn build, nhưng kiểm tra tương thích configuration cache với target iOS theo đúng phiên bản Kotlin Gradle Plugin đang dùng trước khi bật cứng trên CI - không khuyên bật tuyệt đối cho mọi dự án. [14]
- Khi cần phân phối framework Kotlin/Native cho app iOS **đã tồn tại sẵn** (không phải viết mới từ đầu) qua Swift Package Manager/CocoaPods, cân nhắc công cụ đóng gói như KMMBridge thay vì copy framework thủ công mỗi lần build - tham khảo thêm, không thuộc baseline bắt buộc. [17]

## 4. Coroutines và Flow đa target

- `kotlinx-coroutines-core` multiplatform là baseline cho mọi target (Android/iOS/JVM/Native); từ khi Kotlin/Native chuyển sang memory manager mới, không còn cần `freeze()` (đã deprecated, luôn no-op). [9,10]
- Inject `CoroutineDispatcher` qua constructor ở common code để test được bằng dispatcher giả lập; không hardcode dispatcher cụ thể trong shared logic. [9]
- Shared API trả `Flow`/`suspend` là cách tự nhiên phía Kotlin. Phía Swift, SKIE hoặc KMP-NativeCoroutines là lựa chọn **tuỳ chọn nâng cao** để export sang `async/await`/`AsyncSequence` - không bắt buộc, chỉ cân nhắc khi team muốn trải nghiệm Swift tự nhiên hơn. [11]
- Khi expose coroutine/Flow sang iOS, quản lý scope/hủy rõ ràng vì vòng đời do phía Swift quyết định, không phó mặc cho GC dọn. [9]
- Test coroutine/Flow trong `commonTest` bằng `runTest` của `kotlinx-coroutines-test`, inject `TestDispatcher` thay dispatcher thật để test chạy nhanh, deterministic trên mọi target. [9]

## 5. Performance theo target

### 5.1 Kotlin/Native memory manager (GC)

- Mặc định Concurrent Mark & Sweep chạy trên thread riêng, mark phase song song với thread ứng dụng để giảm pause time. [12]
- Đo GC pause thật trước khi tune (bật `kotlin.native.binary.enableSafepointSignposts=true` rồi quan sát qua Xcode Instruments trên target Apple) thay vì đoán theo cảm tính; `kotlin.native.binary.gc=pmcs`/`noop` chỉ dùng thử nghiệm ngắn hạn, `noop` không dùng production vì bộ nhớ tăng vô hạn. [12]

### 5.2 Binary size và framework export cho iOS

- Dùng XCFramework thay "universal (fat) framework" để không phải tự loại kiến trúc thừa trước khi publish; chỉ `export()` dependency thật sự cần lộ ra Objective-C/Swift, không export tất cả. [8]
- Tuỳ chọn nâng cao khi đã đo thấy binary size/memory là bottleneck thật: `-Xbinary=smallBinary=true`, Latin-1 string encoding - không bật mặc định cho mọi dự án. [13,12]
- Chọn static hay dynamic framework có chủ đích: static gộp vào app đơn giản hơn cho project mới; dynamic phù hợp khi cần chia sẻ giữa nhiều app target hoặc extension trên cùng máy - không có lựa chọn "luôn đúng", quyết định theo cấu trúc Xcode project thật của dự án. [8]

### 5.3 Build performance

- Version catalog + convention plugin (mục 3) là nền tảng; cộng thêm build cache/parallel execution để tái sử dụng output task giữa các lần build. [14]
- Configuration cache tăng tốc configuration phase nhưng cần verify tương thích task Kotlin/Native theo phiên bản Kotlin Gradle Plugin trước khi bật cứng trên CI. [14]

### 5.4 Interop overhead (Objective-C/Swift, cinterop)

- Tránh convert collection/string hai lần khi Swift dùng lại kiểu Kotlin: cast rõ ràng sang kiểu Objective-C gốc (`NSArray`/`NSDictionary`/`NSString`) khi chỉ cần đọc, thay vì để bridge tự convert rồi Swift copy lại. [15]
- Giữ bề mặt API export mỏng, hạn chế gọi qua biên Objective-C nhiều lần trong vòng lặp nóng. [15]

## 6. Testing multiplatform

- Đặt test dùng chung ở `commonTest` với `kotlin.test`; mỗi target vẫn giữ test source set riêng (`androidUnitTest`, `iosTest`...) cho phần không share được. [16]
- Chạy toàn bộ test multiplatform bằng `./gradlew allTests`, hoặc chỉ một target cụ thể bằng task `<target>Test` (ví dụ `iosSimulatorArm64Test`) khi cần lặp nhanh trên một platform. [16]
- Ưu tiên fake implement interface (khớp mục 2) hơn mock framework chỉ chạy trên JVM, vì mock JVM-only không chạy được trên target Native - hệ quả trực tiếp từ việc dùng interface + DI ở mục 2. [3,4]
