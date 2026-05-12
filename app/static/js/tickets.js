// Ticket form - multi step & upload
document.addEventListener('DOMContentLoaded', function() {
    // Upload area
    const area = document.getElementById('uploadArea');
    const input = document.getElementById('photoInput');
    const preview = document.getElementById('uploadPreview');
    const placeholder = document.getElementById('uploadPlaceholder');

    if (area && input) {
        area.addEventListener('click', () => input.click());
        area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('dragover'); });
        area.addEventListener('dragleave', () => area.classList.remove('dragover'));
        area.addEventListener('drop', e => {
            e.preventDefault(); area.classList.remove('dragover');
            input.files = e.dataTransfer.files;
            showPreviews();
        });
        input.addEventListener('change', showPreviews);
    }

    function showPreviews() {
        if (!preview || !input.files) return;
        preview.innerHTML = '';
        if (input.files.length > 0 && placeholder) placeholder.style.display = 'none';
        Array.from(input.files).slice(0, 5).forEach(file => {
            const reader = new FileReader();
            reader.onload = e => {
                const div = document.createElement('div');
                div.className = 'preview-item';
                div.innerHTML = `<img src="${e.target.result}" alt="preview"><span>${file.name}</span>`;
                preview.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
    }
});

// Multi-step navigation with validation
function nextStep(step) {
    // Validate current step before moving forward
    const currentActive = document.querySelector('.form-step-content.active');
    if (currentActive) {
        const currentStep = parseInt(currentActive.id.replace('step', ''));
        if (step > currentStep) {
            const requiredFields = currentActive.querySelectorAll('[required]');
            let valid = true;
            requiredFields.forEach(f => {
                if (!f.value) {
                    f.classList.add('is-invalid');
                    valid = false;
                } else {
                    f.classList.remove('is-invalid');
                }
            });
            if (!valid) {
                // Shake animation
                currentActive.style.animation = 'none';
                currentActive.offsetHeight;
                currentActive.style.animation = 'shake 0.4s';
                return;
            }
        }
    }

    document.querySelectorAll('.form-step-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.form-step').forEach(el => el.classList.remove('active'));
    document.getElementById('step' + step).classList.add('active');
    document.querySelector(`.form-step[data-step="${step}"]`).classList.add('active');
    document.querySelectorAll('.form-step').forEach(el => {
        if (parseInt(el.dataset.step) < step) el.classList.add('done');
        else el.classList.remove('done');
    });
}

// Star rating
function setRating(value) {
    document.getElementById('ratingInput').value = value;
    for (let i = 1; i <= 5; i++) {
        const star = document.getElementById('star' + i);
        if (star) {
            star.className = i <= value ? 'bi bi-star-fill text-warning' : 'bi bi-star text-muted';
        }
    }
}
