# Gabby's Tetris para Android

Esta carpeta contiene una aplicación Android separada del juego de escritorio. Conserva las reglas y la estética de Gabby's Tetris, con un tablero vertical que se ajusta a la pantalla y controles táctiles.

## Generar un APK de prueba

La compilación Android requiere Linux o macOS, Java 17, Buildozer y conexión a Internet para descargar el SDK y el NDK de Android. El primer armado puede tardar bastante porque descarga esas herramientas.

Desde esta carpeta, en un entorno Linux preparado para Android:

```bash
buildozer -v android debug
```

El APK de prueba aparecerá en `bin/`. Para instalarlo en un teléfono Android, copia el APK al dispositivo y ábrelo. Android puede pedir que autorices la instalación desde esa fuente.

También se puede compilar desde GitHub: abre **Actions**, elige **Build Android APK**, pulsa **Run workflow** y descarga el artefacto `gabbys-tetris-android-apk` cuando termine.

Para generar un paquete de publicación para una tienda, revisa la configuración de firma antes de crear el AAB:

```bash
buildozer -v android release
```

## Audio

Los archivos WAV de esta carpeta se generan desde `generate_audio.py`, usando la melodía y los efectos procedurales del juego original. La app permite silenciar la música y pausa la partida si Android la interrumpe cuando se cambia de aplicación.

La app usa el identificador `io.github.gabbyzamora80.gabbystetris`, la licencia GPL-3.0-only y compila para ARM64 y ARM32. La interfaz usa unidades adaptables de Kivy para acomodar distintas pantallas.
