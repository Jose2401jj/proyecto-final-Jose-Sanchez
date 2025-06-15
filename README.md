# 🩺 NeumScan

**Sistema Inteligente para el Análisis Automatizado de Radiografías Pulmonares**

## 📑 Tabla de Contenidos

- [👥 Integrantes](#-integrantes)
- [📝 Descripción General](#-descripción-general)
- [✨ Características Destacadas](#-características-destacadas)
- [⚙️ Requisitos Previos](#️-requisitos-previos)
- [🚀 Instalación Paso a Paso](#-instalación-paso-a-paso)
- [🔧 Configuración Inicial](#-configuración-inicial)
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

- Python 3.8 o superior
- Git
- pip
- (Opcional) Entorno virtual: `venv` o `virtualenv`
- (Opcional) Docker (para despliegue en contenedores)
- Credenciales de servicios externos (Google, correo, etc.)

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
pip install -r requirements.txt
```

## 🔧 Configuración Inicial

### 4️⃣ Configura las variables de entorno

- Copia el archivo `.env.example` a `.env`:
  ```sh
  copy .env.example .env  # En Windows
  cp .env.example .env    # En Mac/Linux
  ```
- Completa los valores requeridos en el archivo `.env` (credenciales, claves secretas, etc).

### 5️⃣ Realiza las migraciones de la base de datos

```sh
python manage.py migrate
```

### 6️⃣ Crea un superusuario

```sh
python manage.py createsuperuser
```
Sigue las instrucciones en pantalla para establecer usuario y contraseña.

## ▶️ Ejecución de la Aplicación

### 7️⃣ Inicia el servidor de desarrollo

```sh
python manage.py runserver
```

### 8️⃣ Accede a la aplicación

- Abre tu navegador y visita: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 🖥️ Guía de Uso

1. **Inicia sesión** con tu cuenta de doctor o administrador.
2. **Registra un paciente** y completa su información.
3. **Sube una radiografía** desde el panel correspondiente.
4. **Espera el análisis automático** realizado por la IA.
5. **Consulta el diagnóstico** y el nivel de confianza.
6. **Descarga o envía el informe PDF** al paciente o a otros profesionales.
7. **Revisa el historial** y las estadísticas desde el panel administrativo.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas!  
Para colaborar:

1. Haz un fork del repositorio.
2. Crea una rama para tu funcionalidad o corrección (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m 'Agrega nueva funcionalidad'`).
4. Haz push a tu rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request describiendo tus cambios.

## 🛡️ Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).

## 📬 Contacto

¿Dudas, sugerencias o soporte?  
Escríbenos a:
-	jsanchezp20@unemi.edu.ec
-	esalvatierrav2@unemi.edu.ec
-	afloresm11@unemi.edu.ec
-	Steveeebarona1511@gmail.com
O contacta al equipo de desarrollo.

> ⚠️ **Nota:** NeumScan es un proyecto académico y no debe usarse en entornos clínicos reales sin la debida validación y certificación profesional.
