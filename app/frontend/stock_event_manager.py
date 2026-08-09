# app/frontend/stock_event_manager.py
"""
Sistema de eventos para notificar cambios en el stock.
Permite que las interfaces notifiquen al menú principal cuando ocurren cambios.
"""

class StockEventManager:
    """Gestor singleton de eventos de stock"""
    
    _instance = None
    _callbacks = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockEventManager, cls).__new__(cls)
            cls._instance._callbacks = []
        return cls._instance
    
    def suscribir(self, callback):
        """
        Suscribe una función callback que será llamada cuando cambie el stock.
        
        Args:
            callback: Función sin parámetros que se ejecutará al notificar
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def desuscribir(self, callback):
        """Remueve un callback de la lista de suscriptores"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def notificar_cambio_stock(self):
        """
        Notifica a todos los suscriptores que hubo un cambio en el stock.
        Debe ser llamado después de:
        - Registrar una venta
        - Registrar una compra
        - Modificar un producto (ABM)
        - Actualizar stock desde inventario
        """
        import tkinter as tk
        for callback in self._callbacks[:]:  # Iterar sobre copia para permitir desuscripción durante iteración
            try:
                callback()
            except tk.TclError:
                # Widget destruido: desuscribir automáticamente
                try:
                    self._callbacks.remove(callback)
                except ValueError:
                    pass
            except Exception as e:
                print(f"Error ejecutando callback de stock: {e}")
    
    def limpiar(self):
        """Limpia todos los callbacks (útil al cerrar la aplicación)"""
        self._callbacks.clear()


# Instancia global para uso en toda la aplicación
stock_events = StockEventManager()