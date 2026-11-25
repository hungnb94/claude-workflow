# Migrate Java -> Kotlin dần dần

Read by `android-standards` khi task chạm code Java, migrate Java -> Kotlin, hoặc nối Flow/coroutine với code Java.


- Chỉ migrate file khi task sửa logic đáng kể trong file đó (không migrate chỉ vì đổi 1-2 dòng). Migrate là commit riêng đứng trước commit đổi hành vi; migrate lớn thì tách thành task riêng.
- Nguyên tắc strangler/boy-scout: chỉ migrate phần đang chạm trong task, không thêm code theo pattern cũ, không big-bang rewrite. [9]
- Đơn vị migrate là file/class/package, không phải cả module một lúc. [8,9]
- Viết/giữ test trước khi convert, dùng test hiện có làm lưới an toàn; mỗi bước convert phải build và test xanh trước khi sang bước tiếp theo, tách commit riêng cho bước convert tự động (J2K) và phần chỉnh tay để dễ review. [9]
- Thứ tự gợi ý khi không có ràng buộc khác: model/utility lá -> data source/repository -> ViewModel -> UI. [9]
- Giữ API cho caller Java còn lại bằng `@JvmStatic`, `@JvmOverloads`, `@file:JvmName`, `@Throws` khi cần; bật Kotlin Interoperability lint check của Android Studio để phát hiện điểm ma sát sớm. [8]

### Bridge Flow/coroutine cho code Java

1. **Java callback/listener -> Flow**: bọc listener bằng `callbackFlow { ...; awaitClose { unregister() } }`.
2. **Kotlin suspend/Flow -> caller Java** (Activity/Fragment Java còn lại): cung cấp hàm/lớp adapter Kotlin nhận `LifecycleOwner` + callback interface Java, bên trong dùng `lifecycleScope.launch` + `repeatOnLifecycle` để tự dừng đúng lifecycle; nếu dự án đang mở đã có ADR mô tả pattern bridge này thì theo ADR đó thay vì viết lại.
3. **Blocking bridge**: `runBlocking` chỉ dùng trong test hoặc entrypoint chắc chắn không chạy trên main thread - không bao giờ gọi trên main thread; ưu tiên 2 pattern trên trước.
4. UI Java còn dùng LiveData: `flow.asLiveData()` làm cầu tạm, gỡ bỏ khi UI đã chuyển sang Kotlin/Compose.

Ví dụ pattern 1:

```kotlin
fun locationUpdates(source: JavaLocationSource): Flow<Location> = callbackFlow {
    val listener = JavaLocationSource.Listener { trySend(it) }
    source.registerListener(listener)
    awaitClose { source.unregisterListener(listener) }
}
```

Ví dụ pattern 2:

```kotlin
fun collectForJava(owner: LifecycleOwner, flow: Flow<Data>, callback: JavaCallback<Data>) {
    owner.lifecycleScope.launch {
        owner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            flow.collect { callback.onData(it) }
        }
    }
}
```
