---
name: test-driven-cobros
description: Fuerza al agente a escribir y ejecutar pruebas unitarias parametrizadas con Pytest para la lógica de MariaDB y CustomTkinter.
---

# Flujo de Testing Obligatorio en Modo BUILD

Al pasar a la fase BUILD, cada función de backend, consulta a MariaDB o componente de CustomTkinter DEBE ser validado inmediatamente mediante pruebas automatizadas.

## 1. Reglas para Lógica y MariaDB (Modelos y Consultas)
- **Aislamiento absoluto:** Todo test que interactúe con MariaDB debe usar una base de datos de pruebas o mocks. Queda prohibido alterar datos reales de desarrollo.
- **Uso de Fixtures:** Define fixtures de Pytest para inicializar conexiones limpias (`setup`) y cerrar transacciones (`teardown`) mediante Rollbacks.
- **Pruebas Parametrizadas:** Si se valida una función de cobro o cálculo de descuentos, utiliza `@pytest.mark.parametrize` para inyectar múltiples escenarios en un solo bloque de test (ej. probar valores normales, valores límite, strings vacíos y números negativos).

## 2. Reglas para CustomTkinter (Interfaz Gráfica)
- **No bloquear el agente:** Las ventanas de CustomTkinter (`ctk.CTk()`) no deben ejecutar `.mainloop()` durante los tests unitarios.
- **Actualizaciones manuales:** Utiliza `.update_idletasks()` y `.update()` en las fixtures para simular el ciclo de renderizado de los componentes gráficos sin congelar el entorno de ejecución.

## 3. Criterio de Aceptación
- No des por finalizado un cambio de código en modo BUILD hasta haber ejecutado el comando `pytest` en la terminal y verificado que el 100% de los casos de prueba parametrizados resulten exitosos.
