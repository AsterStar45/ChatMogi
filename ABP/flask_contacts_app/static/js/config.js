    function eliminarUsuario(buttonElement) {
        const nombreUsuario = buttonElement.getAttribute('data-usuario');

        fetch('/configuracion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `eliminar_usuario=${encodeURIComponent(nombreUsuario)}`
        })
        .then(response => response.text())
        .then(data => {
            location.reload();
        })
        .catch(error => {
            console.error('Error al eliminar el usuario:', error);
        });
    }