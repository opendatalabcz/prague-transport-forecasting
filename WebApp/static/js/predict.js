// --- DROPDOWN LOGIKA ---
document.querySelectorAll('.select-option').forEach(option => {
    option.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('data-target');
        const value = this.getAttribute('data-value');
        const text = this.innerText;

        document.getElementById(targetId).value = value;
        const btn = document.getElementById(targetId + '-button');
        btn.querySelector('span').innerText = text;
    });
});

// --- ODESLÁNÍ NA SERVER ---
document.getElementById('predictForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
        date: document.getElementById('date').value,
        temp: document.getElementById('temp').value,
        rain: document.getElementById('rain').value,
        sun: document.getElementById('sun').value, 
        wind: document.getElementById('wind').value,
        snow: document.getElementById('snow').value
    };

    const container = document.getElementById('results-container');
    container.style.opacity = "1"; // Zvýrazníme výsledky

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.success) {
            // Animace čísla (volitelné, ale hravé)
            document.getElementById('res-car').innerText = result.car_value;
            document.getElementById('res-mhd').innerText = result.mhd_value;
            document.getElementById('res-bike').innerText = result.cyclo_value;

            // Zobrazení grafu pro auta
            const btnShapCar = document.getElementById('btn-shap-car');
            btnShapCar.classList.remove('d-none'); // Zobrazíme tlačítko
            
            btnShapCar.onclick = () => {
                document.getElementById('shap-img-placeholder-car').src = "data:image/png;base64," + result.car_shap;
            };

            // Zobrazení grafu pro MHD
            const btnShapMhd = document.getElementById('btn-shap-mhd');
            btnShapMhd.classList.remove('d-none'); // Zobrazíme tlačítko

            btnShapMhd.onclick = () => {
                document.getElementById('shap-img-placeholder-mhd').src = "data:image/png;base64," + result.mhd_shap;
            };

            // Zobrazení grafu pro kola
            const btnShapCyclo = document.getElementById('btn-shap-cyclo');
            btnShapCyclo.classList.remove('d-none'); // Zobrazíme tlačítko

            btnShapCyclo.onclick = () => {
                document.getElementById('shap-img-placeholder-cyclo').src = "data:image/png;base64," + result.cyclo_shap;
            };
        } else {
            alert("Chyba: " + result.error);
        }
    } catch (err) {
        console.error("Chyba komunikace:", err);
    }
});
