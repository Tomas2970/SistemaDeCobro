TYPE=VIEW
query=select `c`.`id_cliente` AS `id_cliente`,`c`.`nombre` AS `nombre`,`c`.`dni` AS `dni`,`c`.`telefono` AS `telefono`,`c`.`email` AS `email`,`cc`.`saldo` AS `saldo`,`cc`.`limite_credito` AS `limite_credito`,`cc`.`limite_credito` + `cc`.`saldo` AS `credito_disponible` from (`supermercado_don_atilio`.`cliente` `c` join `supermercado_don_atilio`.`cuentacorriente` `cc` on(`c`.`id_cliente` = `cc`.`id_cliente`)) where `cc`.`saldo` < 0 and `c`.`activo` = 1 order by `cc`.`saldo`
md5=702e98dea656158e1d92ab518169de76
updatable=1
algorithm=0
definer_user=root
definer_host=localhost
suid=2
with_check_option=0
timestamp=0001762702545779489
create-version=2
source=SELECT\n  c.id_cliente,\n  c.nombre,\n  c.dni,\n  c.telefono,\n  c.email,\n  cc.saldo,\n  cc.limite_credito,\n  (cc.limite_credito + cc.saldo) AS credito_disponible\nFROM Cliente c\nJOIN CuentaCorriente cc ON c.id_cliente = cc.id_cliente\nWHERE cc.saldo < 0 AND c.activo = 1\nORDER BY cc.saldo ASC
client_cs_name=utf8mb4
connection_cl_name=utf8mb4_uca1400_ai_ci
view_body_utf8=select `c`.`id_cliente` AS `id_cliente`,`c`.`nombre` AS `nombre`,`c`.`dni` AS `dni`,`c`.`telefono` AS `telefono`,`c`.`email` AS `email`,`cc`.`saldo` AS `saldo`,`cc`.`limite_credito` AS `limite_credito`,`cc`.`limite_credito` + `cc`.`saldo` AS `credito_disponible` from (`supermercado_don_atilio`.`cliente` `c` join `supermercado_don_atilio`.`cuentacorriente` `cc` on(`c`.`id_cliente` = `cc`.`id_cliente`)) where `cc`.`saldo` < 0 and `c`.`activo` = 1 order by `cc`.`saldo`
mariadb-version=120002
