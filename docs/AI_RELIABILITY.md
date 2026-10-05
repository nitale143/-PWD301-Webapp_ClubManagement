# Độ tin cậy và tính lặp lại của AI Agent CLB

## Cách giải thích khi bảo vệ bài

Ứng dụng không dùng câu văn do LLM sinh ra làm nguồn số liệu nghiệp vụ. Với các câu hỏi đã hỗ trợ, backend xác định truy vấn, kiểm tra quyền, đọc database, tính toán bằng code và trả lời theo mẫu cố định. Khi chưa nhận diện được câu hỏi hoặc người được hỏi, hệ thống hỏi bổ sung hoặc từ chối kết luận; không nhờ model đoán số liệu.

Model vẫn có thể soạn **bản nháp** nội dung email hoặc gợi ý sự kiện/task. Bản nháp không phải dữ kiện đã xác minh. Backend kiểm tra mã thành viên, ban, thời gian, mức nhận task và quyền; BDH xem lại rồi duyệt mới thực thi. Mail mẫu lấy nội dung đã được CLB lưu, điền biến từ hồ sơ thật và vẫn chờ duyệt.

Không thể chứng minh mọi câu trả lời AI đúng 100%. Database có thể thiếu hoặc nhập sai dữ liệu, code có thể có lỗi, còn model có thể viết nội dung không đúng. Cam kết có thể kiểm thử là: **cùng câu hỏi tra cứu đã hỗ trợ, cùng phiên bản code, cùng quyền, cùng mốc thời gian và cùng trạng thái dữ liệu thì kết quả nghiệp vụ có cùng định dạng và thứ tự**. Nếu dữ liệu hoặc quyền đổi, câu trả lời đúng phải đổi theo.

## Những chốt kiểm soát đã triển khai

- `AI_STRICT_FACTS=true` mặc định: câu hỏi tra cứu không được hỗ trợ trả thông báo cố định; không gọi model viết một câu trả lời có vẻ đúng. Có thể tắt để thử chat sinh tự do, nhưng khi đó phản hồi được đánh dấu `unverified_draft` và không có cam kết lặp lại.
- Câu hỏi quỹ, hồ sơ, task, tóm tắt hôm nay và báo cáo đi qua truy vấn cố định. Số tiền tính bằng `Decimal`; danh sách được sắp xếp theo khóa ổn định. Khi điểm danh bằng nhau, kết quả có tiêu chí phụ thay vì chọn tùy ý.
- Tên thành viên trùng hoặc không nằm trong phạm vi được xem không được tự chọn. Người dùng được yêu cầu cung cấp MSSV. Đề xuất thiếu giờ, sự kiện hoặc ban phải bổ sung dữ kiện.
- Dữ liệu quỹ kỳ cũ và khoản thu mới là hai luồng riêng. Báo cáo tuần/tháng nói rõ phạm vi nguồn, không tự cộng hai nguồn rồi gọi đó là toàn bộ quỹ.
- Báo cáo lưu một bản chụp số liệu cùng ID nguồn, khoảng ngày và phạm vi quyền. Xuất Excel/nháp email dùng đúng bản đã lưu, không gọi LLM tính lại. Quyền được kiểm tra lại khi tải hoặc tạo nháp.
- Chat không tự gửi mail hoặc tự áp dụng sự kiện/task. Các thao tác duyệt riêng có kiểm tra quyền, CSRF và trạng thái đã xử lý.
- Nhật ký ghi người hỏi, loại truy vấn và thao tác để đối chiếu. Bộ test dùng database tạm, mô phỏng API/SMTP và kiểm tra cả trường hợp thiếu dữ liệu, phân quyền, dữ liệu lặp và prompt yêu cầu bịa số liệu.

## Cách trình diễn cho thầy

1. Hỏi hai lần `Tổng đã thu` trên cùng dữ liệu: nội dung và số tiền giống nhau, không gọi Gemini.
2. Hỏi `Xem task của SV123`: backend lấy task thật, hiển thị ID nguồn. Tài khoản thành viên không đọc được task của người khác.
3. Hỏi một nội dung chưa hỗ trợ như `Dự đoán chắc chắn ai sẽ đóng quỹ năm 2030`: chế độ mặc định không tự tạo con số.
4. Hỏi tên trùng: hệ thống yêu cầu MSSV, không chọn người đầu tiên.
5. Lưu báo cáo, sau đó sửa dữ liệu nguồn: bản đã lưu giữ nguyên; báo cáo mới phản ánh dữ liệu mới.
6. Nhờ tạo sự kiện hoặc gửi mail: chỉ xuất hiện đề xuất/nháp; chưa có tác động thật cho đến khi BDH duyệt.

Không dùng việc trả lời giống nhau làm bằng chứng rằng câu trả lời đúng. Tính lặp lại và tính đúng là hai tiêu chí khác nhau; muốn kiểm tra tính đúng cần đối chiếu bản ghi nguồn và quy tắc tính toán.

## Vì sao không chỉ đặt temperature=0 hoặc seed?

Temperature điều khiển độ ngẫu nhiên, không kiểm tra sự thật. Seed có thể tăng khả năng tái lập nhưng Google không cam kết kết quả hoàn toàn cố định. JSON schema ràng buộc cấu trúc, không bảo đảm các giá trị đúng nghĩa. Vì thế các kết quả nghiệp vụ dùng code và nguồn dữ liệu, không dựa vào tham số sinh văn bản để chứng minh tính đúng.

Tài liệu chính thức: [Gemini generation config](https://ai.google.dev/api/generate-content#v1beta.GenerationConfig), [Vertex AI về seed](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1beta1/GenerationConfig), [structured output và kiểm tra ngữ nghĩa](https://ai.google.dev/gemini-api/docs/structured-output), [hướng dẫn tính đúng của Gemini](https://ai.google.dev/gemini-api/docs/safety-guidance).

## Kho dữ liệu có cần nâng cấp thêm không?

Chốt tra cứu cố định và `AI_STRICT_FACTS` không yêu cầu vector database hay bảng cache. Hồ sơ, task, quỹ và điểm danh đã có bảng nguồn; bản chụp báo cáo dùng `ai_report_snapshot`, hội thoại bổ sung dùng `assistant_pending`. Với bản nâng cấp AI hiện tại, sao lưu SQLite trước khi khởi động lại; `db.create_all()` tạo các bảng mới còn thiếu. Nếu đã có `email_proposal` phiên bản cũ, thực hiện migration được hướng dẫn trong README.

Muốn báo cáo “task hoàn thành trong kỳ” chính xác trong tương lai cần lưu thời điểm hoàn thành riêng; hiện báo cáo chỉ đếm task có **hạn trong kỳ** và trạng thái hoàn thành **tại lúc lập báo cáo**. Muốn chứng minh mọi thay đổi dữ liệu cần quy trình kiểm tra đầu vào, đối soát và lưu lịch sử tương ứng; không thể thay thế bằng một lời nhắc cho LLM.
