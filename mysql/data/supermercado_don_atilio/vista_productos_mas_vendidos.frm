TYPE=VIEW
query=select `p`.`id_producto` AS `id_producto`,`p`.`nombre` AS `nombre`,`p`.`precio` AS `precio`,`c`.`nombre` AS `categoria`,sum(`dv`.`cantidad`) AS `total_vendido`,sum(`dv`.`subtotal`) AS `ingresos_generados` from (((`supermercado_don_atilio`.`producto` `p` join `supermercado_don_atilio`.`detalleventa` `dv` on(`p`.`id_producto` = `dv`.`id_producto`)) join `supermercado_don_atilio`.`venta` `v` on(`dv`.`id_venta` = `v`.`id_venta`)) left join `supermercado_don_atilio`.`categoria` `c` on(`p`.`id_categoria` = `c`.`id_categoria`)) where `v`.`estado` = \'completada\' and `p`.`activo` = 1 group by `p`.`id_producto` order by sum(`dv`.`cantidad`) desc
md5=9c6f78ec1668f8ff2623270c60dc0b18
updatable=0
algorithm=0
definer_user=root
definer_host=localhost
suid=2
with_check_option=0
timestamp=0001762702545770855
create-version=2
source=SELECT\n  p.id_producto,\n  p.nombre,\n  p.precio,\n  c.nombre AS categoria,\n  SUM(dv.cantidad) AS total_vendido,\n  SUM(dv.subtotal) AS ingresos_generados\nFROM Producto p\nJOIN DetalleVenta dv ON p.id_producto = dv.id_producto\nJOIN Venta v ON dv.id_venta = v.id_venta\nLEFT JOIN Categoria c ON p.id_categoria = c.id_categoria\nWHERE v.estado = \'completada\' AND p.activo = 1\nGROUP BY p.id_producto\nORDER BY total_vendido DESC
client_cs_name=utf8mb4
connection_cl_name=utf8mb4_uca1400_ai_ci
view_body_utf8=select `p`.`id_producto` AS `id_producto`,`p`.`nombre` AS `nombre`,`p`.`precio` AS `precio`,`c`.`nombre` AS `categoria`,sum(`dv`.`cantidad`) AS `total_vendido`,sum(`dv`.`subtotal`) AS `ingresos_generados` from (((`supermercado_don_atilio`.`producto` `p` join `supermercado_don_atilio`.`detalleventa` `dv` on(`p`.`id_producto` = `dv`.`id_producto`)) join `supermercado_don_atilio`.`venta` `v` on(`dv`.`id_venta` = `v`.`id_venta`)) left join `supermercado_don_atilio`.`categoria` `c` on(`p`.`id_categoria` = `c`.`id_categoria`)) where `v`.`estado` = \'completada\' and `p`.`activo` = 1 group by `p`.`id_producto` order by sum(`dv`.`cantidad`) desc
mariadb-version=120002
