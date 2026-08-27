# BÁO CÁO KỸ THUẬT & KẾT QUẢ THỰC HIỆN LAB 25
## Tối ưu hóa Chi phí GPU (GPU FinOps Optimization Workshop)

**Họ và tên sinh viên:** Nguyễn Gia Thiệu  
**Mã sinh viên / ID:** 2A202601759  
**Khóa học:** AICB · Phase 2 · Track 2 (Infrastructure) · Day 25  
**Ngày thực hiện:** 27/08/2026  

---

## 1. TỔNG QUAN KẾT QUẢ (BASELINE VS. OPTIMIZED)

Sau khi hoàn thành kiểm toán và áp dụng chuỗi đòn bẩy FinOps cho hệ thống *NimbusAI*, chi phí đơn vị (`$/1M-token`) và chi phí tổng thể hàng tháng đã giảm đáng kể:

| Số liệu (Metric) | Chi phí Gốc (Baseline) | Chi phí Tối ưu (Optimized) | Tỷ lệ Tiết kiệm (% Savings) |
|---|---|---|---|
| **Đơn giá Token (`$/1M-token`)** | **$6.488 / 1M token** | **$1.126 / 1M token** | **82.6%** |
| **Chi phí Inference / Ngày** | $48.87 / ngày | $8.48 / ngày | 82.6% |
| **Chi phí GPU Workloads / Tháng** | $25,667 / tháng | $15,627 / tháng | 39.1% |
| **Tổng Chi phí Hàng tháng** | **$27,133 / tháng** | **$14,626 / tháng** | **46.1%** |

> **Nhận xét chính:** Tổng chi phí GPU của NimbusAI giảm **46.1%** hàng tháng (tiết kiệm **$12,507/tháng** hay **$150,084/năm**). Đặc biệt, chỉ số hiệu quả cốt lõi `$/1M-token` phục vụ cho khách hàng đã giảm hơn **6 lần**.

---

## 2. PHÂN TÍCH CÁC ĐÒN BẨY TIẾT KIỆM CHI PHÍ (SAVINGS LEVERS BREAKDOWN)

Bảng phân tích đóng góp chi tiết của từng đòn bẩy FinOps trong mô hình tối ưu:

| Đòn bẩy (Lever) | Tiết kiệm (USD/tháng) | % Đóng góp vào tổng tiết kiệm | Cơ chế hoạt động & Tác động |
|---|---|---|---|
| **1. Strategic Purchasing (Spot & Reserved)** | **$10,040 / tháng** | **80.3%** | Chuyển đổi các training job có thể gián đoạn sang Spot Instance (+ Checkpointing) và các inference job 24/7 sang Reserved Instance 3 năm. |
| **2. Inference Optimization (Cascade, Cache, Batch)** | **$1,212 / tháng** | **9.7%** | Định tuyến (Cascade) 70% request đơn giản sang model nhỏ ($0.20/1M input), áp dụng Prompt Caching (giảm 90% input) và Batch API (giảm 50%). |
| **3. Right-sizing GPU (MBU/VRAM)** | **$655 / tháng** | **5.2%** | Chuyển đổi các workload bị nghẽn bộ nhớ (memory-bound) từ H100 sang A100/A10G với chi phí thuê giờ rẻ hơn. |
| **4. Eliminating Idle Waste (Kill Idle GPUs)** | **$600 / tháng** | **4.8%** | Tự động hạ ngắt các GPU không hoạt động (GPU util < 10% trong nhiều giờ liên tục). |

---

## 3. GIẢI MÃ PHÂN TÍCH "GPU-UTIL LIE" (M1 AUDIT)

### 3.1. Hiện tượng "GPU-Util Lie" là gì?
Trong quá trình kiểm toán telemetry (`gpu_telemetry.csv`), phát hiện các GPU có chỉ số `nvidia-smi GPU-Util %` rất cao nhưng hiệu năng thực tế (`MFU`) lại cực kỳ thấp:
* **Mã GPU bị cờ báo:** `gpu-h100-4` (GPU-Util: **98.2%**, MFU: **19.4%**, MBU: **20.7%**).
* **GPU thứ hai:** `gpu-a10g-1` (GPU-Util: **96.9%**, MFU: **26.8%**).

### 3.2. Nguyên nhân gốc rễ và cơ chế kỹ thuật
Chỉ số `GPU-Util` của `nvidia-smi` chỉ đo tỷ lệ thời gian *Xung nhịp GPU (GPU Clock)* hoạt động trong một khoảng thời gian, **KHÔNG đo lượng tính toán thực tế (FLOPs)**.
* `gpu-h100-4` hiển thị 98.2% Util nhưng MFU chỉ là 19.4% do GPU bị **Memory Stall (nghẽn băng thông HBM)** và **I/O Wait (chờ nạp dữ liệu từ CPU/Disk)**. Trong thời gian chờ này, lõi Tensor Core của H100 hoàn toàn bị bỏ trống (Idle FLOPs).
* **Tác động tài chính:** NimbusAI đang trả tiền trần $2.50/giờ cho H100 (tương đương $1,800/tháng), nhưng chỉ nhận được 1/5 sức mạnh tính toán của nó.

---

## 4. PHÂN TÍCH TÍNH BỀN VỮNG & NĂNG LƯỢNG (SUSTAINABILITY)

* **Tiêu thụ năng lượng trung bình:** `0.24 Wh` / query chuẩn.
* **Phát thải Carbon trung bình:** `0.091 gCO2e` / query (vùng mặc định `us-east-1`).
* **Phân tích Vùng triển khai (Region Optimization):**
  * `europe-central2` (Ba Lan): Đạt **660 gCO2/kWh** (bẩn nhất do dùng điện than).
  * `us-east-1` (Virginia): Đạt **380 gCO2/kWh**.
  * `europe-north1` (Na Uy): Chỉ **30 gCO2/kWh** (sạch nhất, dùng 100% thủy điện/năng lượng tái tạo).
* **Khuyến nghị:** Dịch chuyển các job huấn luyện không thời gian thực sang hạ tầng tại **`europe-north1`** giúp giảm **92.1% lượng phát thải carbon** với chi phí điện năng chỉ $0.09/kWh.

---

## 5. BÁO CÁO CÁC PHẦN MỞ RỘNG ĐÃ THỰC HIỆN ("YOUR TURN" EXTENSIONS)

Đã triển khai thành công **4 phần mở rộng (Extensions 1, 2, 3, 4)** và bổ sung bộ unit test `tests/test_extensions.py` (tất cả 19 tests PASS).

### 🔹 Extension 1 — Cải thiện thuật toán `recommend_tier()`
* **Vị trí:** [finops/pricing.py](file:///c:/Users/Admin/Downloads/Track2-Day25-2A202601759-NguyenGiaThieu/finops/pricing.py#L63)
* **Nội dung:** Bổ sung tham số phân tích rủi ro bị thu hồi (`interruption_risk`) theo loại GPU. Ví dụ: H100/A100 spot có tỷ lệ gián đoạn thấp (<5%), trong khi T4/A10G spot có tỷ lệ gián đoạn cao (>15%). Với các GPU nguy cơ gián đoạn cao và chu kỳ chạy lớn (Duty Cycle ≥ 75%), thuật toán chuyển hướng khuyến nghị sang `reserved` thay vì `spot` để bảo đảm SLA.

### 🔹 Extension 2 — Right-sizing GPU dựa trên MBU & VRAM Cost
* **Vị trí:** [missions/m1_efficiency_audit.py](file:///c:/Users/Admin/Downloads/Track2-Day25-2A202601759-NguyenGiaThieu/missions/m1_efficiency_audit.py#L49)
* **Nội dung:** Với các GPU memory-bound có MBU < 50%, hệ thống tự động tính toán băng thông thực tế đạt được (`Achieved BW`) và đối chiếu với Catalog. 
* **Kết quả:** Đề xuất hạ tầng phù hợp hơn: Chuyển 6 GPU H100 chạy workload decode nhẹ sang A100 giúp tiết kiệm **$511.20/tháng mỗi GPU** ($3,067/tháng tổng cộng).

### 🔹 Extension 3 — Điểm hòa vốn Prompt Caching `cache_is_worth_it()`
* **Vị trí:** [finops/pricing.py](file:///c:/Users/Admin/Downloads/Track2-Day25-2A202601759-NguyenGiaThieu/finops/pricing.py#L79)
* **Công thức hòa vốn:** `avg_cache_reads * (1 - read_discount) > write_cost_ratio`.
* **Phân tích:** Khi mức chiết khấu đọc cache là 90% (0.1x) và chi phí ghi cache bằng 1.0x chi phí đọc thông thường, điểm hòa vốn là **> 1.11 lần đọc**. Dataset của NimbusAI đạt trung bình **2.5 lần đọc** mỗi prefix cache $\rightarrow$ Prompt Caching hoàn toàn có lợi về mặt chi phí (`True`).

### 🔹 Extension 4 — Quản lý ngân sách Reasoning Models (Reasoning Budget)
* **Vị trí:** [missions/m2_inference_levers.py](file:///c:/Users/Admin/Downloads/Track2-Day25-2A202601759-NguyenGiaThieu/missions/m2_inference_levers.py#L17)
* **Phân tích:** 
  * Số lượng request Reasoning (`is_reasoning=1`): **201 / 2,400 requests (chỉ chiếm 8.4% traffic)**.
  * Chi phí tài chính: **$1.40 / ngày (chiếm 16.5% tổng chi phí inference)**.
  * Năng lượng tiêu thụ: **29.79 kWh / ngày (chiếm tới 94.0% tổng năng lượng tiêu thụ inference)**.
* **Insight & Đề xuất:** Reasoning Model tiêu tốn năng lượng gấp **80 lần** request thông thường. Cần thiết lập chính sách chỉ cho phép kích hoạt Reasoning Tokens khi điểm tự tin (confidence score) của Model nhỏ < threshold 0.7.

---

## 6. BA KHUYẾN NGHỊ HÀNH ĐỘNG HÀNG ĐẦU CHO BAN LÃNH ĐẠO NIMBUSAI

1. **Triển khai Auto-Purchasing Policy (Tiết kiệm $10,040/tháng):** Lập tức ký hợp đồng Reserved Instance 3 năm cho 3 cluster inference 24/7 (`job-infer-chat`, `job-infer-rag`, `job-infer-search`) và chuyển 100% job training/batch sang Spot Instance có checkpointing.
2. **Áp dụng Model Cascade & Prompt Caching Gateway (Tiết kiệm $1,212/tháng):** Cấu hình LiteLLM Proxy tự động phân tuyến 70% request RAG/Search đơn giản sang model `small`, đồng thời bật Cache cho các prompt hệ thống trùng lặp.
3. **Right-size H100 Cluster & Kiểm soát Reasoning Budget:** Hạ cấp các instance H100 đang bị nghẽn Memory Stall sang A100, đồng thời siết chặt quota sử dụng Reasoning model chỉ cho các bài toán logic phức tạp.

---

## 7. KẾT QUẢ KIỂM TRA TỰ ĐỘNG & UNIT TESTS

```bash
$ python verify.py
============================================================
  LAB 25 VERIFY
============================================================
  [PASS] M1 flags the GPU-Util lie (gpu-h100-4)
  [PASS] M1 detects idle waste
  [PASS] M2 $/1M-token drops after optimization
  [PASS] M2 inference savings in 60-95% band
  [PASS] M3 recommends a spot tier
  [PASS] M3 recommends a reserved tier
  [PASS] M3 purchasing saves money
  [PASS] M4 tag coverage 85-100%
  [PASS] M4 chargeback gate is open
  [PASS] M5 total savings in 40-95% band
  [PASS] M5 report.md written
------------------------------------------------------------
  11/11 checks passed
============================================================

$ pytest -q
...................                                                      [100%]
19 passed in 0.50s
```
