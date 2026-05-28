import os
import csv
from flask import Flask, render_template, Response, request, jsonify
from werkzeug.utils import secure_filename
from speed_camera import Config, generate_frames

app = Flask(__name__)

# Cấu hình upload
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Trạng thái hiện tại của nguồn video
current_video_source = "input_video.mp4" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    config = Config()
    # Sử dụng nguồn video hiện tại được chọn
    return Response(generate_frames(current_video_source, config),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/set_source', methods=['POST'])
def set_source():
    global current_video_source
    data = request.json
    source = data.get('source')
    if source:
        current_video_source = source
        # Nếu là số (ví dụ '0'), chuyển sang int cho webcam
        if source.isdigit():
            current_video_source = int(source)
        return jsonify({"status": "success", "source": current_video_source})
    return jsonify({"status": "error", "message": "No source provided"}), 400

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global current_video_source
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        current_video_source = filepath
        return jsonify({"status": "success", "filename": filename, "filepath": filepath})

@app.route('/api/violations')
def get_violations():
    config = Config()
    violations = []
    if os.path.exists(config.VIOLATIONS_LOG):
        with open(config.VIOLATIONS_LOG, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Lấy 10 vi phạm mới nhất
            rows = list(reader)
            violations = rows[-10:][::-1] # Đảo ngược để mới nhất lên đầu
            
            # Cập nhật đường dẫn ảnh để web có thể truy cập
            for v in violations:
                # Flask phục vụ file tĩnh, chúng ta cần route để xem ảnh hoặc dùng static folder
                # Ở đây giả sử thư mục violations nằm cùng cấp, ta có thể route riêng
                v['Image_Path'] = f"/violation_image/{os.path.basename(v['Image_Path'])}"
                
    return jsonify(violations)

@app.route('/violation_image/<filename>')
def get_violation_image(filename):
    config = Config()
    from flask import send_from_directory
    return send_from_directory(config.VIOLATIONS_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
