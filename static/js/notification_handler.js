const token = localStorage.getItem("token");
const messagesList = document.getElementById("messagesList");
const unreadCountSpan = document.getElementById("unreadCount");

if (!token) {
    window.location.href = "/login";
}

// =========================================================================
// 1. OBTENER INFORMACIÓN DEL USUARIO Y AJUSTAR LA INTERFAZ
// =========================================================================
fetch("/api/dashboard", {
    headers: { "Authorization": `Bearer ${token}` }
})
.then(res => {
    if (!res.ok) throw new Error("Unauthorized");
    return res.json();
})
.then(data => {
    // Si es USUARIO, muestra el formulario de Soporte
    if (data.role === "user") {
        document.getElementById("supportFormContainer").style.display = "block";
    }
    // Si es ADMIN, oculta ambos (la lógica de admin está en dashboard)
    if (data.role === "admin") {
        // ...
    }
    
    // Una vez que tenemos el rol, cargamos los mensajes
    loadMessages();
})
.catch(err => {
    console.error("Error al obtener el rol del usuario:", err);
    alert("Error de autenticación. Por favor, vuelve a iniciar sesión.");
    localStorage.clear();
    window.location.href = "/";
});


// =========================================================================
// 2. LÓGICA DEL BUZÓN (GET /api/messages)
// =========================================================================

function loadMessages() {
    messagesList.innerHTML = '<p>Cargando mensajes...</p>';
    fetch("/api/messages", {
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(messages => {
        messagesList.innerHTML = ''; // Limpiar el mensaje de carga
        let unread = 0;

        if (messages.length === 0) {
            messagesList.innerHTML = '<p class="text-info">Tu buzón está vacío.</p>';
            unreadCountSpan.innerText = 0;
            return;
        }

        messages.forEach(msg => {
            const isRead = msg.is_read_by_recipient;
            
            // Lógica para contar no leídos:
            if (!isRead && msg.message_type !== 'alert') {
                unread++;
            }

            const messageElement = document.createElement("div");
            messageElement.classList.add("message-item");
            messageElement.classList.add(isRead ? "read" : "unread");
            messageElement.id = `message-${msg.id}`;

            // Estilos y etiquetas basados en el tipo de mensaje
            let typeLabel = '';
            let markReadButton = '';
            
            if (msg.message_type === 'alert') {
                typeLabel = '<span class="badge bg-danger">ALERTA GLOBAL</span>';
            } else if (msg.message_type === 'support') {
                typeLabel = '<span class="badge bg-warning text-dark">SOPORTE TÉCNICO</span>';
            } else {
                typeLabel = '<span class="badge bg-primary">PRIVADO</span>';
            }
            
            // Solo se puede marcar como leído si NO es una alerta global
            if (!isRead && msg.message_type !== 'alert') {
                markReadButton = `<button class="btn btn-sm btn-outline-secondary float-end" onclick="markAsRead('${msg.id}')">Marcar Leído</button>`;
            }

            // 💡 ESTA ES LA PARTE QUE DEBES AÑADIR/MODIFICAR 💡
            // ----------------------------------------------------
            let deleteButton = '';
            
            // Solo permitir borrar si NO es una alerta global
            if (msg.message_type !== 'alert') { 
                deleteButton = `<button class="btn btn-sm btn-outline-danger float-end ms-2" onclick="deleteMessage('${msg.id}')">Eliminar</button>`;
            }
            // ----------------------------------------------------

            const date = new Date(msg.timestamp);
            const localDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000));
            const formattedDate = localDate.toLocaleString("es-AR", { hour12: false });
            messageElement.innerHTML = `
                <div class="message-header">
                    ${typeLabel}
                    ${markReadButton}
                    ${deleteButton}  <strong class="subject">${msg.subject}</strong>
                </div>
                <small class="text-muted">De: ${msg.sender_username} - ${formattedDate}</small>
                <p class="message-body">${msg.body}</p>
            `;

            messagesList.appendChild(messageElement);
        });

        unreadCountSpan.innerText = unread;
    })
    .catch(err => {
        console.error("Error al cargar mensajes:", err);
        messagesList.innerHTML = '<p class="text-danger">Error al cargar mensajes. Intenta de nuevo.</p>';
    });
}


// =========================================================================
// 3. LÓGICA DE ENVÍO DE SOPORTE (POST /api/messages/support)
// =========================================================================

document.getElementById("supportForm").addEventListener("submit", function(e) {
    e.preventDefault();
    
    const subject = document.getElementById("supportSubject").value;
    const body = document.getElementById("supportBody").value;

    fetch("/api/messages/support", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ subject: subject, body: body })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        // Limpiar formulario y recargar mensajes
        document.getElementById("supportSubject").value = "";
        document.getElementById("supportBody").value = "";
        loadMessages(); 
    })
    .catch(err => {
        console.error("Error al enviar mensaje de soporte:", err);
        alert("Error al enviar el mensaje de soporte.");
    });
});


// =========================================================================
// 4. MARCAR COMO LEÍDO (PATCH /api/messages/<id>/read)
// =========================================================================

function markAsRead(messageId) {
    fetch(`/api/messages/${messageId}/read`, {
        method: "PATCH",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
        if (data.message.includes("marcado como leído")) {
            // Actualizar la apariencia en el DOM sin recargar
            const msgElement = document.getElementById(`message-${messageId}`);
            if (msgElement) {
                msgElement.classList.remove("unread");
                msgElement.classList.add("read");
                
                // Remover el botón "Marcar Leído"
                const button = msgElement.querySelector(".float-end");
                if (button) button.remove();
            }
            // Recalcular no leídos
            loadMessages();
        } else {
            alert("No se pudo marcar como leído.");
        }
    })
    .catch(err => {
        console.error("Error al marcar como leído:", err);
        alert("Error de red al intentar marcar como leído.");
    });
}

// =========================================================================
// 5. ELIMINAR MENSAJE (DELETE /api/messages/<id>)
// =========================================================================
function deleteMessage(messageId) {
    if (!confirm("¿Estás seguro de que quieres eliminar este mensaje?")) {
        return;
    }

    fetch(`/api/messages/${messageId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
        if (data.message.includes("eliminado con éxito")) {
            alert(data.message);
            // Quitar el elemento del DOM y recargar para actualizar el contador
            document.getElementById(`message-${messageId}`).remove();
            loadMessages(); 
        } else {
            alert(data.message);
        }
    })
    .catch(err => {
        console.error("Error al eliminar el mensaje:", err);
        alert("Error de red al intentar eliminar el mensaje.");
    });
}