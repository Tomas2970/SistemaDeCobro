TYPE=VIEW
query=select cast(`v`.`fecha` as date) AS `fecha`,count(`v`.`id_venta`) AS `total_ventas`,sum(`v`.`total`) AS `monto_total` from `supermercado_don_atilio`.`venta` `v` where `v`.`estado` = \'completada\' group by cast(`v`.`fecha` as date) order by cast(`v`.`fecha` as date) desc
md5=a3a7209051b68200dbd0ea6c7daa0b94
updatable=0
algorithm=0
definer_user=root
definer_host=localhost
suid=2
with_check_option=0
timestamp=0001762702545762360
create-version=2
source=SELECT\n  DATE(v.fecha) AS fecha,\n  COUNT(v.id_venta) AS total_ventas,\n  SUM(v.total) AS monto_total\nFROM Venta v\nWHERE v.estado = \'completada\'\nGROUP BY DATE(v.fecha)\nORDER BY fecha DESC
client_cs_name=utf8mb4
connection_cl_name=utf8mb4_uca1400_ai_ci
view_body_utf8=select cast(`v`.`fecha` as date) AS `fecha`,count(`v`.`id_venta`) AS `total_ventas`,sum(`v`.`total`) AS `monto_total` from `supermercado_don_atilio`.`venta` `v` where `v`.`estado` = \'completada\' group by cast(`v`.`fecha` as date) order by cast(`v`.`fecha` as date) desc
mariadb-version=120002
