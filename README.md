<div align="center">

# GIÁM SÁT TỐC ĐỘ VÀ CẢNH BÁO VI PHẠM

Hệ Thống Giám Sát Tốc Độ Phương Tiện Tự Động Bằng Trí Tuệ Nhân Tạo

<table>
<tr>
<td align="center" width="45%">
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Logo_DAI_NAM.png/400px-Logo_DAI_NAM.png" alt="Đại học Đại Nam Logo" width="150"/>
</td>
<td align="center" width="10%">
</td>
<td align="center" width="45%">
<img src="LogoAIoTLab.png" alt="AIoT Lab Logo" width="150"/>
</td>
</tr>
</table>

**TRƯỜNG ĐẠI HỌC ĐẠI NAM**  
**Khoa Công nghệ thông tin - Chuyên ngành AI & IoT**

Sử dụng Computer Vision để phát hiện, theo dõi, ước tính tốc độ phương tiện giao thông và lưu trữ bằng chứng vi phạm trên nền tảng Blockchain.

🚀 Demo • ✨ Tính Năng • 📦 Cài Đặt • 📖 Tài Liệu • 🤝 Đóng Góp

</div>

## 📋 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng](#-tính-năng)
- [Công Nghệ](#️-công-nghệ)
- [Kiến Trúc Hệ Thống](#️-kiến-trúc-hệ-thống)
- [Cài Đặt](#-cài-đặt)
- [Sử Dụng](#-sử-dụng)
- [Tài Liệu Cốt Lõi](#-tài-liệu-cốt-lõi)
- [Hệ Thống Cảnh Báo Vi Phạm Giao Thông](#-hệ-thống-cảnh-báo-vi-phạm-giao-thông)
- [Đóng Góp](#️-đóng-góp)
- [License](#-license)

## 🎯 Giới Thiệu
**GIÁM SÁT TỐC ĐỘ VÀ CẢNH BÁO VI PHẠM** là giải pháp công nghệ thông minh hỗ trợ giám sát giao thông tự động. Bằng cách kết hợp sức mạnh của **YOLOv8** và **OpenCV**, hệ thống có khả năng phân tích luồng video thời gian thực để đo lường tốc độ xe cộ. 

Không chỉ dừng lại ở AI, hệ thống còn tiên phong tích hợp **Blockchain** để lưu vết bằng chứng vi phạm một cách minh bạch, chống gian lận dữ liệu, đồng thời cung cấp Web Dashboard tiện lợi và cảnh báo trực tiếp qua **Telegram**.

🌟 **Điểm Đặc Biệt**

- ✅ **Chính Xác Cao** - Ước tính tốc độ qua thuật toán Homography (Perspective Transform) và tracking chính xác bằng ByteTrack.
- ✅ **Toàn Vẹn Dữ Liệu** - Mọi hình ảnh vi phạm đều được băm (hashing) và lưu trữ hash lên Smart Contract.
- ✅ **Thông Báo Tức Thì** - Cảnh báo qua Telegram ngay khi có xe vượt quá tốc độ giới hạn (kèm ảnh bằng chứng).
- ✅ **Linh Hoạt Nguồn Video** - Hỗ trợ Webcam, IP Camera, hoặc tải lên File Video bất kỳ.

## ✨ Tính Năng
🚗 **1. Nhận Diện & Theo Dõi Thông Minh**

- Nhận diện 4 loại phương tiện: Xe hơi, Xe máy, Xe buýt, Xe tải (YOLOv8).
- Duy trì ID liên tục cho từng phương tiện trên các khung hình (ByteTrack).

⚡ **2. Đo Tốc Độ Tự Động**

- Tính toán tốc độ km/h dựa trên khoảng cách di chuyển thực tế (đã được hiệu chuẩn).
- Phân biệt rõ ràng trạng thái: Bình thường (Xanh), Chú ý (Cam), Vi phạm (Đỏ).

🌐 **3. Web Dashboard Trực Quan**

- Giao diện giám sát trực tiếp trên trình duyệt.
- Tự động thống kê và hiển thị danh sách các xe vi phạm mới nhất (Realtime).
- Thay đổi nguồn phát (Webcam, File, IP Camera) chỉ bằng 1 cú click.

⛓️ **4. Lưu Trữ Blockchain & Telegram**

- Sinh mã Hash cho ảnh vi phạm.
- Ghi dữ liệu (ID Xe, Tốc độ, Hash ảnh, Thời gian) vào mạng lưới Blockchain.
- Gửi ảnh và thông báo tức thì đến điện thoại người quản lý qua Telegram.

## 🛠️ Công Nghệ
### Tech Stack
| Công Nghệ | Phiên Bản | Mục Đích |
|-----------|-----------|----------|
| [Python](https://python.org) | 3.10+ | Ngôn ngữ phát triển chính |
| [YOLOv8](https://github.com/ultralytics/ultralytics) | Latest | Model AI phát hiện vật thể |
| [OpenCV](https://opencv.org/) | 4.8.x | Xử lý ảnh, Perspective Transform |
| [Flask](https://flask.palletsprojects.com/) | 3.x | Web Backend Framework |
| [Web3.py](https://web3py.readthedocs.io/) | 6.x | Giao tiếp với Smart Contract (Blockchain) |
| [Solidity](https://soliditylang.org/) | ^0.8.0 | Viết Smart Contract |

## 🏗️ Kiến Trúc Hệ Thống

```text
┌─────────────────────────────────────────────────────────────┐
│                       NGUỒN VIDEO                           │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐         │
│  │  Webcam  │   OR  │IP Camera │   OR  │ File MP4 │         │
│  └────┬─────┘       └────┬─────┘       └────┬─────┘         │
└───────┼──────────────────┼──────────────────┼───────────────┘
        │                  │                  │
┌───────▼──────────────────▼──────────────────▼───────────────┐
│                    AI CORE (speed_camera.py)                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ YOLOv8 Object  │  │ ByteTrack      │  │ Perspective    │ │
│  │ Detection      ├──► ID Tracking    ├──► Transformation │ │
│  └────────────────┘  └────────────────┘  └───────┬────────┘ │
└──────────────────────────────────────────────────┼──────────┘
                                                   │
┌──────────────────────────▼───────────────────────▼──────────┐
│                    XỬ LÝ VI PHẠM                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ Ghi log CSV    │  │ Gửi Telegram   │  │ Đẩy lên        │ │
│  │ Lưu ảnh Local  │  │ Bot Alert      │  │ Blockchain     │ │
│  └────┬───────────┘  └────────────────┘  └────────────────┘ │
└───────┼─────────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│                    WEB DASHBOARD (app.py)                   │
│  ┌────────────────┐  ┌────────────────┐                     │
│  │ Video LiveFeed │  │ Cập nhật bảng  │                     │
│  │ (Flask Route)  │  │ vi phạm (API)  │                     │
│  └────────────────┘  └────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Cài Đặt
### Yêu Cầu Hệ Thống
- Python 3.10 trở lên
- Mạng Blockchain Local (như Ganache) nếu muốn test Smart Contract
- Telegram Bot Token

### Bước 1: Clone Repository
```bash
git clone https://github.com/PhamThang-209-204/canh_bao_vi_pham.git
cd canh_bao_vi_pham
```

### Bước 2: Tạo Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Bước 3: Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình Telegram & Blockchain (Tùy chọn)
- Mở file `telegram_bot.py` và điền `TOKEN`, `CHAT_ID` của bạn.
- Đảm bảo Smart Contract `TrafficViolation.sol` đã được deploy nếu sử dụng tính năng Blockchain.

## 🚀 Sử Dụng

### 1. Hiệu Chuẩn Camera (Calibrate)
Để tính tốc độ chính xác, hệ thống cần biết tỉ lệ Pixel -> Mét thực tế.
```bash
python calibrate.py --video input_video.mp4 --frame 100
```
- Dùng chuột click vào 2 điểm có khoảng cách thực tế đã biết trên video.
- Nhập khoảng cách thực (mét) vào terminal. Hệ thống sẽ in ra thông số để bạn cấu hình.

### 2. Chạy Web Dashboard
```bash
python app.py
```
- Mở trình duyệt truy cập: `http://127.0.0.1:5000`
- Tải lên video MP4 hoặc nhấp nút **Dùng Webcam** để bắt đầu giám sát.

## 📖 Tài Liệu Cốt Lõi
### Nguyên Lý Tính Tốc Độ (Perspective Transform)
Hệ thống không tính tốc độ mù quáng theo 2D pixel vì vật càng xa trông càng nhỏ (chuyển động chậm hơn). Thay vào đó:
1. Dùng ma trận **Homography** chiếu không gian 2D (màn hình) thành không gian phẳng (nhìn từ trên xuống) với đơn vị tính là **Mét**.
2. Tính khoảng cách giữa tâm xe ở frame A và frame B trên không gian phẳng này.
3. Chia cho thời gian chênh lệch (Delta T) để ra vận tốc (m/s) -> quy đổi ra km/h.

## 📸 Screenshots
*(Bạn có thể thêm hình ảnh giao diện Web hoặc tin nhắn Telegram vào đây)*

## 🤝 Đóng Góp
Contributions, issues và feature requests đều được chào đón!

1. Fork repository.
2. Tạo branch (`git checkout -b feature/AmazingFeature`).
3. Commit changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to branch (`git push origin feature/AmazingFeature`).
5. Mở Pull Request.

## 📄 License
MIT License - xem file `LICENSE` để biết chi tiết.

## 👨‍💻 Tác Giả
**Phạm Thắng**

- GitHub: [@PhamThang-209-204](https://github.com/PhamThang-209-204)
- Môn học: Trí Tuệ Nhân Tạo / Đồ Án Chuyên Ngành
- Trường Đại Học Đại Nam

🙏 **Acknowledgments**
- [Ultralytics](https://github.com/ultralytics/ultralytics) - YOLOv8 Object Detection.
- Khoa Công nghệ thông tin, Trường Đại học Đại Nam.
- Nguồn cảm hứng từ các hệ thống Giao thông thông minh (ITS).

⭐ **Nếu project này hữu ích, hãy cho một star nhé!** ⭐

Made with ❤️ by Phạm Thắng
