// Lấy giá trị từ localStorage khi trang được tải
window.onload = function() {
    const predictInput = document.getElementById('predict-input');
    const symptomInput = document.getElementById('symptom-input');

    if (localStorage.getItem('predictValue')) {
        predictInput.value = localStorage.getItem('predictValue');
    }

    if (localStorage.getItem('symptomValue')) {
        symptomInput.value = localStorage.getItem('symptomValue');
    }
};
function clearInput() {
    localStorage.removeItem('predictValue');
    localStorage.removeItem('symptomValue');
}
// Lưu giá trị khi người dùng nhập dữ liệu
function saveInput() {
    const predictInput = document.getElementById('predict-input').value;
    const symptomInput = document.getElementById('symptom-input').value;

    localStorage.setItem('predictValue', predictInput);
    localStorage.setItem('symptomValue', symptomInput);
}

function addToCart(id, name, medicineUnit_id){
    event.preventDefault()

    fetch('/api/add_medicine', {
        method: 'put',
        body: JSON.stringify({
            'id': id,
            'name': name,
            'medicineUnit_id': medicineUnit_id
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(function(res){
        console.info(res)
        return res.json()
    }).then(function(data){
        console.info(data)
        location.reload();
    }).catch(function(err){
        console.error(err)
    })
}

function deleteCart(id) {
    if (confirm("Bạn chắn chắn xóa thuốc này khỏi đơn?") == true) {
        fetch('/api/delete_cart/' + id, {
            method: 'delete',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(function (res) {
            console.info(res);
            return res.json();
        }).then(function (data) {
            console.info(data);
            // Sau khi xóa thành công, làm mới trang
            location.reload();
        }).catch(function (err) {
            console.error(err);
        });
    }
}


/*thay đổi nội dung button*/
