# Despliegue simulado de NeumScan

Este procedimiento reproduce un despliegue local desde una carpeta externa al repositorio de desarrollo. No publica información clínica ni credenciales reales.

## Requisitos

- Docker Desktop con Docker Compose v2.
- Git.
- El archivo `inceptionv3.h5` descargado en `static/model/` si se va a utilizar el análisis de radiografías. La aplicación puede iniciar sin ese archivo; solo la función de análisis lo necesita.

## Pasos

1. Desde una carpeta externa, clonar el repositorio:

   ```bash
   git clone https://github.com/Jose2401jj/proyecto-final-Jose-Sanchez.git neumscan-deploy
   cd neumscan-deploy
   ```

2. Crear las variables locales y reemplazar la clave secreta:

   ```bash
   cp .env.example .env
   ```

3. Construir y levantar los servicios:

   ```bash
   docker compose up --build -d
   ```

4. Verificar que los servicios estén activos y abrir la aplicación en `http://localhost:8000`:

   ```bash
   docker compose ps
   docker compose logs -f web
   ```

5. Para detener la simulación conservando los datos de PostgreSQL:

   ```bash
   docker compose down
   ```

6. Para eliminar también los datos de la simulación:

   ```bash
   docker compose down -v
   ```

## Flujo automatizado

Cada `push` y cada pull request ejecuta el flujo de GitHub Actions: instala dependencias, corre las pruebas, construye la imagen Docker y valida la configuración de Docker Compose. El flujo adjunta un manifiesto de despliegue como artefacto para dejar evidencia del build.
