---
name: testing-python
description: Habilita la capacidad de ejecutar y estructurar pruebas unitarias con Pytest en entornos de Python.
---

# Capacidad Técnica: Pytest Automation

El agente tiene permitido usar la consola local para ejecutar suites de pruebas automatizadas mediante el comando `pytest`.

## Directrices de Ejecución
- Cada vez que se genere o modifique lógica de código, se debe verificar su integridad ejecutando `pytest` en la terminal.
- Se deben capturar los errores del output de la consola de Pytest para corregir bugs de inmediato en la fase BUILD.
- Se priorizará el uso de aserciones (`assert`) claras y el manejo de excepciones estándar de Python.
