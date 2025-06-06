function showContactInfo() {
    alert("Correo: MOGI.edu.co");
}

document.querySelector('#evaluacion-form').addEventListener('submit', function(event) {
    event.preventDefault();
    alert('¡Gracias por compartir cómo te sientes! Tu evaluación ha sido registrada.');
    document.querySelector('#evaluacion-form').reset();
});
