# 🩺 NeumScan

**Sistema Inteligente para el Análisis Automatizado de Radiografías Pulmonares**

## 📑 Tabla de Contenidos

- [👥 Integrantes](#-integrantes)
- [📝 Descripción General](#-descripción-general)
- [✨ Características Destacadas](#-características-destacadas)
- [⚙️ Requisitos Previos](#️-requisitos-previos)
- [🚀 Instalación Paso a Paso](#-instalación-paso-a-paso)
- [🔧 Configuración Inicial y Variables de Entorno](#-configuración-inicial-y-variables-de-entorno)
- [⬇️ Descarga del Modelo de IA](#️-descarga-del-modelo-de-ia)
- [▶️ Ejecución de la Aplicación](#️-ejecución-de-la-aplicación)
- [🖥️ Guía de Uso](#️-guía-de-uso)
- [📂 Estructura del Proyecto](#-estructura-del-proyecto)
- [🤝 Contribuciones](#-contribuciones)
- [🛡️ Licencia](#️-licencia)
- [📬 Contacto](#-contacto)

## 👥 Integrantes

- Jose Manuel Sanchez Puga
- Steven Leonardo Barona Alvarado
- Elkin James Salvatierra Villarreal
- Aaron Joel Flores Martinez

## 📝 Descripción General

**NeumScan** es una plataforma web avanzada que utiliza inteligencia artificial para analizar radiografías pulmonares, facilitando el diagnóstico temprano de enfermedades respiratorias.
Permite a los profesionales de la salud gestionar pacientes, analizar imágenes, generar informes automáticos y mantener la seguridad de los datos médicos.

## ✨ Características Destacadas

- 👤 **Gestión de usuarios y roles** (doctores, administradores)
- 🗂️ **Gestión integral de pacientes**
- 🖼️ **Carga y análisis automático de radiografías**
- 🤖 **Diagnóstico asistido por IA** con nivel de confianza
- 📄 **Generación y descarga de informes PDF**
- 📊 **Panel administrativo con estadísticas e historial**
- 📧 **Notificaciones automáticas por correo**
- 🔒 **Seguridad y privacidad de datos**
- 🌐 **Integración con servicios externos (Google, correo, etc.)**

## ⚙️ Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- 🐍 Python 3.10 o superior
- 🧬 Git
- 🌐 Acceso a internet
- 📧 Cuenta de Google para autenticación (opcional)
- 💻 (Opcional) Editor de código como VSCode

## 🚀 Instalación Paso a Paso

### 1️⃣ Clona el repositorio

```sh
git clone https://github.com/tu_usuario/neumscan.git
cd neumscan
```

### 2️⃣ Crea y activa un entorno virtual

```sh
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate
```

### 3️⃣ Instala las dependencias

```sh
pip install --upgrade pip
pip install -r requirements.txt
```

## 🔧 Configuración Inicial y Variables de Entorno

### 🛠️ Paso a paso para cada variable:

#### 🔑 Google OAuth2

1. Ve a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto o selecciona uno existente.
3. Ve a **APIs y servicios** > **Credenciales**.
4. Haz clic en **Crear credenciales** > **ID de cliente de OAuth**.
5. Selecciona **Aplicación web**.
6. En **URIs de redirección autorizados** agrega:
   - `http://127.0.0.1:8000/settings/google/callback/`
   - (Opcional) `http://localhost:8000/settings/google/callback/`
7. Descarga el archivo `client_secrets.json` y colócalo en la raíz del proyecto.
8. Copia el `client_id` y el `client_secret` y pégalos en tu archivo `.env` así:

```env
GOOGLE_OAUTH2_CLIENT_ID=tu_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=tu_client_secret
```

#### 📧 Correo electrónico (Gmail)

1. Ve a [Gestionar tu cuenta de Google](https://myaccount.google.com/security).
2. Activa la **verificación en dos pasos**.
3. Crea una **Contraseña de aplicación** para Gmail.
4. Usa tu correo y la contraseña de aplicación en el `.env`:

```env
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion
```

#### ☁️ AWS S3 (para imágenes de perfil)

1. Crea una cuenta en [AWS](https://aws.amazon.com/).
2. Ve a **S3** y crea un bucket (por ejemplo: `djangoperfilimagenes2025`).
3. Ve a **IAM** y crea un usuario con permisos para S3.
4. Descarga el `AWS_ACCESS_KEY_ID` y el `AWS_SECRET_ACCESS_KEY`.
5. En el `.env` coloca:

```env
AWS_ACCESS_KEY_ID=tu_aws_key
AWS_SECRET_ACCESS_KEY=tu_aws_secret
AWS_S3_REGION_NAME=us-east-2
AWS_STORAGE_BUCKET_NAME=tu_bucket
```

> ℹ️ **Nota:** El nombre del bucket y la región deben coincidir exactamente con los de tu cuenta de AWS.

---

## ⬇️ Descarga del Modelo de IA

⬇️ Descarga el archivo del modelo desde el siguiente enlace de Google Drive y colócalo en la carpeta `static/model/`:

[Descargar modelo InceptionV3 (Google Drive)](https://drive.google.com/file/d/1D97tktwtWRs_7SpvgCzjrHl7cqdydZDX/view?usp=sharing)

El archivo debe llamarse exactamente:  
`inceptionv3.h5`

---

## ▶️ Ejecución de la Aplicación

### 1️⃣ Realiza las migraciones de la base de datos

```sh
python manage.py migrate
```

### 2️⃣ Crea un superusuario

```sh
python manage.py createsuperuser
```
Sigue las instrucciones en pantalla para establecer usuario y contraseña.

### 3️⃣ Inicia el servidor de desarrollo

```sh
python manage.py runserver
```

### 4️⃣ Accede a la aplicación

- Abre tu navegador y visita: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🖥️ Guía de Uso

1. **Inicia sesión** con tu cuenta de doctor o administrador.
2. **Registra un paciente** y completa su información.
3. **Sube una radiografía** desde el panel correspondiente.
4. **Espera el análisis automático** realizado por la IA.
5. **Consulta el diagnóstico** y el nivel de confianza.
6. **Descarga o envía el informe PDF** al paciente o a otros profesionales.
7. **Revisa el historial** y las estadísticas desde el panel administrativo.

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas!  
Para colaborar:

1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad o corrección (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m 'Agrega nueva funcionalidad'`).
4. Haz push a tu rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request describiendo tus cambios.

---

## 🛡️ Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).

---

## 📬 Contacto

¿Dudas, sugerencias o soporte?  
Escríbenos a:
-	jsanchezp20@unemi.edu.ec
-	esalvatierrav2@unemi.edu.ec
-	afloresm11@unemi.edu.ec
-	Steveeebarona1511@gmail.com
O contacta al equipo de desarrollo.

> ⚠️ **Nota:** NeumScan es un proyecto académico y no debe usarse en entornos clínicos reales sin la debida validación y certificación profesional.