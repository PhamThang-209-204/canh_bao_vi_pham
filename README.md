````md
<div align="center">

# 🚦 GIÁM SÁT TỐC ĐỘ VÀ CẢNH BÁO VI PHẠM

### Hệ Thống Giám Sát Tốc Độ Phương Tiện Tự Động Bằng Trí Tuệ Nhân Tạo

<img src="https://ttsinhvien.dainam.edu.vn/FileManager/Upload/images/logoTruongDHThuDo.png" alt="DaiNam University Logo" width="150"/>

<br>

**TRƯỜNG ĐẠI HỌC ĐẠI NAM**  
**Khoa Công nghệ thông tin - Chuyên ngành AI & IoT**

<br>

Sử dụng Computer Vision để phát hiện, theo dõi, ước tính tốc độ phương tiện giao thông và lưu trữ bằng chứng vi phạm trên nền tảng Blockchain.

🚀 Demo • ✨ Tính Năng • 📦 Cài Đặt • 📖 Tài Liệu • 🤝 Đóng Góp

</div>

---

# 📋 Mục Lục

- [🎯 Giới Thiệu](#-giới-thiệu)
- [✨ Tính Năng](#-tính-năng)
- [🛠️ Công Nghệ](#️-công-nghệ)
- [🏗️ Kiến Trúc Hệ Thống](#️-kiến-trúc-hệ-thống)
- [📦 Cài Đặt](#-cài-đặt)
- [🚀 Sử Dụng](#-sử-dụng)
- [📖 Tài Liệu Cốt Lõi](#-tài-liệu-cốt-lõi)
- [📸 Screenshots](#-screenshots)
- [🤝 Đóng Góp](#️-đóng-góp)
- [📄 License](#-license)

---

# 🎯 Giới Thiệu

## GIÁM SÁT TỐC ĐỘ VÀ CẢNH BÁO VI PHẠM

Là giải pháp công nghệ thông minh hỗ trợ giám sát giao thông tự động bằng Trí Tuệ Nhân Tạo.

Hệ thống sử dụng:

- 🤖 YOLOv8 để nhận diện phương tiện
- 🎥 OpenCV để xử lý video
- 🚗 ByteTrack để theo dõi phương tiện
- ⚡ Perspective Transform để tính tốc độ
- ⛓️ Blockchain để lưu trữ dữ liệu vi phạm
- 📲 Telegram Bot để cảnh báo tức thì

Hệ thống có khả năng:

- Phát hiện xe vi phạm tốc độ theo thời gian thực
- Tính toán vận tốc phương tiện chính xác
- Chụp ảnh bằng chứng
- Gửi cảnh báo Telegram
- Lưu dữ liệu minh bạch lên Blockchain

---

# 🌟 Điểm Nổi Bật

✅ **Độ Chính Xác Cao**  
Ước tính tốc độ bằng Homography và ByteTrack Tracking.

✅ **Realtime Detection**  
Xử lý video thời gian thực với Webcam hoặc IP Camera.

✅ **Blockchain Security**  
Hash ảnh vi phạm được lưu trên Smart Contract.

✅ **Telegram Alert**  
Thông báo ngay khi phát hiện xe vượt tốc độ.

✅ **Hỗ Trợ Nhiều Nguồn Video**  
Webcam, Video MP4, IP Camera.

---

# ✨ Tính Năng

## 🚗 1. Nhận Diện & Theo Dõi Phương Tiện

- Nhận diện:
  - Xe máy
  - Ô tô
  - Xe tải
  - Xe buýt

- Theo dõi ID từng phương tiện bằng ByteTrack.

---

## ⚡ 2. Đo Tốc Độ Tự Động

- Tính tốc độ theo km/h
- Hiển thị trạng thái:
  - 🟢 Bình thường
  - 🟠 Cảnh báo
  - 🔴 Vi phạm

---

## 🌐 3. Web Dashboard

- Hiển thị video realtime
- Danh sách xe vi phạm
- Upload video trực tiếp
- Hỗ trợ Webcam/IP Camera

---

## ⛓️ 4. Blockchain & Telegram

- Sinh mã Hash SHA256
- Lưu dữ liệu lên Blockchain
- Gửi cảnh báo Telegram
- Lưu ảnh vi phạm tự động

---

# 🛠️ Công Nghệ

| Công Nghệ | Phiên Bản | Mục Đích |
|-----------|-----------|----------|
| Python | 3.10+ | Ngôn ngữ chính |
| YOLOv8 | Latest | Object Detection |
| OpenCV | 4.8+ | Xử lý ảnh/video |
| Flask | 3.x | Web Framework |
| Web3.py | 6.x | Blockchain |
| Solidity | ^0.8.0 | Smart Contract |

---

# 🏗️ Kiến Trúc Hệ Thống

```text
┌───────────────────────────────────────────────┐
│                 VIDEO INPUT                   │
│ Webcam │ IP Camera │ Video File               │
└──────────────────────┬────────────────────────┘
                       │
┌──────────────────────▼────────────────────────┐
│                AI PROCESSING                  │
│ YOLOv8 → ByteTrack → Speed Estimate           │
└──────────────────────┬────────────────────────┘
                       │
┌──────────────────────▼────────────────────────┐
│              VIOLATION PROCESSING             │
│ Save Image │ Telegram │ Blockchain            │
└──────────────────────┬────────────────────────┘
                       │
┌──────────────────────▼────────────────────────┐
│                WEB DASHBOARD                  │
│ Live Stream │ Statistics │ Violation Table    │
└───────────────────────────────────────────────┘
````

---

# 📦 Cài Đặt

## ⚙️ Yêu Cầu Hệ Thống

* Python 3.10+
* Webcam hoặc IP Camera
* Telegram Bot Token
* Ganache (nếu dùng Blockchain)

---

## 🔽 Clone Repository

```bash
git clone https://github.com/PhamThang-209-204/canh_bao_vi_pham.git
cd canh_bao_vi_pham
```

---

## 🐍 Tạo Virtual Environment

### Windows

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### Linux/Mac

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 📥 Cài Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Cấu Hình Telegram

Tạo file `.env`

```env
TELEGRAM_TOKEN=your_token
CHAT_ID=your_chat_id
```

---

# 🚀 Sử Dụng

## 🎯 Hiệu Chuẩn Camera

```bash
python calibrate.py --video input_video.mp4 --frame 100
```

### Các bước:

1. Click 2 điểm trên video
2. Nhập khoảng cách thực tế
3. Hệ thống tính tỉ lệ Pixel → Mét

---

## ▶️ Chạy Hệ Thống

```bash
python app.py
```

Mở trình duyệt:

```text
http://127.0.0.1:5000
```

---

# 📖 Nguyên Lý Tính Tốc Độ

Hệ thống sử dụng:

* Perspective Transform
* Homography Matrix
* Object Tracking

Quy trình:

1. Chuyển đổi không gian 2D → Bird Eye View
2. Tính khoảng cách thực tế
3. Tính vận tốc:

```text
Speed = Distance / Time
```

4. Quy đổi sang km/h

---

# 📸 Screenshots

## 🌐 Web Dashboard

* Live Camera
* Vehicle Tracking
* Speed Detection
* Violation Table

## 📲 Telegram Alert

* Ảnh xe vi phạm
* Tốc độ
* Thời gian
* Vehicle ID

---

# 🤝 Đóng Góp

Contributions, issues và feature requests đều được chào đón!

## Các bước đóng góp:

```bash
1. Fork repository
2. Create branch
3. Commit changes
4. Push branch
5. Open Pull Request
```

---

# 📄 License

MIT License

---

# 👨‍💻 Tác Giả

## Phạm Thắng

* GitHub: https://github.com/PhamThang-209-204
* Trường Đại Học Đại Nam
* Chuyên ngành AI & IoT

---

# 🙏 Acknowledgments

* Ultralytics YOLOv8
* OpenCV
* Flask
* Web3.py
* Trường Đại Học Đại Nam

---

<div align="center">

## ⭐ Nếu project hữu ích hãy cho repository một Star ⭐

Made with ❤️ by Phạm Thắng

</div>
```
