var selectedDate = ''; // Đây là biến lưu trữ ngày khám được chọn

document.addEventListener("DOMContentLoaded", function() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('ngayKham').setAttribute('min', today);

});


function deletePatient(patientId) {
    const confirmation = confirm('Bạn có chắc chắn muốn xóa bệnh nhân này không?');

    if (confirmation) {
        fetch(`/patients/${patientId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ patientId: patientId })
        })
        .then(response => {
            location.reload(); // Load lại trang sau khi xóa thành công
        })
        .catch(error => console.error('There was an error!', error));
    }
}

function filterByDate() {
    var selectedDate = document.getElementById('ngayKham').value;
     if (!selectedDate) {
        alert("Vui lòng chọn ngày trước khi nhấn Lọc");
        return; // Dừng xử lý tiếp theo nếu ngày chưa được chọn
    }


    fetch(`/get_patients_by_date?ngayKham=${selectedDate}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Phản hồi từ mạng không hợp lệ');
            }
            return response.json();
        })
        .then(data => {
            console.log(data);
        })
        .catch(error => console.error('LỖI!', error));

    window.location.href = `/get_patients_by_date?ngayKham=${selectedDate}`;
}
