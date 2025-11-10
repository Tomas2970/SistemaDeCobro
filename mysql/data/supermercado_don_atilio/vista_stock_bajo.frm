TYPE=VIEW
query=select `p`.`id_producto` AS `id_producto`,`p`.`nombre` AS `nombre`,`p`.`precio` AS `precio`,`p`.`es_pesable` AS `es_pesable`,`c`.`nombre` AS `categoria`,`i`.`cantidad` AS `cantidad`,`i`.`stock_minimo` AS `stock_minimo`,`i`.`stock_minimo` - `i`.`cantidad` AS `unidades_faltantes` from ((`supermercado_don_atilio`.`producto` `p` join `supermercado_don_atilio`.`inventario` `i` on(`p`.`id_producto` = `i`.`id_producto`)) left join `supermercado_don_atilio`.`categoria` `c` on(`p`.`id_categoria` = `c`.`id_categoria`)) where `i`.`cantidad` <= `i`.`stock_minimo` and `p`.`activo` = 1 order by `i`.`cantidad`
md5=4cd44a13f44497b8b9f7a7a73232e02d
updatable=0
algorithm=0
definer_user=root
definer_host=localhost
suid=2
with_check_option=0
timestamp=0001762702545750512
create-version=2
source=SELECT\n  p.id_producto,\n  p.nombre,\n  p.precio,\n  p.es_pesable,\n  c.nombre AS categoria,\n  i.cantidad,\n  i.stock_minimo,\n  (i.stock_minimo - i.cantidad) AS unidades_faltantes\nFROM Producto p\nJOIN Inventario i ON p.id_producto = i.id_producto\nLEFT JOIN Categoria c ON p.id_categoria = c.id_categoria\nWHERE i.cantidad <= i.stock_minimo AND p.activo = 1\nORDER BY i.cantidad ASC
client_cs_name=utf8mb4
connection_cl_name=utf8mb4_uca1400_ai_ci
view_body_utf8=select `p`.`id_producto` AS `id_producto`,`p`.`nombre` AS `nombre`,`p`.`precio` AS `precio`,`p`.`es_pesable` AS `es_pesable`,`c`.`nombre` AS `categoria`,`i`.`cantidad` AS `cantidad`,`i`.`stock_minimo` AS `stock_minimo`,`i`.`stock_minimo` - `i`.`cantidad` AS `unidades_faltantes` from ((`supermercado_don_atilio`.`producto` `p` join `supermercado_don_atilio`.`inventario` `i` on(`p`.`id_producto` = `i`.`id_producto`)) left join `supermercado_don_atilio`.`categoria` `c` on(`p`.`id_categoria` = `c`.`id_categoria`)) where `i`.`cantidad` <= `i`.`stock_minimo` and `p`.`activo` = 1 order by `i`.`cantidad`
mariadb-version=120002
