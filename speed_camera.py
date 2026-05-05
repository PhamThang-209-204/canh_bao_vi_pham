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

    # ---------- Tốc độ ----------
    SPEED_LIMIT = 50.0
    METERS_PER_PIXEL = 0.000265         # Lấy từ calibrate.py
    SPEED_BUFFER_SIZE = 10             # Số mẫu để smoothing tốc độ

    # Chỉ ghi vi phạm khi xe đã đủ N mẫu trong buffer (đảm bảo tốc độ đã ổn định)
    MIN_SAMPLES_FOR_VIOLATION = 8

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

    def __init__(self, fps, meters_per_pixel, buffer_size=10, time_based=False):
        self.fps = fps
        self.mpp = meters_per_pixel
        self.buffer_size = buffer_size
        self.time_based = time_based

        # history[id] = deque[(frame_or_time, cx, cy)]
        self.history = defaultdict(lambda: deque(maxlen=buffer_size))
        self.speeds = {}
        self.violated_ids = set()

    def update(self, track_id, cx, cy, timestamp_or_frame):
        """
        timestamp_or_frame:
        - Nếu time_based=True: thời gian thực (giây, từ time.time())
        - Nếu time_based=False: số thứ tự frame (int)
        """
        self.history[track_id].append((timestamp_or_frame, cx, cy))

        if len(self.history[track_id]) < 2:
            self.speeds[track_id] = 0.0
            return 0.0

        first_t, fx, fy = self.history[track_id][0]
        last_t, lx, ly = self.history[track_id][-1]

        # Quãng đường thực tế (mét)
        pixel_distance = np.sqrt((lx - fx) ** 2 + (ly - fy) ** 2)
        meters = pixel_distance * self.mpp

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

    def is_in_roi(self, cx, cy, roi):
        if roi is None:
            return True
        x1, y1, x2, y2 = roi
        return x1 <= cx <= x2 and y1 <= cy <= y2


# ===================== LỚP GHI NHẬN VI PHẠM =====================
class ViolationLogger:
    def __init__(self, output_dir, log_file):
        self.output_dir = output_dir
        self.log_file = log_file
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.exists(log_file):
            with open(log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Track_ID", "Vehicle_Type",
                    "Speed_kmh", "Speed_Limit", "Image_Path"
                ])

    def log_violation(self, frame, bbox, track_id, vehicle_type, speed, speed_limit):
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

        with open(self.log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                time_str, track_id, vehicle_type,
                f"{speed:.2f}", f"{speed_limit:.0f}", filepath
            ])

        print(f"[CẢNH BÁO] Xe ID={track_id} ({vehicle_type}) "
              f"vi phạm tốc độ: {speed:.1f} km/h. Đã lưu: {filepath}")


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
        fps, config.METERS_PER_PIXEL,
        config.SPEED_BUFFER_SIZE, time_based=live
    )
    logger = ViolationLogger(config.VIOLATIONS_DIR, config.VIOLATIONS_LOG)

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

        if config.ROI:
            x1, y1, x2, y2 = config.ROI
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(annotated, "ROI - Vung do toc do", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            class_ids = results[0].boxes.cls.int().cpu().numpy()

            for box, track_id, cls_id in zip(boxes, track_ids, class_ids):
                x1, y1, x2, y2 = map(int, box)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                if not tracker.is_in_roi(cx, cy, config.ROI):
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
                    pt1 = (history[i - 1][1], history[i - 1][2])
                    pt2 = (history[i][1], history[i][2])
                    cv2.line(annotated, pt1, pt2, color, 2)

                # Ghi vi phạm khi đủ điều kiện
                if (speed > config.SPEED_LIMIT
                        and int(track_id) not in tracker.violated_ids
                        and tracker.num_samples(int(track_id)) >= config.MIN_SAMPLES_FOR_VIOLATION):
                    tracker.violated_ids.add(int(track_id))
                    logger.log_violation(
                        frame, box, int(track_id),
                        vehicle_type, speed, config.SPEED_LIMIT
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


if __name__ == "__main__":
    config = Config()
    run_speed_camera(config)
