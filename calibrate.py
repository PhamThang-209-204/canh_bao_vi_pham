"""
Công cụ hiệu chuẩn camera - Đo tỉ lệ pixel sang mét thực tế
============================================================
Cách sử dụng:
1. Chạy script với 1 frame từ video bạn muốn xử lý
2. Click chuột vào 2 điểm có khoảng cách thực tế đã biết
   (ví dụ: 2 vạch kẻ đường cách nhau 10 mét)
3. Nhập khoảng cách thực tế vào console
4. Script sẽ tính ra giá trị METERS_PER_PIXEL để dùng trong Config
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
        if len(points) < 2:
            points.append((x, y))
            cv2.circle(display_img, (x, y), 6, (0, 0, 255), -1)
            cv2.putText(display_img, f"P{len(points)}: ({x},{y})",
                        (x + 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)
            if len(points) == 2:
                cv2.line(display_img, points[0], points[1], (0, 255, 0), 2)
                pixel_dist = np.sqrt(
                    (points[1][0] - points[0][0]) ** 2 +
                    (points[1][1] - points[0][1]) ** 2
                )
                mid = ((points[0][0] + points[1][0]) // 2,
                       (points[0][1] + points[1][1]) // 2)
                cv2.putText(display_img, f"{pixel_dist:.1f} pixels",
                            mid, cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 0), 2)
            cv2.imshow("Calibration - Click 2 points", display_img)


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

    print("\n=== HIỆU CHUẨN CAMERA ===")
    print("1. Click vào 2 điểm có khoảng cách thực tế đã biết")
    print("   (ví dụ: 2 vạch kẻ đường cách nhau X mét)")
    print("2. Nhấn 'r' để reset, 'q' để thoát")
    print("3. Sau khi chọn 2 điểm, nhấn ENTER và nhập khoảng cách thực\n")

    cv2.namedWindow("Calibration - Click 2 points")
    cv2.setMouseCallback("Calibration - Click 2 points", mouse_callback)
    cv2.imshow("Calibration - Click 2 points", display_img)

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            points.clear()
            display_img = original_img.copy()
            cv2.imshow("Calibration - Click 2 points", display_img)
        elif key == 13 and len(points) == 2:  # ENTER
            cv2.destroyAllWindows()
            pixel_dist = np.sqrt(
                (points[1][0] - points[0][0]) ** 2 +
                (points[1][1] - points[0][1]) ** 2
            )
            try:
                real_meters = float(input("Nhập khoảng cách thực tế (mét): "))
                mpp = real_meters / pixel_dist
                print("\n=== KẾT QUẢ HIỆU CHUẨN ===")
                print(f"Khoảng cách pixel: {pixel_dist:.2f} px")
                print(f"Khoảng cách thực: {real_meters} m")
                print(f"METERS_PER_PIXEL  = {mpp:.6f}")
                print(f"\n>> Gán giá trị này vào Config.METERS_PER_PIXEL trong speed_camera.py")
            except ValueError:
                print("Giá trị không hợp lệ.")
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
