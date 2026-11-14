# Báo cáo cá nhân --- Day 6: Data Ingestion Engineering

## Dữ liệu và pipeline

-   **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:**
    -   Chủ đề: AI và Machine Learning.
    -   Corpus: AI-For-Beginners của Microsoft.
    -   Giấy phép khai báo trong manifest: MIT License; chủ thể quyền:
        Microsoft Corporation.
    -   Số đơn vị tài liệu trong manifest: 39.
    -   Corpus gồm các tài liệu độc lập; 30 tài liệu có ít nhất 1.500 ký
        tự sau chuẩn hóa, 9 tài liệu còn lại ngắn hơn nhưng là các tài
        liệu riêng biệt, không phải bản sao được tạo thêm để tăng số
        lượng.
    -   Với Markdown, chương trình coi toàn bộ file là một đơn vị tài
        liệu logic (`page=1`, `location_type=markdown_file`,
        `page_type=logical_document`), không xem đó là trang PDF vật lý.
    -   Manifest lưu thông tin nguồn, giấy phép, đường dẫn và SHA256. Đã
        kiểm tra các file nguồn tồn tại, không rỗng và hash khớp với nội
        dung nguồn.
    -   **Giới hạn cần lưu ý:** cần trình bày rõ trong buổi chấm cách
        xác định 39 đơn vị là các đơn vị nguồn độc lập có ý nghĩa; không
        gọi chúng là 39 trang PDF.
-   **Chuẩn hóa, lỗi và giới hạn:**
    -   Chuẩn hóa Unicode theo NFC.
    -   Loại bỏ BOM, chuẩn hóa CRLF, thay thế NBSP, loại bỏ khoảng trắng
        cuối dòng, gộp chuỗi dòng trống dài hơn hai dòng và loại bỏ
        khoảng trắng ở đầu/cuối nội dung.
    -   Giữ liên kết về `document_id`, nguồn và vị trí logic của tài
        liệu.
    -   Offset chunk được tính trên nội dung trang sau chuẩn hóa.
    -   Markdown được biểu diễn thành một đơn vị tài liệu logic.
    -   Đã kiểm tra 39 tài liệu trong manifest; tất cả file nguồn tồn
        tại và không rỗng.
    -   Đã kiểm tra 20 đoạn gold evidence; cả 20 đoạn đều tìm thấy chính
        xác trong nội dung nguồn đã chuẩn hóa và có normalized offsets
        hợp lệ.
    -   Giới hạn: cách biểu diễn Markdown thành một đơn vị logic không
        tương đương phân trang vật lý; corpus có một số tài liệu ngắn
        hơn 1.500 ký tự.
-   **Embedding model/provider/version/số chiều, vector store/version,
    metric, lệnh chạy và chi phí:**
    -   Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
    -   Provider/thư viện: Sentence Transformers, chạy local.
    -   Số chiều vector: 384.
    -   Vector store: PostgreSQL + pgvector.
    -   Metric truy xuất: cosine distance.
    -   Metadata lưu trong JSONB; có GIN index hỗ trợ truy vấn metadata.
    -   Cấu hình kết nối benchmark dùng PostgreSQL tại
        `127.0.0.1:55433`, database `day6_lab`.
    -   Lệnh khởi chạy database: `docker compose up -d` (chạy từ thư mục
        có `docker-compose.yml`).
    -   Lệnh ingestion: `python .\ingest_corpus.py`.
    -   Lệnh benchmark: `python .\benchmark_runner.py`.
    -   Chi phí API embedding: 0; model chạy local. Chưa tính điện
        năng/phần cứng và chi phí máy.
    -   Phiên bản PostgreSQL, pgvector và phiên bản package cụ thể: **bổ
        sung từ cấu hình Docker/requirements trước khi nộp**; không tự
        suy đoán phiên bản.
-   **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do
    chọn:**
    -   Metadata truy vết tối thiểu: `document_id`, `source` và
        `page`/vị trí logic tương đương.
    -   Trường bổ sung trong corpus: `topic`, `lesson`, `license`,
        `document_type`, `location_type` (ngoài các trường metadata khác
        được lưu theo tài liệu).
    -   Các giá trị được lấy từ manifest và metadata của tài liệu, không
        tự suy đoán.
    -   `topic` và `lesson` hỗ trợ giới hạn phạm vi nội dung;
        `document_type` và `location_type` phân biệt loại/vị trí tài
        liệu; `license` hỗ trợ kiểm tra quyền sử dụng; `source` và
        `page` hỗ trợ truy vết.
    -   Các trường được phép filter trong store: `topic`, `lesson`,
        `license`, `document_type`, `source`, `location_type`.

## Cấu hình và benchmark

-   **A / B / C (tham số cụ thể, khác biệt duy nhất B--C):**

      -----------------------------------------------------------------------
      Cấu hình          Chunking          Tham số           Metadata filter
      ----------------- ----------------- ----------------- -----------------
      A                 Fixed-size        500 ký tự,        Không
                                          overlap 50        

      B                 By-paragraph      Kích thước tối đa Không
                                          1.000 ký tự       

      C                 By-paragraph      Kích thước tối đa Có filter khi câu
                                          1.000 ký tự       hỏi cung cấp điều
                                                            kiện
      -----------------------------------------------------------------------

    Cả ba cấu hình dùng cùng corpus, embedding model, vector store và
    cosine distance. B và C chỉ khác nhau ở việc áp dụng metadata
    filter; A và B khác nhau ở chiến lược chunking.

-   **Bộ câu hỏi và cách kiểm chứng evidence:**

    -   Tổng số: 20 câu hỏi; 15 dev và 5 test.
    -   Có câu hỏi kiểm tra metadata filter; cả 5 câu test đều có filter
        metadata.
    -   Các filter test lần lượt gồm: Q16 `topic=2-Regression`, Q17
        `topic=4-Classification`, Q18 `topic=6-NLP`, Q19
        `topic=7-TimeSeries`, Q20 `topic=8-Reinforcement`.
    -   Gold evidence được kiểm tra trực tiếp với nội dung nguồn sau
        chuẩn hóa. 20/20 evidence quote tìm thấy trong nguồn tương ứng;
        normalized offsets hợp lệ 20/20.
    -   Cấu hình C chỉ áp dụng filter khi câu hỏi có filter; không đưa
        gold source hoặc đáp án vào query/filter.
    -   Chạy top-3 cho mỗi câu hỏi trên cả ba cấu hình, tổng cộng 60
        lượt truy xuất.

-   **Tiêu chí chọn chiến lược đã chốt trước khi xem test:**

    -   Tiêu chí đánh giá theo yêu cầu bài: ưu tiên retrieval accuracy
        (Hit@1 và Evidence Hit@3), sau đó xem xét grounding, chunk
        coherence, metadata usefulness và tài nguyên.
    -   **Hạn chế về ghi nhận:** hiện chưa có artifact độc lập ghi lại
        thời điểm chốt tiêu chí trước khi xem test. Vì vậy, báo cáo
        không khẳng định có bằng chứng về việc đăng ký trước tiêu chí;
        kết quả test được dùng để mô tả và phân tích, không dùng để
        tuyên bố một chiến lược thắng tổng quát.

## Kết quả

### 1. Retrieval accuracy và tài nguyên

`Hit@1` trong benchmark hiện tại là chỉ số document-level (chunk top-1
thuộc tài liệu gold), không phải kiểm tra chunk top-1 chứa toàn bộ
evidence. `Full Evidence Hit@3` là chỉ số chính cho việc một chunk trong
top-3 chứa toàn bộ đoạn gold evidence. `Overlap Evidence Hit@3` chỉ là
chỉ số bổ sung, đo việc chunk có giao với đoạn evidence.

  --------------------------------------------------------------------------------
  Strategy   Split       Hit@1       Full    Overlap     Chunk Thời gian   Chi phí
                         (n/N)   Evidence   Evidence     count truy xuất       API
                                    Hit@3      Hit@3                  TB 
                                    (n/N)      (n/N)                     
  ---------- ------- --------- ---------- ---------- --------- --------- ---------
  A          Dev         14/15       4/15      12/15     1.004  29,91 ms         0
                       (93,3%)    (26,7%)    (80,0%)                     

  A          Test          4/5   0/5 (0%) 5/5 (100%)     1.004  28,90 ms         0
                       (80,0%)                                           

  B          Dev         14/15      10/15      11/15       554  29,82 ms         0
                       (93,3%)    (66,7%)    (73,3%)                     

  B          Test          2/5        1/5        1/5       554  25,79 ms         0
                       (40,0%)    (20,0%)    (20,0%)                     

  C          Dev         14/15      10/15      11/15       554  24,43 ms         0
                       (93,3%)    (66,7%)    (73,3%)                     

  C          Test          2/5        1/5        1/5       554  18,84 ms         0
                       (40,0%)    (20,0%)    (20,0%)                     
  --------------------------------------------------------------------------------

Tổng số chunk đã nạp: - Fixed-size: 1.004 chunks trên 39 tài liệu. -
By-paragraph: 554 chunks trên 39 tài liệu. - Tổng hai chiến lược: 1.558
chunks. - Kiểm tra database: không có chunk thiếu start/end offset và
không có offset không hợp lệ.

### 2. Audit thủ công và metadata

  --------------------------------------------------------------------------
  Strategy       Coherence      Metadata đủ và Filter tuân    Grounding
                 trung bình /2  đúng (n/N)     thủ            0/1/2 (số câu)
                 (n=10)                                       và trung bình
                                                              /2
  -------------- -------------- -------------- -------------- --------------
  A              Chưa chấm      Chưa tổng hợp  N/A (không     Chưa chấm đủ 5
                                thành tỷ lệ    filter)        câu

  B              Chưa chấm      Chưa tổng hợp  N/A (không     Chưa chấm đủ 5
                                thành tỷ lệ    filter)        câu

  C              Chưa chấm      Chưa tổng hợp  15/15 kết quả  Chưa chấm đủ 5
                                thành tỷ lệ    top-3 test     câu
                                               tuân thủ       
                                               filter         
  --------------------------------------------------------------------------

-   Đã kiểm tra thủ công nội dung top-3 của 5 câu test cho cả A/B/C để
    phân tích trường hợp đúng/sai.
-   Với C, cả 15/15 bản ghi top-3 trên Q16--Q20 đều thỏa điều kiện topic
    filter tương ứng.
-   Chưa hoàn thành bảng chấm coherence theo 10 vị trí nguồn dùng chung
    cho từng chiến lược.
-   Chưa hoàn thành nhãn grounding 0/1/2 cho 5 câu test của từng chiến
    lược.
-   Chưa tổng hợp tỷ lệ metadata `source`, `page` và các trường cần
    thiết đúng/đủ trên toàn bộ 45 bản ghi test (5 câu × top-3 × 3 cấu
    hình). Không tự điền tỷ lệ khi chưa có bảng audit.

### 3. Đường dẫn trace, nhãn thủ công và cách chọn mẫu

-   Câu hỏi, split và gold evidence: `starter/benchmark/questions.json`.
-   Kết quả benchmark CSV: `starter/benchmark/results.csv`.
-   Trace chi tiết top-3: `starter/benchmark/results.json`.
-   Mã ingestion: `starter/src/ingestion.py`.
-   Mã chunking: `starter/src/chunking.py`.
-   Mã embedding: `starter/src/embeddings.py`.
-   Mã vector store: `starter/src/store.py`.
-   Mã benchmark: `starter/benchmark_runner.py`.
-   Số liệu audit filter: kiểm tra 5 câu test Q16--Q20, mỗi câu có 3 kết
    quả top-3 của cấu hình C.
-   Chọn mẫu coherence theo yêu cầu GUIDE: cần xác định trước 10 vị trí
    nguồn dùng chung cho A/B/C, sau đó chấm chunk bao phủ từng vị trí
    theo thang 0--2. Bảng nhãn này chưa được hoàn thành.
-   Grounding: cần chấm top-3 của từng cấu hình cho 5 câu test theo
    thang 0--2; bảng nhãn và lý do chưa được hoàn thành.

## Phân tích và kết luận

-   **So sánh A--B:**
    -   Trên dev, A và B cùng đạt Hit@1 14/15. Full Evidence Hit@3 của B
        là 10/15, cao hơn A là 4/15.
    -   Trên test, A đạt Hit@1 4/5, B đạt 2/5. Tuy nhiên, Full Evidence
        Hit@3 của A là 0/5 và B là 1/5.
    -   B giảm số chunk từ 1.004 xuống 554. Thời gian trung bình dev gần
        tương đương (29,82 ms so với 29,91 ms); trên test B là 25,79 ms
        so với 28,90 ms của A.
    -   Kết quả cho thấy chunking theo đoạn có lợi trên dev về Full
        Evidence Hit@3 và giảm số chunk, nhưng kết quả test nhỏ không
        cho phép kết luận B tốt hơn A trong mọi trường hợp.
-   **So sánh B--C:**
    -   B và C có cùng Hit@1 và Full Evidence Hit@3 trên cả dev và test.
    -   C có thời gian truy xuất trung bình thấp hơn trong lần chạy này:
        24,43 ms so với 29,82 ms trên dev; 18,84 ms so với 25,79 ms trên
        test.
    -   C tuân thủ filter ở 15/15 bản ghi top-3 trên năm câu test có
        filter.
    -   Kết quả hiện tại chưa cho thấy metadata filter làm tăng Full
        Evidence Hit@3 so với B; lợi ích quan sát được rõ nhất là khả
        năng giới hạn phạm vi theo metadata và thời gian truy xuất trong
        lần chạy này.
-   **Hai ví dụ truy xuất chưa tốt:**
    1.  **Q19 --- TimeSeries:** cấu hình A tìm được đoạn giải thích phù
        hợp trong tài liệu, quanh offset 4.950--5.450. B và C truy xuất
        đúng chủ đề nhưng evidence không xuất hiện đầy đủ trong top-3.
        Đây là ví dụ cho thấy chunking theo đoạn không phải lúc nào cũng
        đưa evidence cần thiết lên thứ hạng cao.
    2.  **Q20 --- Reinforcement Learning:** evidence gold dài khoảng 689
        ký tự, vượt kích thước chunk cố định 500 ký tự. A tìm được chunk
        đầu liên quan đến agent, states và actions nhưng không chứa toàn
        bộ evidence. B và C xếp các chunk kém liên quan hơn ở thứ hạng
        cao. Đây là trường hợp evidence dài có thể cần chiến lược ghép
        nhiều chunk hoặc chunk size lớn hơn.
-   **Chiến lược chọn, đánh đổi, điều kiện áp dụng:**
    -   Không tuyên bố một cấu hình thắng tuyệt đối.
    -   Nếu ưu tiên Hit@1 trên tập test hiện tại, A có kết quả cao hơn.
    -   Nếu ưu tiên Full Evidence Hit@3 trên dev và giảm số lượng chunk,
        B/C có kết quả tốt hơn A.
    -   Nếu yêu cầu lọc phạm vi theo metadata, C là cấu hình đáp ứng yêu
        cầu đó; audit test cho thấy filter được tuân thủ 15/15.
    -   Lựa chọn phù hợp phụ thuộc mục tiêu: tìm đúng tài liệu, lấy đủ
        evidence, giảm số chunk hay giới hạn phạm vi bằng metadata.
-   **Hạn chế của dữ liệu, nhãn, test nhỏ, đo thời gian/chi phí:**
    -   Corpus gồm 39 tài liệu thuộc một chủ đề; 9 tài liệu ngắn hơn
        1.500 ký tự.
    -   Test chỉ có 5 câu nên tỷ lệ phần trăm thay đổi mạnh khi một câu
        đúng hoặc sai.
    -   Hit@1 hiện là document-level, không chứng minh chunk top-1 chứa
        đủ evidence.
    -   Full Evidence Hit@3 không ghi nhận đầy đủ trường hợp evidence bị
        chia qua nhiều chunk.
    -   Chưa hoàn thành chấm coherence, grounding và tỷ lệ metadata
        đủ/đúng bằng nhãn thủ công.
    -   Thời gian truy xuất là số đo trong một lần chạy, có thể chịu ảnh
        hưởng của cache, tải máy và trạng thái database; không nên xem
        là benchmark hiệu năng ổn định.
    -   Chi phí API bằng 0 do chạy local, chưa tính chi phí phần
        cứng/điện năng.
-   **Nếu làm lại hoặc mở rộng, cải tiến gì?**
    -   Tăng số lượng câu hỏi test và đa dạng cách diễn đạt, điều kiện
        và ngoại lệ.
    -   Hoàn thiện audit coherence, metadata và grounding với cùng mẫu
        và tiêu chí cho A/B/C.
    -   Thử nghiệm chunking theo heading hoặc kết hợp heading với
        paragraph.
    -   Thử nghiệm chunk size lớn hơn hoặc retrieval đa chunk cho
        evidence dài.
    -   Đánh giá thêm khả năng ghép evidence từ nhiều chunk nhưng vẫn
        giữ nguyên chỉ số Full Evidence Hit@3 chính thức.
    -   Chạy benchmark nhiều lần và báo cáo trung bình/độ dao động thời
        gian.
    -   Ghi rõ phiên bản PostgreSQL, pgvector, Python packages và thời
        điểm chạy để tăng khả năng tái lập.

