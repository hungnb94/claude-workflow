# Catalog kỹ thuật legacy / incremental refactoring

Nguồn duy nhất cho thang chi phí, Kiểm tra SRP và định nghĩa kỹ thuật. Đọc khi code đích là legacy
chưa test (không có test bao phủ, hoặc không khởi tạo được trong test), hoặc khi cần Kiểm tra SRP. Đây là heuristic tổng hợp từ Feathers,
Fowler, Hammant, Ellnestam/Brolund, không phải quy tắc chuẩn ngành.

Luật mũ (Two Hats): mục `Mũ: feature` chỉ dành cho task thêm tính năng; task refactor thuần
(ví dụ phương án refactor của `/solution-brainstorm`) chỉ dùng mục `Mũ: chung`.

## Kiểm tra SRP

- Phạm vi: class/module và function mà task sửa hoặc thêm code vào, có test hay chưa (không tính code chỉ đọc/gọi tới). Đích lẫn trách nhiệm khi có ≥2 lý do thay đổi độc lập; ranh giới YAGNI: không tính helper private nhỏ dùng state, không tách chỉ vì file dài.
- Quy tắc cứng: không đặt trách nhiệm MỚI vào đích; trách nhiệm mới ở class mới (Sprout Class/Wrap Class, không Sprout/Wrap Method).
- Task sửa logic trong vùng lẫn, đích có lưới test và phần tách vừa ngân sách: Extract Method/Class (Fowler) ở commit `refactor` riêng trước, code tách ra có unit test happy/edge/error, rồi mới sửa ở code mới.
- Không có lưới test hoặc tách vượt ngân sách: sửa tại chỗ tối thiểu, ghi `nợ SRP: <đích> - <lý do không tách>`. Không Extract Class bằng tay trên code chưa có test.
- Chỉ tách trách nhiệm task chạm tới; trách nhiệm còn lại ghi vào `Đề xuất refactor tiếp` (trách nhiệm, file:line, kỹ thuật).

## Kiểm tra phạm vi owner

- Phạm vi: phụ thuộc vòng đời/đăng ký mà task thêm hoặc đổi chỗ gắn (lifecycle owner, listener host, scope, Context). Liệt kê owner ứng viên từ hẹp tới rộng, mỗi owner kèm nguyên nhân khiến đích phải dừng hay sống theo nó.
- Quy tắc cứng: dùng owner hẹp nhất còn sống lâu hơn đích và đúng nguyên nhân, do caller truyền vào; đích không nhận object rộng hơn rồi tự lấy owner ra.
- Hành vi hôm nay giống nhau không phải hòa: owner hẹp hơn thắng. Owner rộng hơn phải ghi `Lý do scope rộng hơn`; "ít phải truyền thêm" không phải lý do.

## Thang chi phí

| Bậc | fw (thêm tính năng) | Đủ khi | Leo bậc kế khi |
|---|---|---|---|
| 1 | Sprout/Wrap | Thay đổi nhỏ, độc lập, không cần sửa logic cũ | Phải sửa logic đang có, hoặc điểm gọi buộc thêm nhánh điều kiện |
| 2 | dependency-breaking Feathers | Sửa/tạo seam được trong ngân sách slice  | Phải thay thành phần có ≥2 consumer, đường cũ/mới cùng tồn tại qua nhiều slice |
| 3 | Branch by Abstraction | Phần thay thế nằm trong codebase | Thay cả hệ thống con qua ranh giới ngoài |
| 4 | Strangler Fig | Bậc cuối | Không có - đề nghị chẻ story |

Mikado Method là lớp phủ áp dụng ở mọi bậc, không phải một bậc.
Thứ tự chi phí trong bậc 1 của fw: Sprout Method < Sprout Class < Wrap Method < Wrap Class.

## Quy ước chung

- Leo bậc phải ghi `Lý do bậc rẻ hơn không đủ`; thiếu thông tin thì ghi câu hỏi, không đoán.
- Chỉ so bậc giữa các option cùng phạm vi owner (`## Kiểm tra phạm vi owner`); bậc rẻ hơn không bù cho owner rộng hơn.
- Sprout/Wrap chỉ chèn MỘT điểm gọi không điều kiện (hoặc rename + method bọc), không thêm nhánh if-else vào method cũ.
- Không dựng abstraction mới khi <2 consumer; Branch by Abstraction chỉ khi ≥2 consumer.
- Seam Extract Interface có fake trong test không tính là abstraction 1 consumer.
- Không tự leo bậc khi thực thi; không đạt thì ghi lý do và BLOCKED.

## Test đầy đủ cho code mới

- Code sprout/wrap/extract mới có unit test viết TRƯỚC (TDD), phủ happy/edge/error, nằm cùng commit.
- Điểm gọi vào legacy có characterization test nếu đưa vào harness được; nếu không, ghi `nợ chưa test: <symbol>` vào plan/output.
- Không đặt ngưỡng coverage số.

## Kỹ thuật

### Sprout Method

- Bậc: 1
- Mũ: feature
- Khi dùng: hành vi mới độc lập và class cũ khởi tạo được trong test.
- Khi leo bậc: phải sửa logic đang có, hoặc class cũ không khởi tạo được (sang Sprout Class).
- Các bước: viết test fail cho method mới (happy/edge/error); viết method mới dùng bảng tra thay vì nhánh; chèn MỘT lời gọi không điều kiện trong method cũ.
- Test bắt buộc: unit test happy/edge/error cho method mới; characterization test cho điểm gọi nếu đưa vào harness được.
- Nợ còn lại: code cũ vẫn chưa test.

Ví dụ (pseudo-Python), không dùng `if type ==` trong method cũ:

```python
RATE_BY_REGION = {"eu": 0.2, "us": 0.07}

def tax_for(region, amount):
    return amount * RATE_BY_REGION[region]

def legacy_invoice(order):
    ...
    order.tax = tax_for(order.region, order.amount)
```

Test: `test_tax_for_known_region`, `test_tax_for_zero_amount`, `test_tax_for_unknown_region_raises`.

### Sprout Class

- Bậc: 1
- Mũ: feature
- Khi dùng: class cũ không đưa vào harness được; class mới là class cụ thể, không interface.
- Khi leo bậc: hành vi mới buộc sửa logic cũ, hoặc cần thay thế thành phần có ≥2 consumer.
- Các bước: viết test fail cho class mới; viết class mới; chèn MỘT điểm gọi không điều kiện tại code cũ.
- Test bắt buộc: unit test happy/edge/error cho class mới; ghi nợ chưa test cho điểm gọi nếu không đưa vào harness được.
- Nợ còn lại: code cũ vẫn chưa test.

### Wrap Method

- Bậc: 1
- Mũ: feature
- Khi dùng: hành vi mới phải chạy ngay trước/sau mọi lời gọi method cũ.
- Khi leo bậc: hành vi mới phải xen vào giữa logic cũ.
- Các bước: đổi tên method cũ; tạo method cùng tên cũ gọi hành vi mới (test-first) và method đã đổi tên.
- Test bắt buộc: unit test happy/edge/error cho hành vi mới; kiểm thứ tự gọi trước/sau.
- Nợ còn lại: code cũ vẫn chưa test; tên method dễ gây hiểu lầm.

### Wrap Class

- Bậc: 1
- Mũ: feature
- Khi dùng: như Wrap Method nhưng không muốn làm to class cũ, hoặc nhiều nơi gọi cần cùng lớp bọc (decorator).
- Khi leo bậc: lớp bọc buộc phải dựng interface mới cho <2 consumer, hoặc phải sửa logic cũ.
- Các bước: viết test fail cho lớp bọc; dùng lại kiểu sẵn có của class cũ; thay chỗ khởi tạo bằng lớp bọc.
- Test bắt buộc: unit test happy/edge/error cho lớp bọc; ghi nợ chưa test cho class cũ.
- Nợ còn lại: code cũ vẫn chưa test.

### Parameterize Constructor

- Bậc: 2
- Mũ: chung
- Khi dùng: constructor tự tạo dependency cứng nên không khởi tạo được trong test.
- Khi leo bậc: dependency có ≥2 consumer cần thay song song.
- Các bước: thêm tham số dependency vào constructor; giữ constructor cũ truyền giá trị mặc định; viết characterization test.
- Test bắt buộc: characterization test chốt hành vi hiện tại trước khi sửa.
- Nợ còn lại: constructor cũ còn tồn tại để tương thích.

### Extract Interface

- Bậc: 2
- Mũ: chung
- Khi dùng: cần thay dependency bằng fake trong test.
- Khi leo bậc: interface sẽ có ≥2 consumer thật và cần chạy đường cũ/mới song song.
- Các bước: trích interface chỉ gồm phương thức được dùng; cho class cũ implement; truyền fake trong test.
- Test bắt buộc: characterization test dùng fake; seam có fake không tính là abstraction 1 consumer.
- Nợ còn lại: interface chỉ phục vụ seam, cần gỡ khi không còn cần.

### Extract and Override Call

- Bậc: 2
- Mũ: chung
- Khi dùng: một lời gọi phụ thuộc ngoài (I/O, thời gian) chặn việc kiểm thử method.
- Khi leo bậc: nhiều lời gọi ngoài cần thay, hoặc subclass test không đủ.
- Các bước: trích lời gọi thành method riêng; override trong subclass dùng cho test; viết characterization test.
- Test bắt buộc: characterization test trên subclass test.
- Nợ còn lại: subclass test và method trích còn tồn tại.

### Branch by Abstraction

- Bậc: 3
- Mũ: chung
- Khi dùng: thay thành phần có ≥2 consumer, đường cũ/mới cùng tồn tại qua nhiều slice. Parallel Change (expand, migrate, contract) là biến thể nhỏ.
- Khi leo bậc: thay cả hệ thống con qua ranh giới ngoài (sang Strangler Fig).
- Các bước: dựng abstraction trên đường cũ; chuyển từng consumer sang abstraction; thêm đường mới sau abstraction; chuyển hẳn rồi xoá đường cũ.
- Test bắt buộc: characterization test đường cũ; unit test happy/edge/error đường mới; mỗi bước giữ test xanh.
- Nợ còn lại: hai đường cùng tồn tại cho tới bước xoá.

### Strangler Fig

- Bậc: 4
- Mũ: chung
- Khi dùng: thay hệ thống con qua ranh giới ngoài, chuyển dần từng chức năng.
- Khi leo bậc: không có - đề nghị chẻ story.
- Các bước: đặt lớp định tuyến ở ranh giới; chuyển từng chức năng sang hệ thống mới; gỡ chức năng cũ khi không còn traffic.
- Test bắt buộc: characterization test ở ranh giới cho cả hai đường; unit test happy/edge/error cho phần mới.
- Nợ còn lại: hệ thống cũ chạy song song cho tới khi gỡ.

### Mikado Method

- Bậc: lớp phủ
- Mũ: chung
- Khi dùng: một bước làm vỡ nhiều chỗ ngoài vùng dự kiến. Quy trình: đặt goal, thử đổi ngây thơ, nếu vỡ (build/test đỏ ngoài dự kiến) thì revert toàn bộ lần thử và ghi prerequisite làm node con, lặp lại, làm từ lá về goal, mỗi lá xanh.
- Khi leo bậc: không áp dụng, Mikado đi kèm bậc đã chọn.
- Các bước: ghi graph dạng checklist lồng `- [ ] Goal` / `- [ ] Prereq` / `- [x] ... (xanh)`; revert theo cách hoàn tác của workflow; fw ghi graph ở `04-plan.md` mục `### Mikado graph`; graph phát hiện thêm khi thực thi ghi ở output impl.
- Test bắt buộc: mỗi lá xanh trước khi sang lá kế; review kiểm qua diff không còn sửa dở của lần thử hỏng (call site nửa cũ nửa mới, code chết, TODO tạm).
- Nợ còn lại: không có nếu mọi lá xanh.
