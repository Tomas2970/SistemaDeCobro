class cliente:
    def __init__(self, nombre,direccion,telefono,email):
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.email = email
        id_cliente = int
        saldo = 0.0
class servicio_cliente:
    def registro_cliente():
        #Logica para el registro de cliente
        nombre = str
        direccion = str
        telefono = int
        email = str
        
        if not nombre:
            raise ValueError("El nombre es obligatorio.")
        if not telefono.isdigit() or len(telefono) < 8:
            raise ValueError("Telefono inválido.")
        if "@" not in email:
            raise ValueError("Email debe contener @")
        cliente_actual = cliente(nombre.strip(),direccion.strip(),telefono,email.strip())
        return cliente_actual

    def ajustar_saldo(cliente, monto):
        #Modificar saldo de cliente
        if not isinstance(monto, (int,float)):
            raise TypeError("El monto debe ser numérico.")
        cliente.saldo += monto
