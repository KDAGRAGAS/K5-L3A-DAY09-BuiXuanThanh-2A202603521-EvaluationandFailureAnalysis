# Judge audit

Chạy (trong `src/`):

```bash
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10      # PASS floors, exit 0
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 21   # FAIL floors, exit 1
```

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt cả ba | **dùng**, chỉ cho tiêu chí giọng văn, không chặn release |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Trượt κ và recall | **loại**, thay bằng grader code `reply_matches_ledger` |

Ma trận nhầm lẫn (FAIL là lớp dương, vì việc của judge là tìm lỗi):

| | tp | fp | fn | tn | Tỉ lệ FAIL quan sát → hiệu chỉnh Rogan-Gladen |
|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.28 → 0.30 |
| helpful | 9 | 0 | 21 | 70 | 0.09 → 0.30 |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha…" | PASS | FAIL | Người | Judge coi xưng "em" + "nha" là thân thiện. Sửa rubric: CS LogiX xưng "LogiX", gọi "anh/chị"; xưng "em"/"bạn" là FAIL. |
| 2 | H-017 "Dạ, bạn ơi LogiX đã hoàn 25.000đ…" | PASS | FAIL | Người | Cùng lỗi xưng hô. Thêm ví dụ âm "bạn ơi" vào rubric. |
| 3 | H-029 "Dạ, vui lòng chờ… không cần nhắn thêm." | PASS | FAIL | Người | Judge bị chữ "Dạ, vui lòng" đánh lừa. Rubric: câu mệnh lệnh cấm khách liên hệ là FAIL dù mở đầu lịch sự. |
| 4 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ…" | FAIL | PASS | Người | Judge phạt vì thiếu xin lỗi. Rubric: xin lỗi không bắt buộc khi kết quả có lợi cho khách; ngắn mà đủ ý là PASS. |
| 5 | H-051 "LogiX đã refund 90.000đ…" | FAIL | PASS | Người | Từ "refund" được CS LogiX cho phép. Thêm danh sách từ tiếng Anh được phép. |
| 6 | H-063 "…đã hoàn 20.000đ và sẽ hoàn thêm…" | PASS | FAIL | Người | Hứa ngoài kết quả hệ thống là lỗi nội dung, không phải giọng văn: chuyển sang grader code (so reply với ledger/status), không giao cho judge tone. |
| 7 | H-070 "…ạ 😂😂" | PASS | FAIL | Người | Rubric: emoji trong phản hồi khiếu nại là FAIL. |
| 8 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn…" | FAIL | PASS | **Judge** | Người đọc nhầm ticket. Sửa nhãn người thành FAIL trong bản CSV kế tiếp (không sửa file replay hiện tại). |
| 9 | H-088 "Dạ, dạ, LogiX đã hoàn 40.000đ…" | FAIL | PASS | Người | Lỗi gõ lặp từ không làm hỏng giọng văn. Rubric: chỉ phạt khi sai lặp làm đổi nghĩa. |
| 10 | H-094 "Da, LogiX da hoan 40.000đ…" (mất dấu) | PASS | FAIL | Người | Rubric: tiếng Việt không dấu là FAIL. |
| 11 | HL-015 "…đã hoàn 55.000đ cho đơn O-112" (ledger 40.000đ) | PASS | FAIL | Người | Judge không thấy ledger nên không thể biết số tiền sai. 18/21 fn của helpful là "sai tiền". |
| 12 | HL-016 / HL-028 (reply dài, xin lỗi nhiều lần, số tiền sai) | PASS | FAIL | Người | Judge thiên vị câu dài và lời xin lỗi (verbosity bias): xin lỗi nhiều che mất số tiền sai. |
| 13 | HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người | Sai xưng hô: đúng ra thuộc tiêu chí tone, không thuộc helpful. |

## Kết luận
- **tone_ok dùng được** (κ 0.757 ≥ 0.6, P 0.857 ≥ 0.8, R 0.8 ≥ 0.7), nhưng chỉ là metric theo dõi, không chặn release. Sau khi sửa rubric theo các case 1–10, cần gán nhãn lại và kiểm lại.
- **helpful bị loại.** Recall 0.30: judge bỏ sót 21/30 reply mà người chấm FAIL, trong đó 18 case là sai tiền (reply nói số khác ledger). Precision 1.0 không cứu được, vì một judge gần như luôn nói PASS thì không bao giờ báo nhầm nhưng cũng không tìm ra lỗi. Dùng judge này làm gate sẽ cho qua đúng loại lỗi đắt nhất. Thay bằng grader code `reply_matches_ledger` (FM-08), so số tiền trong reply với ledger. Đúng quy tắc: tiền luôn chấm bằng code.
- Tỉ lệ lỗi hiệu chỉnh của helpful (0.09 → 0.30) cho thấy judge báo thấp tỉ lệ lỗi thật khoảng 3 lần.
- **Rủi ro còn lại:** judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có tập held-out thật. Có ít nhất một nhãn người sai (H-081), nên nhãn người cũng cần kiểm chéo.
