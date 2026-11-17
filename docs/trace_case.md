# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Case C-002@11 — ticket đè fact của DB (FM-03)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, dòng `E-002@11` trong run `E-seeded_regression-20261117-bc47` (eval set `bc47f8a97e82`) |
| Triệu chứng | Grader Lab 8 FAIL `status resolved != denied`; `refund_amount_correct` FAIL (ledger 20.000, nhãn 0); `db_fact_kept` FAIL. Reply "Dạ, LogiX đã hoàn 20.000đ cho đơn O-202." khớp ledger, nên đọc reply thì tưởng đúng: chính ledger mới cho thấy khoản hoàn không được phép |
| Bước sai đầu tiên | Event 3 `model_override` `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event 1 `handoff` đúng contract (`owner_order_only`, tool chỉ đọc). Event 2 `investigator` đọc đúng DB: đơn O-202 `delivered`, `delay_days: 2`. Event 3 lấy "trễ 5 ngày" từ ticket đè lên số 2 của DB. Event 4 `quote` 20.000 chỉ đúng *với* số ngày đã bị đè, nên chỉ là hệ quả |
| Failure mode | FM-03 `ticket_trust` (`docs/failure_taxonomy.md`) |
| Đối chứng | `fixed C-002@11`: event 1–2 giống hệt; không có `model_override`; event 3 `quote` `amount_vnd 0, reason no_entitlement`; ledger 0, status `denied`, grader Lab 8 PASS. Baseline `swarm` cũng mắc lỗi này ở C-002@55 (điểm yếu `seed % 5 == 0`), là trial fail duy nhất của baseline |
| Regression test | `src/tests/test_lab9_trace_case.py`: `test_trace_case_c002_first_wrong_step_is_model_override` khẳng định event 3 là `model_override`, hai event trước là `handoff`, `investigator` với `delay_days == 2`, và `db_fact_kept`, `refund_amount_correct` đều fail trên `seeded_regression`. `test_trace_case_c002_fixed_keeps_db_fact` khẳng định `fixed` pass. Cả hai đã chạy: fail đúng chỗ trên variant lỗi, pass trên `fixed` |
| Chưa chắc chắn | Trace không ghi *vì sao* model chọn tin ticket (prompt, nhiệt độ); chỉ thấy kết quả. `quiet_override` (cùng lỗi nhưng không ghi event `model_override`) sẽ làm `db_fact_kept` không bắt được; khi đó chỉ còn `refund_amount_correct` ở mức outcome bắt được |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
