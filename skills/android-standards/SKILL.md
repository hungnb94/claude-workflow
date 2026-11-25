---
name: android-standards
description: Android and Kotlin coding standards (coroutines, Flow, SOLID, Clean Architecture, MVVM and UDF, Hilt, Compose state, testing, Java to Kotlin migration). Use when writing, reviewing, or planning Android app code in Kotlin or Java, when the user asks for "chuẩn Android" or Android best practice, or when a workflow names it as the platform standards. Do not use for shared code in a Kotlin Multiplatform project (use kmp-standards) or for non-Android projects.
---

# Chuẩn Android/Kotlin

Chuẩn để viết, lên phương án và review code Android/Kotlin. Mọi ví dụ là minh hoạ generic, không gắn với
tên module, lớp hay pattern của một dự án cụ thể.

Quy ước **đã chốt** của dự án đang mở thắng (`AGENTS.md`, `CLAUDE.md`, `docs/adr/`, tài liệu kiến trúc),
rồi tới chuẩn này, rồi tới best practice chung. Khi mâu thuẫn thì theo dự án và nói rõ điều đó; không tự
đổi quy ước dự án. Dự án chưa chốt điểm nào thì dùng chuẩn này làm mặc định.

## Luật bắt buộc

- Chỉ áp cho code mới và code task đang chạm. Không sửa code không liên quan, không migrate hàng loạt
  code Java chưa đụng tới.
- Migrate Java -> Kotlin chỉ khi task sửa logic đáng kể trong file đó, và là commit riêng đứng trước
  commit đổi hành vi (`migration.md`).
- Test theo hành vi qua API công khai (mục Testing).
- Không thêm abstraction (interface 1 impl, Strategy, Hilt map multibinding, gateway) hay đưa component
  vào `:core:ui` hoặc module dùng chung khi chỉ có 1 consumer.
- Mỗi commit một thay đổi nhỏ; test không tính vào độ lớn thay đổi.

## Đọc thêm khi cần

| Task | Đọc |
|---|---|
| Chạm code Java, migrate Java -> Kotlin, hoặc nối Flow/coroutine với code Java | `migration.md` |
| Cần nguồn của một luật (số `[n]` cuối dòng) | `references.md` |

## Kotlin Coroutine

- Inject `CoroutineDispatcher` qua constructor, không hardcode `Dispatchers.IO`/`Default` - để test bằng `TestDispatcher`. [1]
- Suspend function phải main-safe: tự `withContext` bên trong, caller không cần biết dispatcher nào. [1]
- Tạo coroutine gắn UI bằng `viewModelScope.launch`; việc cần sống lâu hơn 1 màn hình dùng `CoroutineScope` được inject riêng, không phải `viewModelScope`. [1]
- Không dùng `GlobalScope`. [1]
- Không nuốt `CancellationException` (luôn rethrow); bắt exception cụ thể (`IOException`...), không bắt tràn lan `Exception`/`Throwable`; dùng `ensureActive()` trong vòng lặp dài để cancel hợp tác. [1]

## Kotlin Flow

- Flow cold và lazy mặc định - nhiều collector sẽ chạy lại producer nhiều lần; dùng `stateIn`/`shareIn` khi cần chia sẻ 1 lần cho nhiều collector. [2]
- Bắt lỗi bằng operator `catch` giữa chuỗi, không bọc `try/catch` quanh `collect`; nhớ `flowOn` chỉ ảnh hưởng upstream, không ảnh hưởng `catch` phía downstream. [2]
- Emit từ callback/thread khác dùng `callbackFlow { ...; awaitClose { ... } }`, không dùng `flow {}` - đây là cầu nối phù hợp để bridge code Java callback-based sang Flow. [2]
- Ở UI, collect bằng `collectAsStateWithLifecycle()` (Compose) hoặc `repeatOnLifecycle` - tránh lãng phí tài nguyên khi collect ngoài lifecycle hiển thị. [2,12]
- Room DAO trả `Flow<List<T>>` cho dữ liệu cần tự động emit khi DB đổi. [2]
- Đặt tên hàm trả stream dạng `get{Model}Stream(): Flow<Model>` khi cần phân biệt rõ với hàm one-shot (`get{Model}(): Model`) cùng tên gốc. [11]

## SOLID (áp dụng chọn lọc)

- Áp dụng tăng dần, có chọn lọc - không áp cứng cả 5 nguyên tắc lên mọi class; bắt đầu từ chỗ đau nhất (một interface quá lớn, một phụ thuộc khó test). [14]
- SRP: ViewModel không chứa logic truy cập dữ liệu/network; đẩy xuống Repository/UseCase. [3]
- SRP - phép thử 1 câu: mô tả class trong 1 câu, liệt kê MỌI trách nhiệm của class SAU thay đổi
  (không gom chung chung kiểu "xử lý broadcast"); nếu câu phải dùng "và/and" thì class vi phạm
  SRP -> tách trách nhiệm mới ra class riêng, test hành vi qua API công khai. Ví dụ: thêm `isEcsPass()`
  (luật nghiệp vụ ECS pass/fail) vào `FemomBroadcastSender` -> mô tả thành "gửi broadcast VÀ quyết
  định ECS pass/fail" -> tách `EcsPassPolicy`, test hành vi của luật ECS. [15]
- SRP - ranh giới YAGNI: không tách helper private nhỏ dùng state của class; không tách khi class chỉ có 1 lý do thay đổi; áp dụng chọn lọc như đầu mục. [14]
- OCP: thêm trường hợp mới bằng `sealed interface`/`sealed class` + `when` exhaustive hoặc bảng map/dispatch, không nối dài chuỗi `if-else`/`switch` kiểm tra `==` cụ thể. [14]
- DIP: ViewModel/UseCase phụ thuộc interface của Repository, bind bằng Hilt `@Binds`, không phụ thuộc class cụ thể. [7]
- ISP: interface nhỏ theo đúng nhu cầu của caller; không gộp nhiều trách nhiệm vào 1 interface lớn. [14]
- Không tạo interface cho class chỉ có 1 impl và không cần fake khi test - tránh over-engineering. [14]
- Không dùng Strategy/Hilt map multibinding/gateway khi chỉ có 1 consumer; không đưa component vào `:core:ui` (hay module dùng chung khác) khi chỉ có 1 nơi dùng - chờ nơi dùng thứ 2 (rule of three). [14,17]

## Clean Architecture ánh xạ vào UI -> Domain -> Data

- Chỉ dùng **nguyên tắc** dependency rule (lớp dưới không biết lớp trên; phụ thuộc qua abstraction hướng vào trong), ánh xạ vào đúng 3 lớp UI -> Domain -> Data đã có - không đặt tên lớp/khái niệm kiến trúc mới (không thêm 4 vòng đồng tâm kinh điển, không MVI/Redux). [3]
- Domain layer là **optional**: chỉ tạo UseCase khi logic dùng lại ở >= 2 ViewModel hoặc một ViewModel đã quá phức tạp. [3]
- UI/ViewModel không gọi thẳng DataSource - luôn qua Repository (1 nguồn dữ liệu/Single Source of Truth cho mỗi loại dữ liệu). [3]

## MVVM và luồng dữ liệu một chiều (UDF)

- Mỗi màn hình có đúng 1 `val uiState: StateFlow<T>` bất biến (data class/sealed class); nếu dự án chưa chốt cách dựng khác thì dùng `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)`. [3,4]
- Không expose kiểu mutable (`MutableStateFlow`) ra ngoài ViewModel - chỉ expose `StateFlow`/`Flow` immutable. [1]
- Unidirectional Data Flow: state chảy xuống UI, event/hành động chảy lên qua hàm public của ViewModel; lỗi biểu diễn như 1 trường trong `uiState` (message/flag), không throw ra UI. [3,4]
- ViewModel không giữ tham chiếu `Activity`/`Context`/`View`. [3]
- Sự kiện one-shot: ưu tiên mô hình hoá thành state khi có thể; chỉ dùng cơ chế event riêng khi thật sự cần thiết và dự án đã có quyết định rõ cho trường hợp đó. [4]

## Best practice bổ sung

### Xử lý lỗi

- Lỗi hiển thị cho người dùng là 1 trường trong `uiState` (message/flag), không phải exception ném ra ngoài UI. [4]
- Dùng `runCatching`/`Result` built-in của Kotlin chỉ ở ranh giới cụ thể (vd. Repository) khi cần phân biệt loại lỗi - không tạo wrapper `Result<Success, Error>` generic phủ toàn bộ data layer. [1,4]
- `runCatching` quanh code có suspend phải rethrow `CancellationException`, không nuốt. [1]

### Null-safety và bất biến

- Hạn chế dùng `!!`; ưu tiên `?:`, smart-cast, `val` thay vì `var`. [10]
- Ưu tiên data class bất biến, dùng `copy()` thay vì mutate; tách rõ collection mutable/read-only. [13]
- Khi Java gọi/được gọi từ Kotlin, khai báo rõ nullability (`@Nullable`/`@NonNull` phía Java) để tránh platform type rò rỉ vào code Kotlin. [8,10]

### Testing

- TDD Red -> Green -> Refactor: viết test fail trước, code tối thiểu cho pass, rồi refactor. [16]
- Hàm/class mới có logic (rẽ nhánh, vòng lặp, tính toán) phải có test nằm cùng commit của task; miễn trừ chỉ cho hàm ủy quyền thuần, getter, wiring. [6,16]
- Test theo hành vi qua API công khai (ViewModel `uiState`, UseCase, Repository), không bắt buộc 1 file test cho mỗi class; bỏ test cho class chỉ chứa dữ liệu, serializer/mapper đơn giản. Test không tính vào độ lớn thay đổi. [6,18]
- Ưu tiên fake hơn mock - fake nhẹ, không cần framework mock, dễ đọc; mock chỉ dùng khi cần verify tương tác (gọi bao nhiêu lần, tham số gì) mà fake không diễn đạt được. [6]
- Test coroutine/Flow bằng `runTest`, inject `TestDispatcher` (`StandardTestDispatcher`/`UnconfinedTestDispatcher`) thay vì dispatcher thật. [1,6]
- Test ViewModel qua `uiState` quan sát được, test Repository qua fake data source. [6]

### Dependency Injection với Hilt

- Constructor injection (`@Inject constructor`) là cách chính; dùng `@Binds` cho interface thay vì `@Provides`. [7]
- Tránh anti-pattern: inject `ViewModel` vào `Repository`; inject `Context` tràn lan; lạm dụng `@Singleton`; trộn Service Locator thủ công với Hilt; nhét business logic vào Module DI. [7]

### Compose state hoisting

- Hoist state lên tới common parent thấp nhất của mọi composable cần đọc state đó. [5]
- Ưu tiên truyền tham số (property drilling) hơn tạo wrapper class chỉ để gom state. [5]
- State UI thuần tuý (vd. dropdown mở/đóng) giữ tại composable (`remember`/`rememberSaveable`); chỉ đẩy lên ViewModel khi có business logic thật sự cần đọc/ghi state đó. [5]
