# Plugin Templates

Este directorio contiene templates y guías para crear nuevos plugins.

## Estado Actual

Los templates automatizados aún no están implementados. Esta documentación describe cómo crear plugins manualmente.

## Tipos de Plugins

El framework soporta tres tipos de plugins:

### OUTGOING (BaseSender)
Plugins que envían mensajes programados automáticamente.

**Características:**
- Configuración de schedule (interval, cron, date)
- Ejecución automática mediante APScheduler
- Gestión de destinatarios
- Logging y error handling automático

**Casos de uso:**
- Alertas periódicas
- Reportes programados
- Notificaciones automáticas

### INCOMING (BaseHandler)
Plugins que responden a comandos y mensajes de usuarios.

**Características:**
- CommandHandler para comandos
- MessageHandler para mensajes con filtros
- Procesamiento de argumentos
- Respuestas dinámicas

**Casos de uso:**
- Comandos de ayuda
- Herramientas interactivas
- Consultas de información

### HYBRID (BaseHybrid)
Plugins que combinan funcionalidad OUTGOING e INCOMING.

**Características:**
- Capacidades de envío programado
- Respuesta a comandos de usuario
- Gestión de jobs dinámicos
- Ideal para sistemas complejos

**Casos de uso:**
- Sistemas de recordatorios personalizados
- Alertas configurables por usuario
- Notificaciones dinámicas

## Crear un Plugin OUTGOING

### Estructura de Archivos

```
modules/outgoing/nombre_plugin/
├── __init__.py
└── nombre_plugin.py
```

### Código Base

```python
from typing import Dict, List
from modules.outgoing.base_sender import BaseSender


class NombrePlugin(BaseSender):
    """Descripción del plugin."""

    def get_schedule(self) -> Dict:
        """Configuración del schedule."""
        return {
            'trigger': 'interval',
            'minutes': 60  # Cada hora
        }

    async def send(self):
        """Lógica de envío del mensaje."""
        recipients = self.get_recipients()

        message = "Mensaje a enviar"

        for chat_id in recipients:
            await self.client.send_message(
                chat_id=chat_id,
                text=message
            )

    def get_recipients(self) -> List[int]:
        """Lista de destinatarios."""
        import os
        return [int(os.getenv('ADMIN_CHAT_ID'))]

    def get_plugin_name(self) -> str:
        """Nombre del directorio del plugin."""
        return "nombre_plugin"

    def get_description(self) -> str:
        """Descripción para el sistema."""
        return "Descripción del plugin"
```

### Archivo __init__.py

```python
from .nombre_plugin import NombrePlugin

__all__ = ['NombrePlugin']
```

### Registrar en main.py

Agregar al plugin_loader:

```python
if plugin_name == 'nombre_plugin' and plugin_class == 'NombrePlugin':
    from modules.outgoing.nombre_plugin.nombre_plugin import NombrePlugin
    return NombrePlugin(telegram_client, scheduler)
```

## Crear un Plugin INCOMING

### Estructura de Archivos

```
modules/incoming/nombre_plugin/
├── __init__.py
└── nombre_plugin.py
```

### Código Base

```python
from typing import Dict
from telegram import Update
from telegram.ext import ContextTypes
from modules.incoming.base_handler import BaseHandler


class NombrePlugin(BaseHandler):
    """Descripción del plugin."""

    def get_handler_type(self) -> str:
        """Tipo de handler."""
        return "command"  # o "message"

    def get_handler_config(self) -> Dict:
        """Configuración del handler."""
        return {
            'command': 'nombre',  # Para CommandHandler
            'description': 'Descripción del comando'
        }
        # O para MessageHandler:
        # return {
        #     'filters': filters.TEXT & ~filters.COMMAND
        # }

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lógica del handler."""
        args = context.args if context.args else []

        response = "Respuesta del bot"

        await update.effective_message.reply_text(response)

    def get_plugin_name(self) -> str:
        """Nombre del directorio del plugin."""
        return "nombre_plugin"

    def get_description(self) -> str:
        """Descripción para el sistema."""
        return "Descripción del plugin"
```

### Registrar en main.py

Agregar al plugin_loader:

```python
if plugin_name == 'nombre_plugin' and plugin_class == 'NombrePlugin':
    from modules.incoming.nombre_plugin.nombre_plugin import NombrePlugin
    return NombrePlugin(telegram_client, scheduler)
```

## Crear un Plugin HYBRID

### Estructura de Archivos

```
modules/hybrid/nombre_plugin/
├── __init__.py
└── nombre_plugin.py
```

### Código Base

```python
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes
from modules.hybrid.base_hybrid import BaseHybrid


class NombrePlugin(BaseHybrid):
    """Descripción del plugin."""

    # Métodos OUTGOING
    def get_schedule(self) -> Dict:
        return {
            'trigger': 'interval',
            'hours': 1
        }

    async def send(self):
        recipients = self.get_recipients()
        for chat_id in recipients:
            await self.client.send_message(
                chat_id=chat_id,
                text="Mensaje programado"
            )

    def get_recipients(self) -> List[int]:
        import os
        return [int(os.getenv('ADMIN_CHAT_ID'))]

    # Métodos INCOMING
    def get_handler_type(self) -> str:
        return "command"

    def get_handler_config(self) -> Dict:
        return {
            'command': 'nombre',
            'description': 'Descripción del comando'
        }

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text("Respuesta")

    # Método común
    def get_plugin_name(self) -> str:
        return "nombre_plugin"
```

## Tipos de Schedule

### Interval
```python
def get_schedule(self) -> Dict:
    return {
        'trigger': 'interval',
        'seconds': 30  # O minutes, hours, days
    }
```

### Cron
```python
def get_schedule(self) -> Dict:
    return {
        'trigger': 'cron',
        'hour': 9,
        'minute': 0,
        'day_of_week': 'mon-fri'
    }
```

### Date (una sola vez)
```python
from datetime import datetime, timedelta

def get_schedule(self) -> Dict:
    run_date = datetime.now() + timedelta(hours=1)
    return {
        'trigger': 'date',
        'run_date': run_date
    }
```

## Gestión de Plugins

Una vez creado, el plugin se puede gestionar desde Telegram:

```
/plugins                          # Listar todos
/plugins status NombrePlugin_job  # Ver estado
/plugins disable NombrePlugin_job # Desactivar
/plugins enable NombrePlugin_job  # Activar
```

## Mejores Prácticas

1. **Nombres descriptivos**: Usar nombres claros que indiquen la funcionalidad
2. **Documentación**: Agregar docstrings a todas las clases y métodos
3. **Error handling**: Usar los wrappers safe_execute cuando sea necesario
4. **Logging**: Usar self.logger para mensajes de debugging
5. **Configuración**: Usar variables de entorno para valores sensibles
6. **Validación**: Implementar validate_config() si hay requisitos especiales

## Ejemplos Existentes

### TestPlugin (OUTGOING)
Ubicación: modules/outgoing/tests/test_plugin.py
Funcionalidad: Envía mensaje de prueba cada 5 minutos

### PluginManagerCommand (INCOMING)
Ubicación: modules/incoming/plugin_manager/plugin_manager.py
Funcionalidad: Gestión completa de plugins via comando /plugins

## Pendiente de Implementación

- Script generador automático de plugins
- Templates con código boilerplate
- Validación automática de estructura
- Sistema de hot-reload para desarrollo
