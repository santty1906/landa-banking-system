# Guía de instalación — LANDA Bank

Esta guía está pensada para que **cualquier persona** pueda correr el proyecto por su cuenta, sin depender de preguntarle a nadie del equipo — incluye los errores específicos que ya encontramos nosotros mismos, con su solución exacta.

Pensada para Windows con PowerShell (que es lo que ha usado el equipo); si usas Mac/Linux, los comandos de `pip`/`python`/`git` son los mismos, solo cambia cómo se activa el entorno virtual (se indica más abajo).

> **Estado de esta guía:** la ruta de instalación local (sin Docker, sección 3) fue probada de punta a punta varias veces por el equipo — es la ruta recomendada y la que deberías seguir. La ruta con Docker (sección 4) es completamente opcional, **no fue verificada** por el equipo, y no es un requisito del curso — sáltala sin problema a menos que quieras experimentar con ella por tu cuenta.

## 0. Antes de empezar: reglas importantes

1. **Usa Python 3.11**, no una versión más nueva (3.13/3.14). Las librerías de reconocimiento facial (numpy, opencv, tensorflow) no siempre tienen versiones precompiladas para Python muy reciente, y terminarías con errores de compilación difíciles de resolver.
2. **En Windows, clona el repo en una ruta corta, fuera de OneDrive** (por ejemplo `C:\landa-banking-system`, no `C:\Users\TuUsuario\OneDrive\Escritorio\...`). Algunas librerías (TensorFlow) generan rutas internas muy largas, y si tu proyecto ya está anidado dentro de varias carpetas de OneDrive, es fácil pasarte del límite de longitud de ruta de Windows.
3. **Necesitas conexión a internet la primera vez que uses Face ID** (enrolamiento o login), no solo durante la instalación — varios modelos de reconocimiento facial y detección de vida se descargan automáticamente en su primer uso, no durante `pip install`.

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

Pega cada resultado en la línea correspondiente de tu `backend/.env`. Debería quedar así (con tus propios valores, no estos de ejemplo):

```env
SECRET_KEY=abc123...
ENCRYPTION_KEY=xyz789...
SESSION_COOKIE_SECURE=true
SESSION_TIMEOUT_MINUTES=30
FACE_DETECTOR_BACKEND=retinaface
FACE_MIN_CONFIDENCE=0.80
FACE_ANTI_SPOOFING=true
FACE_CHECK_EYES_OPEN=true
FACE_MIN_EYE_ASPECT_RATIO=0.20
```

> Si tu `.env.example` tiene variables adicionales que no aparecen en este ejemplo, cópialas igual con el mismo formato — puede que se hayan agregado después de escribir esta guía.

## 3. Backend local (ruta recomendada, probada por el equipo)

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
Esto tarda varios minutos (TensorFlow, DeepFace, PyTorch, OpenCV, MediaPipe son librerías pesadas).

**Confirma que todo carga bien:**
```bash
python -c "from app.app import create_app; app = create_app(); print('OK, la app carga correctamente')"
```

**Corre las pruebas automatizadas:**
```bash
pytest
```
Deberías ver algo como `63 passed` con cobertura arriba del 70%.

**Levanta la aplicación:**
```bash
python run.py
```
Abre el navegador en `http://localhost:5000`.

## 4. (Opcional, no verificado) Levantar todo con Docker

El equipo evaluó esta ruta pero **decidió no invertir tiempo en verificarla**, ya que no es un requisito del curso y ya existe una ruta local completamente funcional (sección 3). Solo síguela si te interesa experimentar con Docker por tu cuenta; no es necesaria para evaluar ni correr el proyecto.

```bash
docker compose up --build
```

Esto debería levantar la base de datos y el backend juntos, sirviendo con `gunicorn` según quedó configurado en el `Dockerfile` y `docker-compose.yml`. Requiere Docker Desktop instalado (con WSL2 en Windows), lo cual implica reiniciar la computadora y, en algunos equipos, activar virtualización desde el BIOS — por eso el equipo no lo consideró necesario para este proyecto. **Si esto falla, usa la sección 3**, que sí está confirmada.

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

Una vez hecha la instalación completa (secciones 1-2 y 3), cada vez que retomes el proyecto solo necesitas:

```bash
cd landa-banking-system/backend
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

python run.py
```

Y para correr las pruebas: `pytest`

## Solución a errores específicos ya conocidos

Estos son errores reales que el equipo ya encontró y resolvió — si te aparece alguno, la solución ya está probada, no hace falta que le preguntes a nadie.

### `ModuleNotFoundError` o error de compilación al instalar `numpy`/`opencv`/`tensorflow`

Estás usando una versión de Python distinta a 3.11 (probablemente 3.13 o 3.14). Confirma con `python --version` dentro del entorno virtual activado. Si es incorrecta, borra la carpeta `venv` y vuelve a crearla explícitamente con `py -3.11 -m venv venv` (ver sección 3).

### `Face could not be detected` o `Confirm that opencv is installed on your environment... violated`

La versión de `opencv-python` que se instaló no incluye los archivos de detección facial (le pasó a la versión más nueva del paquete, 5.x, en cierto momento). Confirma la versión exacta:
```bash
pip show opencv-python
```
Si no coincide con la versión fijada en `requirements.txt`, reinstálala explícitamente:
```bash
pip uninstall -y opencv-python
pip install opencv-python==4.11.0.86
```

### Error de importación mencionando `protobuf` al usar MediaPipe

`mediapipe` y `tensorflow` pueden pedir versiones distintas de `protobuf`. Corrige con:
```bash
pip install --upgrade "protobuf>=6.31.1,<7"
```

### El chequeo de "ojos cerrados" no rechaza nada, ni da error

Es un comportamiento intencional, no un bug: si el modelo de MediaPipe no logra descargarse (por ejemplo, si una red universitaria o corporativa bloquea el dominio `storage.googleapis.com`), el sistema **deja pasar la captura en silencio** en vez de tumbar todo el login. Revisa la terminal donde corre `python run.py` — si ves la advertencia `No se pudo ejecutar la detección de ojos abiertos; se omite este chequeo`, confirma que fue exactamente esto.

### `.\venv\Scripts\Activate.ps1 no se reconoce...`

Estás en la carpeta incorrecta. Confirma con `dir` que ves `requirements.txt` y `run.py` en el listado — si no, navega primero a la carpeta `backend` del proyecto.

### `IndentationError` después de pegar código

Ocurre al copiar/pegar bloques de código en Notepad u otros editores que mezclan tabs y espacios. Verifica con `python -m py_compile ruta\al\archivo.py` antes de correr la app; si marca error, vuelve a pegar el bloque completo de la función afectada (borrando la versión anterior por completo) en vez de intentar corregir línea por línea.

## Flujo de colaboración

- Crea ramas de feature a partir de `main`
- Mantén los PRs enfocados y pequeños
- Corre las pruebas localmente (`pytest`) antes de abrir un PR
- Usa mensajes de commit siguiendo convenciones (conventional commits) cuando sea posible
