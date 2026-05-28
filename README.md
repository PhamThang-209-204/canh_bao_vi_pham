<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Logo_DAI_NAM.png/400px-Logo_DAI_NAM.png" alt="Đại học Đại Nam Logo" width="150"/>
  
  <h3>TRƯỜNG ĐẠI HỌC ĐẠI NAM</h3>
  <h4>KHOA CÔNG NGHỆ THÔNG TIN - CHUYÊN NGÀNH AI & IoT</h4>
  
  <br>

  # SpeedShield AI - Hệ Thống Giám Sát Tốc Độ Bằng Trí Tuệ Nhân Tạo
  
  <p>
    Dự án nghiên cứu và phát triển hệ thống phát hiện, theo dõi, ước tính tốc độ phương tiện giao thông và lưu trữ bằng chứng vi phạm trên nền tảng Blockchain.
  </p>
</div>

---

## 📖 Giới thiệu đề tài

**SpeedShield AI** là hệ thống tự động phát hiện, theo dõi và ước tính tốc độ phương tiện từ video/webcam/IP Camera sử dụng mạng nơ-ron tích chập **YOLOv8** và xử lý ảnh **OpenCV**. 

Khi phát hiện phương tiện vượt quá tốc độ cho phép, hệ thống sẽ tự động chụp ảnh bằng chứng, ghi nhận các thông tin vi phạm (ID xe, loại xe, tốc độ, thời gian) và băm dữ liệu (hashing) để lưu trữ lên **Blockchain (Smart Contract)** nhằm đảm bảo tính toàn vẹn và minh bạch của dữ liệu.

## ✨ Tính năng nổi bật

- 🚗 **Phát hiện phương tiện:** Hỗ trợ nhận diện 4 loại phương tiện phổ biến: xe hơi, xe máy, xe buýt, xe tải (YOLOv8 pretrained trên tập dữ liệu COCO).
- 🎯 **Theo dõi đa đối tượng:** Sử dụng thuật toán **ByteTrack** để duy trì định danh (track_id) cho từng xe trong suốt quá trình di chuyển.
- ⚡ **Ước tính tốc độ (Perspective Transform):** Tính toán tốc độ thực tế (km/h) dựa trên phép biến đổi phối cảnh và khoảng cách pixel qua các frame, đem lại độ chính xác cao.
- ⛓️ **Tích hợp Blockchain:** Đảm bảo tính bất biến của bằng chứng vi phạm. Mã băm (hash) của hình ảnh và dữ liệu được đẩy lên Smart Contract (Ethereum/Local Network).
- 🌐 **Web Dashboard:** Giao diện trực quan (Flask) cho phép người dùng giám sát luồng video trực tiếp, tải video lên hoặc dùng Webcam, đồng thời hiển thị danh sách xe vi phạm theo thời gian thực.
- 📱 **Cảnh báo Telegram:** Tự động gửi ảnh và thông báo vi phạm đến điện thoại qua Telegram Bot.

## 📂 Cấu trúc thư mục

```text
speed_camera/
├── app.py                # Server Flask chạy giao diện Web Dashboard
├── speed_camera.py       # Core xử lý AI (YOLO, Tracker, Tính tốc độ)
├── blockchain_utils.py   # Module tương tác với Smart Contract (Web3)
├── TrafficViolation.sol  # Smart Contract lưu trữ vi phạm
├── telegram_bot.py       # Module gửi cảnh báo qua Telegram
├── calibrate.py          # Script hiệu chuẩn camera (chuyển đổi Pixel -> Mét)
├── requirements.txt      # Danh sách thư viện cần thiết
├── templates/            # Giao diện HTML của Web Dashboard
├── static/               # CSS, JS cho giao diện Web
└── violations/           # Thư mục lưu ảnh vi phạm tự động
```

## 🚀 Hướng dẫn cài đặt & Chạy dự án

### 1. Cài đặt thư viện
```bash
pip install -r requirements.txt
```
*(Lần đầu chạy, hệ thống sẽ tự động tải file model `yolov8n.pt`)*

### 2. Hiệu chuẩn Camera (Quan trọng)
Để tính toán tốc độ chính xác, hệ thống cần biết tỉ lệ chuyển đổi từ điểm ảnh (pixel) sang mét thực tế.
```bash
python calibrate.py --video input_video.mp4 --frame 100
```
- Dùng chuột click vào 2 điểm có khoảng cách thực tế đã biết trên video.
- Nhập khoảng cách thực (mét) vào terminal. Hệ thống sẽ tính ra thông số cấu hình.

### 3. Khởi động hệ thống & Web Dashboard
```bash
python app.py
```
- Mở trình duyệt web và truy cập vào địa chỉ: **`http://127.0.0.1:5000`**
- Tại giao diện, bạn có thể:
  - Xem thống kê trực tiếp.
  - Chuyển đổi nguồn video (Tải lên file video mp4 hoặc Dùng Webcam).
  - Xem danh sách và hình ảnh vi phạm được cập nhật realtime.

## 🧠 Nguyên lý hoạt động

1. **Phát hiện & Theo dõi (Detection & Tracking):** Mạng YOLOv8 phát hiện các hộp giới hạn (bounding boxes) của phương tiện. ByteTrack gán ID duy nhất cho mỗi xe.
2. **Biến đổi không gian (Homography):** Dựa trên 4 điểm chuẩn (tạo thành một mặt phẳng hình chữ nhật trên mặt đường), OpenCV tính toán ma trận Perspective Transform.
3. **Tính toán tốc độ:** Tọa độ pixel của xe được nhân với ma trận để suy ra vị trí thực tế trên mặt đường (theo mét). Từ độ dời quãng đường và thời gian (số frame / FPS), hệ thống tính ra tốc độ `km/h`.
4. **Xử lý vi phạm:** Nếu tốc độ > Giới hạn, hệ thống crop ảnh, đóng dấu thời gian, mã hóa hash, đẩy hash lên Smart Contract và gửi tin nhắn Telegram.

## 👨‍💻 Sinh viên thực hiện
*Dự án thuộc Khoa Công nghệ thông tin - Trường Đại học Đại Nam.*
