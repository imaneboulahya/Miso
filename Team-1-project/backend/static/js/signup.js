document.querySelector('form').addEventListener('submit', function(e) {
    const inputs = document.querySelectorAll('.input-field');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('error');
            isValid = false;
        } else {
            input.classList.remove('error');
        }
    });
    
    if (!isValid) {
        e.preventDefault();
    }
});
document.getElementById('profile_pic').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            document.getElementById('profile-pic-preview').src = event.target.result;
        };
        reader.readAsDataURL(file);
    }
});