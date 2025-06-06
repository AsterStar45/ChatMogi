document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("mensaje");
    const boton = document.getElementById("enviar");
    const conversacion = document.getElementById("conversacion");

    input.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            enviarMensaje();
        }
    });

    boton.addEventListener("click", function () {
        enviarMensaje();
    });

    function enviarMensaje() {
        const mensaje = input.value.trim();
        if (!mensaje) return;

        fetch("/chatbot", {
            method: "POST",
            body: JSON.stringify({ mensaje }),
            headers: { "Content-Type": "application/json" }
        })
        .then(response => response.json())
        .then(data => {
            mostrarMensaje("Tú", mensaje);
            mostrarMensaje("MOGI", data.respuesta);
            input.value = "";
        });
    }

function mostrarMensaje(remitente, texto) {
    const mensaje = document.createElement("div");

    if (remitente === "Tú") {
        mensaje.classList.add("mogi-user-message");
        mensaje.innerHTML = `
            <div style="display: flex; align-items: center;">
                <img src="/static/css/user_profile0.png" alt="Usuario" class="mogi-avatar">
                <div><strong>${remitente}:</strong> ${texto}</div>
            </div>
        `;
    } else {
        mensaje.classList.add("mogi-bot-message");
        mensaje.innerHTML = `
            <div style="display: flex; align-items: center;">
                <img src="/static/css/user_mogi.png" alt="MOGI" class="mogi-avatar">
                <div><strong>${remitente}:</strong> ${texto}</div>
            </div>
        `;
    }

    conversacion.appendChild(mensaje);
    conversacion.scrollTop = conversacion.scrollHeight;
}

});

function detectarEnter(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    enviarMensaje();
  }
}

function enviarMensaje() {
  const mensajeInput = document.getElementById("mensaje");
  const mensaje = mensajeInput.value.trim();
  const conversacion = document.getElementById("conversacion");

  if (mensaje === "") return;

  // Mostrar mensaje del usuario
  const userMessage = document.createElement("div");
  userMessage.className = "user-message";
  userMessage.innerHTML = `<div style="text-align:right;"><strong>Tú:</strong> ${mensaje}</div>`;
  conversacion.appendChild(userMessage);

  mensajeInput.value = "";

  // Mostrar animación de cargando
  const loader = document.createElement("div");
  loader.id = "loader";
  loader.className = "loader";
  loader.innerHTML = `
    <div class="loader-dot"></div>
    <div class="loader-dot"></div>
    <div class="loader-dot"></div>
  `;
  conversacion.appendChild(loader);
  conversacion.scrollTop = conversacion.scrollHeight;

  // Enviar mensaje al backend y mostrar respuesta real
  fetch("/chatbot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ mensaje })
  })
    .then(respuesta => respuesta.json())
    .then(data => {
      loader.remove();

      const botMessage = document.createElement("div");
      botMessage.className = "mogi-bot-message";
      botMessage.innerHTML = `
        <div style="display: flex; align-items: center;">
          <img src="/static/css/user_mogi.png" alt="MOGI" class="mogi-avatar">
          <div><strong>Mogi:</strong> ${data.respuesta}</div>
        </div>
      `;
      conversacion.appendChild(botMessage);
      conversacion.scrollTop = conversacion.scrollHeight;
    })
    .catch(error => {
      loader.remove();

      const errorMessage = document.createElement("div");
      errorMessage.className = "mogi-bot-message";
      errorMessage.innerHTML = `
        <div style="display: flex; align-items: center;">
          <img src="/static/css/user_mogi.png" alt="MOGI" class="mogi-avatar">
          <div><strong>Mogi:</strong> Lo siento, hubo un error al responder.</div>
        </div>
      `;
      conversacion.appendChild(errorMessage);
      conversacion.scrollTop = conversacion.scrollHeight;
      console.error("Error al obtener respuesta de MOGI:", error);
    });
}
