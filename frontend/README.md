# Frontend estático para Vercel

Este directorio contiene la versión estática de la interfaz de usuario que puede desplegarse en Vercel.

## Qué contiene

- `index.html`: página principal estática.
- `css/styles.css`: estilos compartidos.
- `js/app.js`: lógica del cliente, ahora configurada para consumir una API externa.
- `logo.svg`: icono de la aplicación.
- `vercel.json`: configuración de Vercel para servir la SPA desde el directorio.

## Cómo usar

1. En `index.html`, actualiza:

```html
<script>
    window.API_BASE_URL = "https://tu-backend.com";
</script>
```

2. Despliega el directorio `frontend/` en Vercel como un sitio estático.
3. Asegúrate de que tu backend Flask esté desplegado y acepte CORS desde el dominio de Vercel.
4. Configura el backend con Supabase PostgreSQL usando la variable de entorno `DATABASE_URL`.

## Requisitos para el backend

En el backend debes configurar:

- `DATABASE_URL`: URL de Supabase Postgres.
- `SECRET_KEY`: valor seguro.
- `CORS_ALLOWED_ORIGINS`: dominio de Vercel, por ejemplo `https://mi-app.vercel.app`.
- `SESSION_COOKIE_SAMESITE=None`
- `SESSION_COOKIE_SECURE=True` en producción HTTPS.

## Notas

- El backend sigue siendo Python/Flask y maneja la validación de gramaticas, autenticación y el historial.
- Supabase actúa como base de datos, no como hosting del backend Python.
