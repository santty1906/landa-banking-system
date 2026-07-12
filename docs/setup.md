# Guía de instalación — LANDA Bank

Esta guía combina el flujo de trabajo en equipo que ya existía con las correcciones reales de cómo levantar el backend, confirmadas ejecutando el proyecto de punta a punta. Está pensada para Windows con PowerShell (que es lo que ha usado el equipo hasta ahora); si alguien usa Mac/Linux, los comandos de `pip`/`python`/`git` son los mismos, solo cambia cómo se activa el entorno virtual (se indica más abajo).

## 0. Antes de empezar: dos reglas importantes

1. **Usa Python 3.11**, no una versión más nueva (3.13/3.14). Las librerías de reconocimiento facial (numpy, opencv, tensorflow) no siempre tienen versiones precompiladas para Python muy reciente, y terminarías con errores de compilación difíciles de resolver.
2. **En Windows, clona el repo en una ruta corta, fuera de OneDrive** (por ejemplo `C:\landa-banking-system`, no `C:\Users\TuUsuario\OneDrive\Escritorio\...`). Algunas librerías (TensorFlow) generan rutas internas muy largas, y si tu proyecto ya está anidado dentro de varias carpetas de OneDrive, es fácil pasarte del límite de longitud de ruta de Windows.

## 1. Clona el repositorio

```bash
git clone https://github.com/santty1906/landa-banking-system.git
cd landa-banking-system
```

## 2. Archivos de entorno

Copia la plantilla del backend y genera tus propias claves (no reutilices las de otro integrante del equipo — cada quien genera las suyas):

```bash
cd backend
cp .env.example .env        # en PowerShell: Copy-Item .env.example .env
```

Genera dos claves distintas con este comando (una para `SECRET_KEY`, otra para `ENCRYPTION_KEY`):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Pega cada resultado en la línea correspondiente de tu `backend/.env`. Debería quedar algo así (con tus propios valores, no estos de ejemplo):

```env
SECRET_KEY=abc123...
ENCRYPTION_KEY=xyz789...
SESSION_COOKIE_SECURE=true
SESSION_TIMEOUT_MINUTES=30
FACE_DETECTOR_BACKEND=retinaface
FACE_MIN_CONFIDENCE=0.80
FACE_ANTI_SPOOFING=true
```

(Revisa tu `.env.example` actual por si hay variables adicionales agregadas después de escribir esta guía, y cópialas con el mismo formato.)

> **Nota:** si el repositorio tiene también un `.env.example` en la raíz o dentro de `frontend/`, cópialos igual con `cp .env.example .env` en su carpeta correspondiente. Esta guía no puede confirmar el contenido exacto de esos dos porque no se trabajaron durante la sesión de corrección de código — si alguno falla al momento de usarlo, coméntalo en el grupo.

## 3. Opción A — Levantar todo con Docker

```bash
docker compose up --build
```

Esto levanta la base de datos y el backend juntos. El backend corre con `gunicorn` (servidor de producción para Flask) según quedó configurado en el `Dockerfile` y `docker-compose.yml` del proyecto — si ves alguna referencia a `uvicorn` en algún archivo viejo, es un resto de una versión anterior del proyecto y ya no aplica; Flask no es compatible con `uvicorn` sin una capa adicional.

## 4. Opción B — Backend local, sin Docker

```bash
cd backend
py -3.11 -m venv venv
```

**Activa el entorno virtual:**

En Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

Si te sale un error de que la ejecución de scripts está deshabilitada, corre esto una sola vez (solo afecta a esta ventana de terminal):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

En Mac/Linux:

```bash
source venv/bin/activate
```

Sabrás que se activó porque tu línea de comandos empieza con `(venv)`.

**Instala las dependencias:**

```bash
pip install -r requirements.txt
```

Esto tarda varios minutos (TensorFlow, DeepFace, PyTorch, OpenCV, MediaPipe son librerías pesadas). Si algo falla en esta instalación, no lo intentes resolver solo — hubo ajustes de versión específicos (por ejemplo, `opencv-python` necesita una versión exacta) que ya se resolvieron una vez; es más rápido preguntar en el grupo que adivinar.

**Confirma que todo carga bien:**

```bash
python -c "from app.app import create_app; app = create_app(); print('OK, la app carga correctamente')"
```

**Corre las pruebas automatizadas:**

```bash
pytest
```

Deberías ver algo como `61 passed` con cobertura arriba del 70%.

**Levanta la aplicación:**

```bash
python run.py
```

Abre el navegador en `http://localhost:5000`.

## 5. (Opcional) Probar Face ID desde un celular

Face ID necesita HTTPS para acceder a la cámara (no funciona con la IP local de tu red Wi-Fi). Para probarlo desde un teléfono:

1. Instala [ngrok](https://ngrok.com/download) y crea una cuenta gratuita.
2. Conecta tu token (cópialo con cuidado desde tu dashboard de ngrok, sin caracteres extra al inicio o final):
   ```bash
   ngrok config add-authtoken TU_TOKEN_AQUI
   ```
3. Con `python run.py` corriendo en una terminal, abre **otra** terminal y corre:
   ```bash
   ngrok http 5000
   ```
4. Abre la URL `https://....ngrok-free.app` que te dé, desde el navegador de tu celular.

## Resumen de comandos del día a día (backend local)

Una vez hecha la instalación completa (pasos 1-2 y 4), cada vez que retomes el proyecto solo necesitas:

```bash
cd landa-banking-system/backend
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

python run.py
```

Y para correr las pruebas: `pytest`

## Si algo no funciona

Este proyecto pasó por bastantes ajustes de entorno (versión de Python, versión de OpenCV, rutas de Windows) antes de quedar estable. Antes de pasar horas resolviendo algo solo, comparte en el grupo:

- El comando exacto que corriste
- El mensaje de error completo (una captura de pantalla de la terminal sirve)
- En qué paso de esta guía estabas

## Flujo de colaboración

- Crea ramas de feature a partir de `main`
- Mantén los PRs enfocados y pequeños
- Corre las pruebas localmente (`pytest`) antes de abrir un PR
- Usa mensajes de commit siguiendo convenciones (conventional commits) cuando sea posible
