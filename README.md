Simon-Garcia-Ayelen-Penia-Valentina-Frias
# 🗻 OpenFrontier
OpenFrontier es una aplicación web desarrollada con **Flask (Python)** que proporciona información **en tiempo real** sobre el estado del **Paso Internacional Cristo Redentor**, principal conexión terrestre entre **Mendoza (Argentina)** y **Chile**.  

El sistema informa si el paso se encuentra **abierto, cerrado o demorado**, e integra datos de **condiciones climáticas**, **alertas**, **soporte técnico** y **notificaciones personalizadas**, facilitando la planificación de viajes a través de la cordillera de los Andes.

---

## 👥 Integrantes del equipo

- **Lucas Olguin**  
- **Simón García**  
- **Ayelén Peña**  
- **Valentina Frías**

---

## 🌐 Descripción general

El proyecto surge como una herramienta para brindar **información clara, confiable y actualizada** a viajeros que desean cruzar el paso fronterizo entre Mendoza y Chile.  

Además del estado del paso, OpenFrontier ofrece:
- 📡 **Actualizaciones automáticas** sobre la apertura o cierre del paso.  
- 🌤️ **Condiciones meteorológicas** en tiempo real.  
- 🚗 **Reportes de usuarios** y alertas colaborativas.  
- 💬 **Mensajes internos y soporte técnico** dentro de la plataforma.  
- 🔔 **Notificaciones y buzón de alertas** personalizadas.  

---

## 🧩 Tecnologías utilizadas

**Backend**
- Python 3  
- Flask  
- Blueprints (rutas modulares)  
- JWT (autenticación segura)  
- SQLite / MySQL (base de datos)  

**Frontend**
- HTML5, CSS3, JavaScript (Fetch API)  
- Bootstrap 5  
- Plantillas Jinja2  

**Testing y utilidades**
- Pytest (tests unitarios e integrales)  
- Cron/Jobs para tareas automáticas  
- Logging y manejo de errores  

---

## 🗂️ Estructura del proyecto
OpenFrontier/
│
├── app.py # Punto de entrada principal de Flask
├── routes/
│ ├── users_routes.py # Registro, login y gestión de usuarios
│ ├── messages_routes.py # Sistema interno de mensajes y alertas
│ ├── tomar_paso_routes.py # Datos del Paso Cristo Redentor
│ ├── clima_routes.py # Clima y temperatura en tiempo real
│ └── init.py
│
├── static/
│ ├── js/
│ │ ├── dashboard.js
│ │ ├── logout_handler.js
│ │ ├── nav_handler.js
│ │ └── ...
│ └── css/
│ └── layout.css
│
├── templates/
│ ├── layout.html
│ ├── dashboard.html
│ ├── login.html
│ └── ...
│
├── tests/
│ └── test_unit_and_integration.py
│


Configuración del entorno
1. Crear un entorno virtual
   
En Linux / macOS:
python3 -m venv <nombre_del_entorno>

En Windows:
python -m venv <nombre_del_entorno>

2. Activar el entorno virtual
En Linux / macOS:
source <nombre_del_entorno>/bin/activate

En Windows:
<nombre_del_entorno>\Scripts\activate

instalar dependencias:
pip install -r requirements.txt

Configurar variables de entorno:
export FLASK_APP=app.py
export FLASK_ENV=development

Configuración de la base de datos
Antes de ejecutar la aplicación, debes configurar las siguientes variables de entorno:


MYSQL_USER=<tu_usuario>

MYSQL_PASSWORD=<tu_contraseña>

MYSQL_HOST=<host_de_mysql>

MYSQL_PORT=<puerto_de_la_base_de_datos>

MYSQL_DB_NAME=<nombre_de_la_base_de_datos>


SECRET_KEY="clave secreta"

WEATHER_API_KEY="api key"


Antes de iniciar app.py:
if __name__ == "__main__":
    with app.app_context():
        #db.drop_all()  #esto se descomenta para reiniciar la base de datos!!!
        #db.create_all() #esto se descomenta la primera vez que se inicia la app para crear las tablas
        print("")
        # Esta llamada solo se ejecuta cuando el script se inicia directamente, NO en el import de pytest
        #actualizar_estado() 
        

🧭 Funcionalidades principales
| Módulo                          | Descripción                                                              |
| ------------------------------- | ------------------------------------------------------------------------ |
| **Inicio de sesión / Registro** | Autenticación mediante JWT.                                              |
| **Estado del paso fronterizo**  | Indica si el Paso Cristo Redentor está abierto, cerrado o demorado.      |
| **Clima en tiempo real**        | Datos actualizados desde APIs meteorológicas.                            |
| **Mensajes y soporte técnico**  | Sistema de buzón interno entre usuarios y administradores.               |
| **Alertas globales**            | Envío de mensajes importantes visibles para todos los usuarios.          |
| **Panel de usuario**            | Visualización de notificaciones, mensajes y actualizaciones del sistema. |

🔍Entidades:
| **Entidad**                      | **Atributos principales**                                                          | **Relaciones**                                                                      | **Notas**                                         |
| -------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------- |
| **Usuario (User)**               | `id`, `username`, `email`, `password`, `role`, `phone`, `created_at`, `updated_at` | Puede tener muchas **Notificaciones**, puede tener historial de **Pasos** visitados | Rol determina acceso (admin, user)                |
| **Paso (BorderCrossing / Paso)** | `id`, `nombre`, `estado`, `horario_atencion`, `actualizado`, `image_filename`      | Tiene muchos **Clima**, puede tener **logs de usuario**                             | Estado dinámico, usado en dashboard y mapas       |
| **Clima (Weather)**              | `id`, `paso_id` (FK → Paso), `temperatura`, `descripcion`, `viento`, `fecha`       | Pertenece a un **Paso**                                                             | Última medición para mostrar en dashboard         |
| **Notificación (Notification)**  | `id`, `user_id` (FK → Usuario), `titulo`, `mensaje`, `tipo`, `leido`, `created_at` | Pertenece a un **Usuario**                                                          | Para alertas o avisos de la app                   |
| **Rol (Role)**                   | `nombre` (admin, user, supervisor)                                                 | Puede estar asociado a **Usuario**                                                  | Puede ser un atributo en Usuario o tabla separada |
| **Registro de Logs (Log)**       | `id`, `user_id` (FK → Usuario), `accion`, `fecha`                                  | Pertenece a un **Usuario**                                                          | Opcional, útil para auditoría y tracking          |


🧪 Tests

-Unit Test
Instalar pytest

pip install pytest pytest-flask

-Para ejecutar los tests unitarios e integrales:
pytest 

 o sino:

 python -m pytest

-Migrations
-Intalar Flask Migrate

pip install Flask-Migrate

flask db init

flask db migrate -m "init"

flsask db upgrade

imagenes:
<img width="1211" height="781" alt="image" src="https://github.com/user-attachments/assets/759a3b70-f485-4a6e-be98-e796638b2e4c" />
<img width="1221" height="812" alt="image" src="https://github.com/user-attachments/assets/bfe464a3-1134-45fc-8f9d-c544b2991da0" />
<img width="764" height="825" alt="image" src="https://github.com/user-attachments/assets/b1daa830-7839-42fc-840f-74134fe0d242" />
<img width="1241" height="659" alt="image" src="https://github.com/user-attachments/assets/1491afed-00a7-477e-86c5-4ad83cb0225c" />

📄 Licencia

Proyecto académico desarrollado por Lucas Olguin, Simón García, Ayelén Peña y Valentina Frías.
Todos los derechos reservados © 2025 — OpenFrontier.




