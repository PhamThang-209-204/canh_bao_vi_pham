"""
Hệ thống Camera Giám Sát Tốc Độ Phương Tiện - PHIÊN BẢN TỐI ƯU
================================================================
Cải tiến so với v1:
- Tự động phát hiện nguồn (file video / webcam / stream) để chọn cách tính FPS đúng
- Với video file: dùng frame_idx + FPS gốc → tốc độ KHÔNG phụ thuộc tốc độ xử lý
- Với webcam/stream: dùng timestamp thực tế → đúng kể cả khi máy chậm
- Hỗ trợ skip frame để tăng tốc xử lý mà vẫn giữ độ chính xác
- Hỗ trợ resize input để tăng FPS đáng kể
- Tách hiển thị khỏi xử lý: bật/tắt hiển thị không ảnh hưởng kết quả
"""

import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict, deque
from datetime import datetime
import os
import csv
import time
from telegram_bot import send_telegram_photo
from blockchain_utils import BlockchainManager, generate_image_hash



# ===================== CẤU HÌNH =====================
class Config:
    # ---------- Nguồn video ----------
    VIDEO_SOURCE = "input_video.mp4"   # File / 0 (webcam) / "rtsp://..."

    # ---------- Model YOLO ----------
    # Nếu chậm: dùng "yolov8n.pt" (nano, nhanh nhất)
    # Nếu cần chính xác hơn: "yolov8s.pt" hoặc "yolov8m.pt"
    MODEL_PATH = "yolov8n.pt"

    # ---------- TỐI ƯU TỐC ĐỘ XỬ LÝ ----------
    # Resize frame trước khi đưa vào YOLO. Giá trị nhỏ → nhanh hơn, ít chính xác hơn
    # 640 là chuẩn của YOLO. Có thể đặt 480 hoặc 416 để tăng tốc.
    YOLO_IMGSZ = 640

    # Bỏ qua frame để tăng tốc. 1 = xử lý mọi frame, 2 = mỗi 2 frame xử lý 1, ...
    # KHÔNG ảnh hưởng độ chính xác tốc độ vì code dùng frame_idx tuyệt đối
    PROCESS_EVERY_N_FRAMES = 1

    # Resize frame hiển thị (để cửa sổ nhỏ gọn). None = giữ nguyên
    DISPLAY_WIDTH = 1280

    # ---------- Phương tiện ----------
    VEHICLE_CLASSES = [2, 3, 5, 7]
    CLASS_NAMES = {2: "Car", 3: "Motorcycle", 5: "Bus", 7: "Truck"}

    # ---------- Tốc độ (Perspective Transform) ----------
    SPEED_LIMIT = 60.0
    
    # 4 điểm tạo thành hình chữ nhật trên mặt đường (Lấy từ kết quả chạy calibrate.py)
    # Thứ tự: Trái-Trên, Phải-Trên, Phải-Dưới, Trái-Dưới
    SRC_POINTS = [(489, 307), (782, 307), (893, 444), (395, 443)]
    REAL_WIDTH = 7.0    # Khoảng 2 làn đường (mỗi làn ~3.5m)
    REAL_LENGTH = 20.0  # Ước tính chiều dài đoạn đường trong ô màu xanh (mét)
    
    SPEED_BUFFER_SIZE = 10             # Số mẫu để smoothing tốc độ

    # Chỉ ghi vi phạm khi xe đã đủ N mẫu trong buffer (đảm bảo tốc độ đã ổn định)
    MIN_SAMPLES_FOR_VIOLATION = 8

    # ---------- Telegram Bot ----------
    TELEGRAM_BOT_TOKEN = "8384672776:AAHu12MkW_5nFCOntd7gABJdipoNOFUEqW0" # Nhập Token của bot (vd: "123456789:ABCdefGhI")
    TELEGRAM_CHAT_ID = "5990406025"   # Nhập Chat ID của bạn (vd: "987654321")

    # ---------- ROI ----------
    ROI = None  # (x1, y1, x2, y2) hoặc None

    # ---------- Output ----------
    VIOLATIONS_DIR = "violations"
    VIOLATIONS_LOG = "violations_log.csv"
    SHOW_DISPLAY = True
    SAVE_OUTPUT_VIDEO = True
    OUTPUT_VIDEO = "output_annotated.mp4"


# ===================== LỚP THEO DÕI TỐC ĐỘ =====================
class SpeedTracker:
    """
    Theo dõi vị trí và ước tính tốc độ.
    Hỗ trợ 2 chế độ:
    - frame-based: dùng frame_idx và FPS (dành cho video file)
    - time-based: dùng timestamp thực tế (dành cho webcam / stream)
    """

    def __init__(self, fps, config, time_based=False):
        self.fps = fps
        self.config = config
        self.buffer_size = config.SPEED_BUFFER_SIZE
        self.time_based = time_based

        # Thiết lập ma trận Perspective Transform (Homography)
        src = np.array(config.SRC_POINTS, dtype=np.float32)
        dst = np.array([
            [0, 0],
            [config.REAL_WIDTH, 0],
            [config.REAL_WIDTH, config.REAL_LENGTH],
            [0, config.REAL_LENGTH]
        ], dtype=np.float32)
        self.M = cv2.getPerspectiveTransform(src, dst)

        # history[id] = deque[(frame_or_time, meter_x, meter_y)]
        self.history = defaultdict(lambda: deque(maxlen=self.buffer_size))
        self.speeds = {}
        self.violated_ids = set()

    def update(self, track_id, cx, cy, timestamp_or_frame):
        """
        timestamp_or_frame:
        - Nếu time_based=True: thời gian thực (giây, từ time.time())
        - Nếu time_based=False: số thứ tự frame (int)
        """
        # Chuyển đổi tọa độ pixel (cx, cy) sang tọa độ mét thực tế
        point = np.array([[[cx, cy]]], dtype=np.float32)
        transformed_point = cv2.perspectiveTransform(point, self.M)
        meter_x, meter_y = transformed_point[0][0]

        self.history[track_id].append((timestamp_or_frame, meter_x, meter_y, cx, cy))

        if len(self.history[track_id]) < 2:
            self.speeds[track_id] = 0.0
            return 0.0

        first_t, fx, fy, _, _ = self.history[track_id][0]
        last_t, lx, ly, _, _ = self.history[track_id][-1]

        # Quãng đường thực tế (mét) đã được tính trên hệ tọa độ mét
        meters = np.sqrt((lx - fx) ** 2 + (ly - fy) ** 2)

        # Thời gian (giây)
        if self.time_based:
            seconds = last_t - first_t
        else:
            frames_elapsed = last_t - first_t
            seconds = frames_elapsed / self.fps

        if seconds <= 0:
            return self.speeds.get(track_id, 0.0)

        speed_kmh = (meters / seconds) * 3.6
        self.speeds[track_id] = speed_kmh
        return speed_kmh

    def num_samples(self, track_id):
        return len(self.history[track_id])

    def is_in_polygon(self, cx, cy, polygon):
        if not polygon:
            return True
        pts = np.array(polygon, np.int32).reshape((-1, 1, 2))
        return cv2.pointPolygonTest(pts, (cx, cy), False) >= 0


# ===================== LỚP GHI NHẬN VI PHẠM =====================
class ViolationLogger:
    def __init__(self, output_dir, log_file, blockchain_manager=None):
        self.output_dir = output_dir
        self.log_file = log_file
        self.blockchain_manager = blockchain_manager
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.exists(log_file):
            with open(log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Track_ID", "Vehicle_Type",
                    "Speed_kmh", "Speed_Limit", "Image_Path", "TxHash"
                ])

    def log_violation(self, frame, bbox, track_id, vehicle_type, speed, config):
        speed_limit = config.SPEED_LIMIT
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"violation_{track_id}_{timestamp}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        x1, y1, x2, y2 = map(int, bbox)
        annotated = frame.copy()
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)

        label = f"VI PHAM: {speed:.1f} km/h (Gioi han: {speed_limit:.0f})"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(annotated, (x1, y1 - th - 15), (x1 + tw + 10, y1), (0, 0, 255), -1)
        cv2.putText(annotated, label, (x1 + 5, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(annotated, time_str, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imwrite(filepath, annotated)

        # ===== XỬ LÝ BLOCKCHAIN =====
        tx_hash = "N/A"
        if self.blockchain_manager:
            image_hash = generate_image_hash(filepath)
            violation_id = f"{timestamp}_{track_id}"
            tx = self.blockchain_manager.add_violation(
                violation_id=violation_id,
                vehicle_id=track_id,
                speed=f"{speed:.2f}",
                timestamp=time_str,
                image_hash=image_hash
            )
            if tx:
                tx_hash = tx
        # ============================

        with open(self.log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                time_str, track_id, vehicle_type,
                f"{speed:.2f}", f"{speed_limit:.0f}", filepath, tx_hash
            ])

        print(f"[CẢNH BÁO] Xe ID={track_id} ({vehicle_type}) "
              f"vi phạm tốc độ: {speed:.1f} km/h. Đã lưu: {filepath}")
              
        # Gửi Telegram
        caption = f"🚨 CẢNH BÁO VI PHẠM TỐC ĐỘ 🚨\n" \
                  f"- Thời gian: {time_str}\n" \
                  f"- Loại xe: {vehicle_type}\n" \
                  f"- Tốc độ: {speed:.1f} km/h (Giới hạn: {speed_limit} km/h)"
        send_telegram_photo(filepath, caption)


# ===================== HÀM HỖ TRỢ =====================
def is_live_source(source):
    """Webcam (int) hoặc URL stream → live source, dùng time-based."""
    if isinstance(source, int):
        return True
    if isinstance(source, str) and (
        source.startswith("rtsp://") or
        source.startswith("http://") or
        source.startswith("https://")
    ):
        return True
    return False


# ===================== HÀM CHÍNH =====================
def run_speed_camera(config: Config):
    print("Đang tải model YOLO...")
    model = YOLO(config.MODEL_PATH)
    print(f"✓ Đã tải model: {config.MODEL_PATH}")

    cap = cv2.VideoCapture(config.VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"✗ Không mở được video: {config.VIDEO_SOURCE}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    live = is_live_source(config.VIDEO_SOURCE)
    mode = "TIME-BASED (live)" if live else "FRAME-BASED (file)"

    print(f"✓ Video: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames")
    print(f"✓ Chế độ tính tốc độ: {mode}")
    print(f"✓ Skip frame: 1/{config.PROCESS_EVERY_N_FRAMES}")
    print(f"✓ YOLO input size: {config.YOLO_IMGSZ}")

    tracker = SpeedTracker(
        fps, config, time_based=live
    )
    
    blockchain_manager = BlockchainManager()
    blockchain_manager.load_contract()
    
    logger = ViolationLogger(config.VIOLATIONS_DIR, config.VIOLATIONS_LOG, blockchain_manager=blockchain_manager)

    writer = None
    if config.SAVE_OUTPUT_VIDEO:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        # Output ghi với FPS tương ứng số frame thực sự được xử lý
        out_fps = fps / config.PROCESS_EVERY_N_FRAMES
        writer = cv2.VideoWriter(config.OUTPUT_VIDEO, fourcc, out_fps, (width, height))

    frame_idx = 0
    processed_count = 0
    start_time = time.time()
    print("\n>>> Bắt đầu xử lý. Nhấn 'q' để thoát.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Skip frame để tăng tốc
        if frame_idx % config.PROCESS_EVERY_N_FRAMES != 0:
            continue

        processed_count += 1

        # Xác định "thời điểm" cho frame này
        if live:
            current_time = time.time()
            time_or_frame = current_time
        else:
            time_or_frame = frame_idx

        # YOLO + ByteTrack
        results = model.track(
            frame,
            persist=True,
            classes=config.VEHICLE_CLASSES,
            tracker="bytetrack.yaml",
            imgsz=config.YOLO_IMGSZ,
            verbose=False
        )

        annotated = frame.copy()

        # Không hiện ô vùng nhận diện lên video nữa theo yêu cầu

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            class_ids = results[0].boxes.cls.int().cpu().numpy()

            for box, track_id, cls_id in zip(boxes, track_ids, class_ids):
                x1, y1, x2, y2 = map(int, box)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                if not tracker.is_in_polygon(cx, cy, config.SRC_POINTS):
                    continue

                vehicle_type = config.CLASS_NAMES.get(int(cls_id), "Unknown")
                speed = tracker.update(int(track_id), cx, cy, time_or_frame)

                # Màu theo trạng thái
                if speed > config.SPEED_LIMIT:
                    color, status = (0, 0, 255), "VI PHAM"
                elif speed > config.SPEED_LIMIT * 0.8:
                    color, status = (0, 165, 255), "CHU Y"
                else:
                    color, status = (0, 255, 0), "OK"

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"ID:{track_id} {vehicle_type} {speed:.1f}km/h"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                cv2.circle(annotated, (cx, cy), 4, color, -1)
                history = tracker.history[int(track_id)]
                for i in range(1, len(history)):
                    pt1 = (history[i - 1][3], history[i - 1][4])
                    pt2 = (history[i][3], history[i][4])
                    cv2.line(annotated, pt1, pt2, color, 2)

                # Ghi vi phạm khi đủ điều kiện
                if (speed > config.SPEED_LIMIT
                        and int(track_id) not in tracker.violated_ids
                        and tracker.num_samples(int(track_id)) >= config.MIN_SAMPLES_FOR_VIOLATION):
                    tracker.violated_ids.add(int(track_id))
                    logger.log_violation(
                        frame, box, int(track_id),
                        vehicle_type, speed, config
                    )

        # Banner thông tin
        info_bg = annotated.copy()
        cv2.rectangle(info_bg, (0, 0), (width, 40), (0, 0, 0), -1)
        annotated = cv2.addWeighted(info_bg, 0.6, annotated, 0.4, 0)

        elapsed = time.time() - start_time
        proc_fps = processed_count / elapsed if elapsed > 0 else 0
        info_text = (f"Frame: {frame_idx}/{total_frames} | "
                     f"FPS xu ly: {proc_fps:.1f} | "
                     f"Mode: {'LIVE' if live else 'FILE'} | "
                     f"Gioi han: {config.SPEED_LIMIT:.0f}km/h | "
                     f"Vi pham: {len(tracker.violated_ids)}")
        cv2.putText(annotated, info_text, (10, 27),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        if writer is not None:
            writer.write(annotated)

        if config.SHOW_DISPLAY:
            display_frame = annotated
            if config.DISPLAY_WIDTH and width > config.DISPLAY_WIDTH:
                ratio = config.DISPLAY_WIDTH / width
                new_h = int(height * ratio)
                display_frame = cv2.resize(annotated, (config.DISPLAY_WIDTH, new_h))

            cv2.imshow("Speed Camera - Press 'q' to quit", display_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()

    total_elapsed = time.time() - start_time
    avg_fps = processed_count / total_elapsed if total_elapsed > 0 else 0

    print(f"\n{'='*50}")
    print(f"HOÀN TẤT")
    print(f"{'='*50}")
    print(f"Thời gian xử lý: {total_elapsed:.1f}s")
    print(f"Số frame đã xử lý: {processed_count}")
    print(f"FPS xử lý trung bình: {avg_fps:.1f}")
    print(f"Số xe vi phạm: {len(tracker.violated_ids)}")
    print(f"Log: {config.VIOLATIONS_LOG}")
    print(f"Ảnh vi phạm: {config.VIOLATIONS_DIR}/")
    if config.SAVE_OUTPUT_VIDEO:
        print(f"Video kết quả: {config.OUTPUT_VIDEO}")


def generate_frames(video_source, config: Config):
    """Generator function để stream video cho Flask."""
    print(f"Đang khởi tạo luồng xử lý cho: {video_source}")
    model = YOLO(config.MODEL_PATH)
    cap = cv2.VideoCapture(video_source)
    
    if not cap.isOpened():
        print(f"✗ Không mở được nguồn video: {video_source}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    live = is_live_source(video_source)
    
    tracker = SpeedTracker(fps, config, time_based=live)
    blockchain_manager = BlockchainManager()
    blockchain_manager.load_contract()
    logger = ViolationLogger(config.VIOLATIONS_DIR, config.VIOLATIONS_LOG, blockchain_manager=blockchain_manager)

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        if frame_idx % config.PROCESS_EVERY_N_FRAMES != 0:
            continue

        time_or_frame = time.time() if live else frame_idx

        # YOLO + ByteTrack
        results = model.track(
            frame,
            persist=True,
            classes=config.VEHICLE_CLASSES,
            tracker="bytetrack.yaml",
            imgsz=config.YOLO_IMGSZ,
            verbose=False
        )

        annotated = frame.copy()

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            class_ids = results[0].boxes.cls.int().cpu().numpy()

            for box, track_id, cls_id in zip(boxes, track_ids, class_ids):
                x1, y1, x2, y2 = map(int, box)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                if not tracker.is_in_polygon(cx, cy, config.SRC_POINTS):
                    continue

                vehicle_type = config.CLASS_NAMES.get(int(cls_id), "Unknown")
                speed = tracker.update(int(track_id), cx, cy, time_or_frame)

                # Màu theo trạng thái
                if speed > config.SPEED_LIMIT:
                    color = (0, 0, 255)
                elif speed > config.SPEED_LIMIT * 0.8:
                    color = (0, 165, 255)
                else:
                    color = (0, 255, 0)

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"ID:{track_id} {vehicle_type} {speed:.1f}km/h"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                if (speed > config.SPEED_LIMIT
                        and int(track_id) not in tracker.violated_ids
                        and tracker.num_samples(int(track_id)) >= config.MIN_SAMPLES_FOR_VIOLATION):
                    tracker.violated_ids.add(int(track_id))
                    logger.log_violation(frame, box, int(track_id), vehicle_type, speed, config)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', annotated)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()


if __name__ == "__main__":
    config = Config()
    run_speed_camera(config)
