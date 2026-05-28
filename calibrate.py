"""
Công cụ hiệu chuẩn camera - Đo tỉ lệ pixel sang mét thực tế
============================================================
Cách sử dụng:
1. Chạy script với 1 frame từ video bạn muốn xử lý
2. Click chuột vào 4 điểm tạo thành HÌNH CHỮ NHẬT trên mặt đường
   (Thứ tự: Trái-Trên -> Phải-Trên -> Phải-Dưới -> Trái-Dưới)
3. Nhấn ENTER, sau đó nhập chiều rộng và chiều dài thực tế vào console
4. Copy các giá trị in ra màn hình vào class Config trong speed_camera.py
"""

import cv2
import numpy as np
import argparse


points = []
display_img = None
original_img = None


def mouse_callback(event, x, y, flags, param):
    global points, display_img
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append((x, y))
            cv2.circle(display_img, (x, y), 6, (0, 0, 255), -1)
            cv2.putText(display_img, f"P{len(points)}: ({x},{y})",
                        (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)
            if len(points) > 1:
                cv2.line(display_img, points[-2], points[-1], (0, 255, 0), 2)
            if len(points) == 4:
                cv2.line(display_img, points[3], points[0], (0, 255, 0), 2)
            cv2.imshow("Calibration - Click 4 points", display_img)


def main():
    global display_img, original_img

    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True,
                        help="Đường dẫn video cần hiệu chuẩn")
    parser.add_argument("--frame", type=int, default=0,
                        help="Số thứ tự frame muốn lấy (mặc định: 0)")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, args.frame)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"Không đọc được frame {args.frame} từ {args.video}")
        return

    original_img = frame.copy()
    display_img = frame.copy()

    print("\n=== HIỆU CHUẨN CAMERA (PERSPECTIVE) ===")
    print("1. Click vào 4 điểm tạo thành HÌNH CHỮ NHẬT trên mặt đường")
    print("   (Thứ tự: Trái-Trên -> Phải-Trên -> Phải-Dưới -> Trái-Dưới)")
    print("2. Nhấn 'r' để reset, 'q' để thoát")
    print("3. Sau khi chọn 4 điểm, nhấn ENTER và nhập kích thước thực\n")

    cv2.namedWindow("Calibration - Click 4 points")
    cv2.setMouseCallback("Calibration - Click 4 points", mouse_callback)
    cv2.imshow("Calibration - Click 4 points", display_img)

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            points.clear()
            display_img = original_img.copy()
            cv2.imshow("Calibration - Click 4 points", display_img)
        elif key == 13 and len(points) == 4:  # ENTER
            cv2.destroyAllWindows()
            try:
                real_width = float(input("Nhập chiều RỘNG thực tế (mét): "))
                real_length = float(input("Nhập chiều DÀI thực tế (mét): "))
                print("\n=== KẾT QUẢ HIỆU CHUẨN ===")
                print(f"SRC_POINTS = {points}")
                print(f"REAL_WIDTH = {real_width}")
                print(f"REAL_LENGTH = {real_length}")
                print("\n>> Copy các giá trị trên vào class Config trong speed_camera.py")
            except ValueError:
                print("Giá trị không hợp lệ.")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
