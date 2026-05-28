document.addEventListener('DOMContentLoaded', () => {
    const videoStream = document.getElementById('video-stream');
    const ipCamInput = document.getElementById('ip-cam-url');
    const btnSetIpCam = document.getElementById('btn-set-ipcam');
    const btnSetWebcam = document.getElementById('btn-set-webcam');
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const violationsList = document.getElementById('violations-list');
    const statViolations = document.getElementById('stat-violations');

    let lastViolationCount = 0;

    // --- XỬ LÝ IP CAMERA ---
    btnSetIpCam.addEventListener('click', () => {
        const url = ipCamInput.value.trim();
        if (url) {
            fetch('/api/set_source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: url })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    reloadVideoStream();
                    alert('Đã kết nối IP Camera: ' + url);
                }
            });
        }
    });

    btnSetWebcam.addEventListener('click', () => {
        fetch('/api/set_source', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: '0' }) // '0' is usually the default webcam
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                reloadVideoStream();
                alert('Đã chuyển sang sử dụng Webcam!');
            }
        });
    });

    // --- XỬ LÝ UPLOAD FILE ---
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', handleFileUpload);

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#3b82f6';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        const file = e.dataTransfer.files[0];
        if (file) uploadFile(file);
    });

    function handleFileUpload(e) {
        const file = e.target.files[0];
        if (file) uploadFile(file);
    }

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        dropZone.innerHTML = '<i class="fas fa-spinner fa-spin"></i><p>Đang tải video...</p>';

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                reloadVideoStream();
                dropZone.innerHTML = '<i class="fas fa-check-circle" style="color:#22c55e"></i><p>Đã tải lên thành công!</p>';
                setTimeout(() => {
                    dropZone.innerHTML = '<i class="fas fa-cloud-upload-alt"></i><p>Kéo thả hoặc Click để chọn file</p>';
                }, 3000);
            } else {
                alert('Lỗi upload: ' + data.message);
            }
        });
    }

    function reloadVideoStream() {
        // Thay đổi src của img để Flask khởi động lại generator với nguồn mới
        // Thêm timestamp để tránh cache
        videoStream.src = '/video_feed?t=' + new Date().getTime();
    }

    // --- CẬP NHẬT DANH SÁCH VI PHẠM ---
    function updateViolations() {
        fetch('/api/violations')
            .then(res => res.json())
            .then(data => {
                // Cập nhật thống kê
                statViolations.innerText = data.length;
                
                // Nếu có vi phạm mới (số lượng thay đổi hoặc mới khởi động)
                // Ta render lại list
                renderViolations(data);
            });
    }

    function renderViolations(violations) {
        violationsList.innerHTML = '';
        violations.forEach(v => {
            const card = document.createElement('div');
            card.className = 'violation-card';
            card.innerHTML = `
                <div class="v-header">
                    <span class="v-time">${v.Timestamp}</span>
                    <span class="v-speed">${v.Speed_kmh} km/h</span>
                </div>
                <img src="${v.Image_Path}" class="v-img" alt="Violation">
                <div class="v-info">
                    <div><strong>ID Xe:</strong> ${v.Track_ID}</div>
                    <div><strong>Loại xe:</strong> ${v.Vehicle_Type}</div>
                </div>
                <div class="v-tx">
                    <i class="fas fa-link"></i> Tx: ${v.TxHash}
                </div>
            `;
            violationsList.appendChild(card);
        });
    }

    // Poll dữ liệu mỗi 3 giây
    setInterval(updateViolations, 3000);
    updateViolations(); // Chạy ngay lần đầu
});
