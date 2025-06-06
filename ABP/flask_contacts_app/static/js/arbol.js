document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("prediction-form");
    const resultado = document.getElementById("resultado");

    form.addEventListener("submit", function(event) {
        event.preventDefault(); // Evita que la página se recargue

        let nivel_estres = parseFloat(document.getElementById("nivel_estres").value);
        let horas_sueno = parseFloat(document.getElementById("horas_sueno").value);
        let actividad_fisica = parseFloat(document.getElementById("actividad_fisica").value);

        if (isNaN(nivel_estres) || isNaN(horas_sueno) || isNaN(actividad_fisica)) {
            resultado.innerText = "Por favor, ingrese valores válidos.";
            resultado.style.color = "red";
            return;
        }

        POST('/ejercicios', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                nivel_estres: nivel_estres,
                horas_sueno: horas_sueno,
                actividad_fisica: actividad_fisica
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                resultado.innerText = "Error: " + data.error;
                resultado.style.color = "red";
            } else {
                resultado.innerText = "Estado predicho: " + data.estado;
                resultado.style.color = "green";
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultado.innerText = "Hubo un error al procesar la predicción.";
            resultado.style.color = "red";
        });
    });
});
