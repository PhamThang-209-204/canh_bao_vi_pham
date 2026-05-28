import argparse
from blockchain_utils import BlockchainManager, generate_image_hash

def verify_violation(violation_id, image_path):
    print(f"\n--- XÁC THỰC DỮ LIỆU VI PHẠM ---")
    print(f"ID Vi Phạm: {violation_id}")
    print(f"File ảnh: {image_path}")
    
    # 1. Tính hash từ file ảnh hiện tại
    print("\n1. Đang tính mã Hash của ảnh tại local...")
    local_hash = generate_image_hash(image_path)
    if not local_hash:
        print("✗ Không thể tính hash do lỗi file.")
        return
    print(f"   Mã Hash (Local): {local_hash}")
    
    # 2. Truy vấn dữ liệu từ Blockchain
    print("\n2. Đang truy vấn Blockchain để lấy dữ liệu gốc...")
    blockchain_manager = BlockchainManager()
    
    # Load contract đã được deploy trước đó
    if not blockchain_manager.load_contract():
        print("✗ Không tìm thấy Smart Contract. Bạn đã chạy hệ thống chính (speed_camera.py) lần nào chưa?")
        return
        
    onchain_data = blockchain_manager.get_violation(violation_id)
    if not onchain_data or onchain_data["vehicleId"] == 0:
        print(f"✗ Không tìm thấy dữ liệu vi phạm với ID: {violation_id} trên Blockchain.")
        return
        
    print(f"   Dữ liệu Blockchain trả về:")
    print(f"   - Vehicle ID: {onchain_data['vehicleId']}")
    print(f"   - Tốc độ: {onchain_data['speed']} km/h")
    print(f"   - Thời gian: {onchain_data['timestamp']}")
    print(f"   - Mã Hash (On-chain): {onchain_data['imageHash']}")
    
    # 3. So sánh Hash
    print("\n3. Kết quả xác thực:")
    if local_hash == onchain_data['imageHash']:
        print("   ✓ DỮ LIỆU NGUYÊN VẸN! Khớp 100%. Ảnh chưa bị chỉnh sửa.")
    else:
        print("   ✗ PHÁT HIỆN GIAN LẬN! Dữ liệu ảnh đã bị thay đổi hoặc không khớp với bản gốc trên Blockchain.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xác thực dữ liệu vi phạm từ Blockchain")
    parser.add_argument("--id", type=str, required=True, help="Mã ID vi phạm (ví dụ: 20260511_143000_123_45)")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn tới file ảnh cần kiểm tra")
    
    args = parser.parse_args()
    verify_violation(args.id, args.image)
