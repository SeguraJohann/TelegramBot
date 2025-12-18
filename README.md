# Telegram Bot Framework

Framework modular para la creación de bots de Telegram con soporte para plugins de tres tipos: OUTGOING (programados), INCOMING (comandos) e HYBRID (mixtos).

## Características

- **Sistema de plugins modular**: Tres tipos de plugins con arquitectura extensible
- **Persistencia automática**: Configuración y estado guardados en JSON
- **Gestión dinámica**: Control completo de plugins desde Telegram
- **Scheduler integrado**: APScheduler para tareas programadas
- **Polling activo**: Recepción de mensajes y comandos en tiempo real
- **Error handling robusto**: Múltiples capas de protección y logging
- **Carga automática**: Restauración de plugins al reiniciar

## Requisitos

- Python 3.8+
- python-telegram-bot
- APScheduler
- python-dotenv

## Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd telegram-bot-repo

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu token y chat ID
```

## Configuración

Archivo `.env`:
```
TELEGRAM_BOT_TOKEN=tu_token_aqui
ADMIN_CHAT_ID=tu_chat_id
```

## Uso

```bash
python main.py
```

El bot iniciará y cargará todos los plugins activos desde `storage/`.

## Tipos de Plugins

### OUTGOING (BaseSender)
Plugins que envían mensajes programados automáticamente.

**Ejemplo**: Alertas periódicas, reportes automatizados

```python
from modules.outgoing.base_sender import BaseSender

class MiPlugin(BaseSender):
    def get_schedule(self) -> Dict:
        return {'trigger': 'interval', 'hours': 1}

    async def send(self):
        # Lógica de envío
        pass
```

### INCOMING (BaseHandler)
Plugins que responden a comandos y mensajes de usuarios.

**Ejemplo**: Comandos interactivos, herramientas

```python
from modules.incoming.base_handler import BaseHandler

class MiComando(BaseHandler):
    def get_handler_type(self) -> str:
        return "command"

    async def handle(self, update, context):
        # Lógica del comando
        pass
```

### HYBRID (BaseHybrid)
Plugins que combinan ambas funcionalidades.

**Ejemplo**: Sistemas de recordatorios configurables

```python
from modules.hybrid.base_hybrid import BaseHybrid

class MiHibrido(BaseHybrid):
    # Implementar métodos de ambos tipos
    pass
```

## Gestión de Plugins

Comando `/plugins` disponible desde Telegram:

```
/plugins                    # Listar todos los plugins
/plugins status <job_id>    # Ver estado detallado
/plugins enable <job_id>    # Activar plugin
/plugins disable <job_id>   # Desactivar plugin
```

Los cambios persisten entre reinicios del bot.

## Estructura del Proyecto

```
telegram-bot-repo/
├── main.py                 # Punto de entrada
├── core/                   # Componentes centrales
│   ├── telegram/           # Cliente de Telegram
│   └── scheduler/          # Gestor de tareas
├── modules/                # Sistema de plugins
│   ├── base/               # Clase base
│   ├── outgoing/           # Plugins programados
│   ├── incoming/           # Plugins de comandos
│   ├── hybrid/             # Plugins mixtos
│   └── storage/            # Sistema de persistencia
├── storage/                # Datos de plugins (JSON)
├── templates/              # Guías para crear plugins
└── logs/                   # Logs del bot
```

## Crear Nuevos Plugins

Ver documentación completa en `templates/README.md`

### Pasos básicos:

1. Crear directorio en `modules/<tipo>/<nombre>/`
2. Implementar clase heredando de la base correspondiente
3. Agregar al `plugin_loader` en `main.py`
4. Reiniciar el bot

## Plugins Incluidos

### TestPlugin (OUTGOING)
Plugin de prueba que envía mensajes cada 5 minutos.

**Ubicación**: `modules/outgoing/tests/test_plugin.py`

### PluginManagerCommand (INCOMING)
Sistema de gestión de plugins via comando `/plugins`.

**Ubicación**: `modules/incoming/plugin_manager/plugin_manager.py`

## Persistencia

Los plugins se guardan automáticamente en `storage/` como archivos JSON:

```json
{
  "job_id": "TestPlugin_job",
  "plugin_type": "outgoing",
  "plugin_name": "tests",
  "plugin_class": "TestPlugin",
  "schedule": {
    "trigger": "interval",
    "minutes": 5
  },
  "metadata": {
    "description": "Plugin de prueba",
    "active": true,
    "created_at": "2025-12-17T20:00:00",
    "execution_count": 0,
    "last_execution": null,
    "error_count": 0
  }
}
```

## Desarrollo

### Arquitectura

El framework utiliza varios patrones de diseño:

- **Template Method**: En BasePlugin para flujos consistentes
- **Strategy**: En configuración de schedules
- **Repository**: En JobStorage para persistencia
- **Dependency Injection**: En constructores de plugins

### Logging

El sistema usa logging estándar de Python. Los logs incluyen:
- Registro de ejecuciones de plugins
- Errores y excepciones
- Estado del scheduler
- Mensajes de Telegram procesados

### Error Handling

Múltiples capas de protección:
- Wrappers en BasePlugin (`safe_execute`, `safe_execute_async`)
- Try-catch en métodos críticos
- Logging automático de errores
- Metadata de error_count

## Roadmap

- [ ] Templates automatizados de plugins
- [ ] Sistema de logging a archivos
- [ ] Sincronización de metadatos a disco
- [ ] Tests unitarios
- [ ] Migración a SQLite (para escalar)
- [ ] Sistema de backups automáticos
- [ ] Hot-reload de plugins

## Licencia

[Definir licencia]

## Contribución

[Definir guías de contribución]
