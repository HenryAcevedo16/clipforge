# Servidor de IA de NovoClip (IA incluida)

Este servidor guarda **tu** clave de Gemini (los usuarios nunca la ven), comprueba la licencia de cada
usuario y limita cuántas peticiones de IA puede hacer al día. Cada clip usa unas 3-4 peticiones.

## Arrancarlo
```
pip install -r requirements.txt
set GEMINI_API_KEY=tu_clave_de_gemini
python server.py
```
Escucha en el puerto 8800. Para que tus clientes lleguen a él tiene que estar en un servidor con dirección
pública (un VPS barato basta: no necesita GPU, solo reenvía peticiones a Gemini).

## Licencias
Edita `licencias.json` (se relee en cada petición, no hace falta reiniciar):
```
"CLAVE-QUE-LE-DAS-AL-CLIENTE": {"name": "Juan", "plan": "pro", "daily_limit": 300, "expires": "2027-01-31", "active": true}
```
Para dar de baja a alguien: `"active": false`.

## En la app
En `ia_incluida.json` (junto a app.py) pon `"proxy_url": "https://tu-servidor:8800"` y deja `gemini_key` vacío.
Cada usuario pega su clave de licencia en la app, en "IA incluida".
