# Chuẩn Android/Kotlin cho android-standards-workflow

File tri thức nền, được mọi bước của feature-workflow đọc trực tiếp; không chứa chỉ dẫn điều phối.
File này + phần thân `SKILL.md` hợp lại là "nội dung command" theo mốc độ dài tham chiếu (~150-220
dòng / ~2000-3000 từ) - tách riêng để giữ `SKILL.md` gọn cho phần điều phối.

## 0. Thứ tự ưu tiên và phạm vi áp dụng

- Thứ tự ưu tiên khi mâu thuẫn: quy ước **đã chốt** của dự án đang mở (`AGENTS.md`, `CLAUDE.md`, `docs/adr/`, tài liệu kiến trúc) > file này > best practice ngành nói chung. Theo dự án, ghi chú mâu thuẫn vào output của bước đang làm - không tự đổi quy ước dự án.
- Dự án chưa chốt điểm nào thì áp file này làm mặc định.
- Phạm vi: áp cho code mới và code đang chạm trong story/task. Không mở rộng để sửa code không liên quan (không migrate hàng loạt code Java chưa đụng tới).
- Không áp đặt tên module/lớp/pattern cụ thể của một dự án nào - mọi ví dụ trong file là minh hoạ generic, dùng chung nhiều dự án Android.

## 1. Kotlin Coroutine

- Inject `CoroutineDispatcher` qua constructor, không hardcode `Dispatchers.IO`/`Default` - để test bằng `TestDispatcher`. [1]
- Suspend function phải main-safe: tự `withContext` bên trong, caller không cần biết dispatcher nào. [1]
- Tạo coroutine gắn UI bằng `viewModelScope.launch`; việc cần sống lâu hơn 1 màn hình dùng `CoroutineScope` được inject riêng, không phải `viewModelScope`. [1]
- Không dùng `GlobalScope`. [1]
- Không nuốt `CancellationException` (luôn rethrow); bắt exception cụ thể (`IOException`...), không bắt tràn lan `Exception`/`Throwable`; dùng `ensureActive()` trong vòng lặp dài để cancel hợp tác. [1]

## 2. Kotlin Flow

- Flow cold và lazy mặc định - nhiều collector sẽ chạy lại producer nhiều lần; dùng `stateIn`/`shareIn` khi cần chia sẻ 1 lần cho nhiều collector. [2]
- Bắt lỗi bằng operator `catch` giữa chuỗi, không bọc `try/catch` quanh `collect`; nhớ `flowOn` chỉ ảnh hưởng upstream, không ảnh hưởng `catch` phía downstream. [2]
- Emit từ callback/thread khác dùng `callbackFlow { ...; awaitClose { ... } }`, không dùng `flow {}` - đây là cầu nối phù hợp để bridge code Java callback-based sang Flow. [2]
- Ở UI, collect bằng `collectAsStateWithLifecycle()` (Compose) hoặc `repeatOnLifecycle` - tránh lãng phí tài nguyên khi collect ngoài lifecycle hiển thị. [2,12]
- Room DAO trả `Flow<List<T>>` cho dữ liệu cần tự động emit khi DB đổi. [2]
- Đặt tên hàm trả stream dạng `get{Model}Stream(): Flow<Model>` khi cần phân biệt rõ với hàm one-shot (`get{Model}(): Model`) cùng tên gốc. [11]

## 3. SOLID (áp dụng chọn lọc)

- Áp dụng tăng dần, có chọn lọc - không áp cứng cả 5 nguyên tắc lên mọi class; bắt đầu từ chỗ đau nhất (một interface quá lớn, một phụ thuộc khó test). [14]
- SRP: ViewModel không chứa logic truy cập dữ liệu/network; đẩy xuống Repository/UseCase. [3]
- OCP: thêm trường hợp mới bằng `sealed interface`/`sealed class` + `when` exhaustive hoặc bảng map/dispatch, không nối dài chuỗi `if-else`/`switch` kiểm tra `==` cụ thể. [14]
- DIP: ViewModel/UseCase phụ thuộc interface của Repository, bind bằng Hilt `@Binds`, không phụ thuộc class cụ thể. [7]
- ISP: interface nhỏ theo đúng nhu cầu của caller; không gộp nhiều trách nhiệm vào 1 interface lớn. [14]
- Không tạo interface cho class chỉ có 1 impl và không cần fake khi test - tránh over-engineering. [14]

## 4. Clean Architecture ánh xạ vào UI -> Domain -> Data

- Chỉ dùng **nguyên tắc** dependency rule (lớp dưới không biết lớp trên; phụ thuộc qua abstraction hướng vào trong), ánh xạ vào đúng 3 lớp UI -> Domain -> Data đã có - không đặt tên lớp/khái niệm kiến trúc mới (không thêm 4 vòng đồng tâm kinh điển, không MVI/Redux). [3]
- Domain layer là **optional**: chỉ tạo UseCase khi logic dùng lại ở >= 2 ViewModel hoặc một ViewModel đã quá phức tạp. [3]
- UI/ViewModel không gọi thẳng DataSource - luôn qua Repository (1 nguồn dữ liệu/Single Source of Truth cho mỗi loại dữ liệu). [3]

## 5. MVVM và luồng dữ liệu một chiều (UDF)

- Mỗi màn hình có đúng 1 `val uiState: StateFlow<T>` bất biến (data class/sealed class); nếu dự án chưa chốt cách dựng khác thì dùng `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)`. [3,4]
- Không expose kiểu mutable (`MutableStateFlow`) ra ngoài ViewModel - chỉ expose `StateFlow`/`Flow` immutable. [1]
- Unidirectional Data Flow: state chảy xuống UI, event/hành động chảy lên qua hàm public của ViewModel; lỗi biểu diễn như 1 trường trong `uiState` (message/flag), không throw ra UI. [3,4]
- ViewModel không giữ tham chiếu `Activity`/`Context`/`View`. [3]
- Sự kiện one-shot: ưu tiên mô hình hoá thành state khi có thể; chỉ dùng cơ chế event riêng khi thật sự cần thiết và dự án đã có quyết định rõ cho trường hợp đó. [4]

## 6. Best practice bổ sung

### 6.1 Xử lý lỗi

- Lỗi hiển thị cho người dùng là 1 trường trong `uiState` (message/flag), không phải exception ném ra ngoài UI. [4]
- Dùng `runCatching`/`Result` built-in của Kotlin chỉ ở ranh giới cụ thể (vd. Repository) khi cần phân biệt loại lỗi - không tạo wrapper `Result<Success, Error>` generic phủ toàn bộ data layer. [1,4]
- `runCatching` quanh code có suspend phải rethrow `CancellationException`, không nuốt. [1]

### 6.2 Null-safety và bất biến

- Hạn chế dùng `!!`; ưu tiên `?:`, smart-cast, `val` thay vì `var`. [10]
- Ưu tiên data class bất biến, dùng `copy()` thay vì mutate; tách rõ collection mutable/read-only. [13]
- Khi Java gọi/được gọi từ Kotlin, khai báo rõ nullability (`@Nullable`/`@NonNull` phía Java) để tránh platform type rò rỉ vào code Kotlin. [8,10]

### 6.3 Testing

- Ưu tiên fake hơn mock - fake nhẹ, không cần framework mock, dễ đọc; mock chỉ dùng khi cần verify tương tác (gọi bao nhiêu lần, tham số gì) mà fake không diễn đạt được. [6]
- Test coroutine/Flow bằng `runTest`, inject `TestDispatcher` (`StandardTestDispatcher`/`UnconfinedTestDispatcher`) thay vì dispatcher thật. [1,6]
- Test ViewModel qua `uiState` quan sát được, test Repository qua fake data source. [6]

### 6.4 Dependency Injection với Hilt

- Constructor injection (`@Inject constructor`) là cách chính; dùng `@Binds` cho interface thay vì `@Provides`. [7]
- Tránh anti-pattern: inject `ViewModel` vào `Repository`; inject `Context` tràn lan; lạm dụng `@Singleton`; trộn Service Locator thủ công với Hilt; nhét business logic vào Module DI. [7]

### 6.5 Compose state hoisting

- Hoist state lên tới common parent thấp nhất của mọi composable cần đọc state đó. [5]
- Ưu tiên truyền tham số (property drilling) hơn tạo wrapper class chỉ để gom state. [5]
- State UI thuần tuý (vd. dropdown mở/đóng) giữ tại composable (`remember`/`rememberSaveable`); chỉ đẩy lên ViewModel khi có business logic thật sự cần đọc/ghi state đó. [5]

## 7. Migrate Java -> Kotlin dần dần

- Nguyên tắc strangler/boy-scout: chỉ migrate phần đang chạm trong story, không thêm code theo pattern cũ, không big-bang rewrite. [9]
- Đơn vị migrate là file/class/package, không phải cả module một lúc. [8,9]
- Viết/giữ test trước khi convert, dùng test hiện có làm lưới an toàn; mỗi bước convert phải build và test xanh trước khi sang bước tiếp theo, tách riêng commit tự động (J2K) khỏi commit chỉnh tay để dễ review. [9]
- Thứ tự gợi ý khi không có ràng buộc khác: model/utility lá -> data source/repository -> ViewModel -> UI. [9]
- Giữ API cho caller Java còn lại bằng `@JvmStatic`, `@JvmOverloads`, `@file:JvmName`, `@Throws` khi cần; bật Kotlin Interoperability lint check của Android Studio để phát hiện điểm ma sát sớm. [8]

### Bridge Flow/coroutine cho code Java

1. **Java callback/listener -> Flow**: bọc listener bằng `callbackFlow { ...; awaitClose { unregister() } }`.
2. **Kotlin suspend/Flow -> caller Java** (Activity/Fragment Java còn lại): cung cấp hàm/lớp adapter Kotlin nhận `LifecycleOwner` + callback interface Java, bên trong dùng `lifecycleScope.launch` + `repeatOnLifecycle` để tự dừng đúng lifecycle; nếu dự án đang mở đã có ADR mô tả pattern bridge này thì theo ADR đó thay vì viết lại.
3. **Blocking bridge**: `runBlocking` chỉ dùng trong test hoặc entrypoint chắc chắn không chạy trên main thread - không bao giờ gọi trên main thread; ưu tiên 2 pattern trên trước.
4. UI Java còn dùng LiveData: `flow.asLiveData()` làm cầu tạm, gỡ bỏ khi UI đã chuyển sang Kotlin/Compose.

```kotlin
// (1) Bridge Java callback/listener -> Flow
fun locationUpdates(source: JavaLocationSource): Flow<Location> = callbackFlow {
    val listener = JavaLocationSource.Listener { trySend(it) }
    source.registerListener(listener)
    awaitClose { source.unregisterListener(listener) }
}
```

```kotlin
// (2) Adapter cho Java Activity/Fragment gọi Kotlin suspend/Flow
fun collectForJava(owner: LifecycleOwner, flow: Flow<Data>, callback: JavaCallback<Data>) {
    owner.lifecycleScope.launch {
        owner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            flow.collect { callback.onData(it) }
        }
    }
}
```

## 8. Nguồn tham chiếu

1. Kotlin coroutines best practices - [developer.android.com/kotlin/coroutines/coroutines-best-practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)
2. Kotlin Flow on Android - [developer.android.com/kotlin/flow](https://developer.android.com/kotlin/flow)
3. App architecture guide - [developer.android.com/topic/architecture](https://developer.android.com/topic/architecture)
4. UI layer - [developer.android.com/topic/architecture/ui-layer](https://developer.android.com/topic/architecture/ui-layer)
5. Compose - Where to hoist state - [developer.android.com/develop/ui/compose/state-hoisting](https://developer.android.com/develop/ui/compose/state-hoisting)
6. Testing - Test doubles - [developer.android.com/training/testing/fundamentals/test-doubles](https://developer.android.com/training/testing/fundamentals/test-doubles)
7. Dependency injection with Hilt - [developer.android.com/training/dependency-injection/hilt-android](https://developer.android.com/training/dependency-injection/hilt-android)
8. Kotlin-Java interop - [developer.android.com/kotlin/interop](https://developer.android.com/kotlin/interop)
9. Martin Fowler - Strangler Fig pattern for mobile apps - [martinfowler.com/articles/strangler-fig-mobile-apps.html](https://martinfowler.com/articles/strangler-fig-mobile-apps.html)
10. Kotlin null safety - [kotlinlang.org/docs/null-safety.html](https://kotlinlang.org/docs/null-safety.html)
11. Now in Android (Google reference app) - [github.com/android/nowinandroid](https://github.com/android/nowinandroid)
12. Manuel Vivo (Android DevRel) - "A safer way to collect flows from Android UIs" - loạt bài coroutines/Flow trên Android Developers Medium.
13. Marcin Moskała - *Effective Kotlin* (kt.academy) - "Item 1: Limit mutability".
14. droidcon - "SOLID principles in practice: the clean architecture" (droidcon.com).
