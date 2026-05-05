# Hệ Thống Camera Giám Sát Tốc Độ Phương Tiện

Hệ thống tự động phát hiện, theo dõi và ước tính tốc độ phương tiện từ video sử dụng **YOLOv8** và **OpenCV**. Khi phát hiện xe vượt quá tốc độ cho phép, hệ thống sẽ tự động chụp ảnh, vẽ thông tin vi phạm và ghi log.

## Tính năng chính

- Phát hiện 4 loại phương tiện: xe hơi, xe máy, xe buýt, xe tải (dùng YOLOv8 pretrained trên COCO)
- Theo dõi đối tượng qua các frame bằng **ByteTrack** (tích hợp sẵn trong Ultralytics)
- Ước tính tốc độ thực tế (km/h) dựa trên quãng đường pixel giữa các frame
- Tự động lưu ảnh vi phạm + ghi log CSV (timestamp, ID xe, loại xe, tốc độ)
- Vẽ trực quan: bounding box, đường di chuyển, tốc độ, trạng thái (xanh/cam/đỏ)
- Hỗ trợ vùng đo (ROI) để tính tốc độ chính xác hơn ở vị trí mong muốn
- Công cụ hiệu chuẩn camera đi kèm

## Cấu trúc thư mục

```
speed_camera/
├── speed_camera.py       # File chính - chạy hệ thống
├── calibrate.py          # Công cụ hiệu chuẩn camera
├── requirements.txt      # Thư viện cần cài
├── violations/           # Thư mục lưu ảnh vi phạm (tự tạo)
└── violations_log.csv    # File log vi phạm (tự tạo)
```

## Cài đặt

```bash
pip install -r requirements.txt
```

Lần đầu chạy, YOLO sẽ tự tải file `yolov8n.pt` (~6MB).

## Cách sử dụng

### Bước 1: Hiệu chuẩn camera (QUAN TRỌNG)

Để tốc độ ước tính chính xác, bạn cần biết **1 pixel ứng với bao nhiêu mét** trên thực tế.

```bash
python calibrate.py --video input_video.mp4 --frame 100
```

- Click chuột vào 2 điểm có khoảng cách thực tế đã biết (ví dụ: 2 vạch kẻ đường cách nhau 10m)
- Nhấn `Enter` rồi nhập khoảng cách thực
- Script sẽ in ra giá trị `METERS_PER_PIXEL`

### Bước 2: Cấu hình

Mở `speed_camera.py` và chỉnh class `Config`:

```python
class Config:
    VIDEO_SOURCE = "input_video.mp4"   # hoặc 0 để dùng webcam
    SPEED_LIMIT = 50.0                 # Giới hạn tốc độ (km/h)
    METERS_PER_PIXEL = 0.05            # Lấy từ bước hiệu chuẩn
    ROI = (100, 300, 1180, 600)        # Vùng đo (x1,y1,x2,y2), None = toàn frame
```

### Bước 3: Chạy

```bash
python speed_camera.py
```

Nhấn `q` để thoát giữa chừng.

## Kết quả

- `output_annotated.mp4` – Video có vẽ bounding box và tốc độ
- `violations/violation_<id>_<timestamp>.jpg` – Ảnh vi phạm
- `violations_log.csv` – Log vi phạm dạng bảng

## Nguyên lý ước tính tốc độ

1. YOLO phát hiện phương tiện ở mỗi frame, ByteTrack gán `track_id` cho từng xe.
2. Lưu lại tâm bounding box của mỗi xe qua N frame gần nhất (mặc định N=10).
3. Tính khoảng cách pixel giữa điểm đầu và cuối trong buffer.
4. Đổi sang mét: `m = pixel × METERS_PER_PIXEL`.
5. Tính thời gian: `t = (last_frame - first_frame) / FPS`.
6. Tốc độ: `speed_kmh = (m / t) × 3.6`.

## Lưu ý quan trọng

- **Hiệu chuẩn càng chính xác → tốc độ càng đúng.** Nên đo từ vạch kẻ đường thật.
- Camera nên đặt cố định, góc nhìn ổn định. Camera lắc sẽ làm sai số tăng cao.
- Với cảnh có phối cảnh (perspective) mạnh, nên chia ROI thành các vùng nhỏ và hiệu chuẩn riêng cho mỗi vùng – hoặc dùng homography để chuyển sang góc nhìn từ trên xuống (bird's-eye view).
- Đổi sang `yolov8s.pt` hoặc `yolov8m.pt` cho độ chính xác cao hơn (chậm hơn).

## Hướng phát triển

- Thêm gửi cảnh báo qua email/Telegram/SMS khi có vi phạm
- OCR biển số xe (dùng EasyOCR hoặc PaddleOCR) để xác định danh tính phương tiện
- Dùng homography để hiệu chuẩn theo perspective chính xác hơn
- Tạo dashboard web (Flask/FastAPI) để xem báo cáo vi phạm trực tuyến
# yolo
