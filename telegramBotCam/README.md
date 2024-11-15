# Instalación
Para sistema Linux! 

Clonar el repositorio **(git clone)**, e ingresar en el directorio.

Primero que todo **INSTALAR PYTHON** !

Crear el entorno en python:

```bash
pip install virtualenv
python -m venv env
source env/bin/activate
```

Crear archivo **.env** y completar las siguientes variables de entorno:

```bash
BOT_TOKEN=XXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
CHAT_ID=000000000
#IP_CAMERA=192.168.0.157:8080
GOOGLE_APPLICATION_CREDENTIALS=/../service_account_credential.json
```

Instalar dependencias de **requeriments.txt**
```bash
pip install -r requirements.txt
```

Debe instalar el programa [**IP Webcam**](https://play.google.com/store/apps/details?id=com.pas.webcam&hl=es&gl=US&pli=1) en un celular android antiguo, que no se utilice o tener una camara IP, de aqui tomar la IP y actualizar la variable de entorno **IP_CAMERA**.

Correr el programa:
```bash
python main.py
```

## Uso
Listado de comandos para el bot:  
**/foto** Toma una fotografia y la envia al chat.    
**/video**  Captura un video y lo envia al chat (duración del video configurable).  
**/agrega** Agrega elementos a detectar en la vigilancia (gatos, perros, automoviles) por defecto solo personas.  
**/start** Inicia vigilancia, cuando detecta algun elemento, lo envia al Chat y a GCP (configurable).  
**/stop** Detiene la vigilancia.  


## License

[MIT](https://choosealicense.com/licenses/mit/)