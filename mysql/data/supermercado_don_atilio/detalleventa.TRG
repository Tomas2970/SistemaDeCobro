TYPE=TRIGGERS
triggers='CREATE DEFINER=`root`@`localhost` TRIGGER trg_detalle_venta_ai_total\nAFTER INSERT ON DetalleVenta\nFOR EACH ROW\nBEGIN\n  UPDATE Venta\n  SET total = (\n    SELECT COALESCE(SUM(subtotal),0)\n    FROM DetalleVenta\n    WHERE id_venta = NEW.id_venta\n  )\n  WHERE id_venta = NEW.id_venta;\nEND' 'CREATE DEFINER=`root`@`localhost` TRIGGER trg_auditoria_venta_inventario\nAFTER INSERT ON DetalleVenta\nFOR EACH ROW\nBEGIN\n  DECLARE v_cant_anterior DECIMAL(10, 3) DEFAULT 0.000; \n  IF NEW.id_producto IS NOT NULL THEN\n    SELECT cantidad INTO v_cant_anterior\n    FROM Inventario WHERE id_producto = NEW.id_producto;\n    INSERT INTO AuditoriaInventario\n      (id_producto, cantidad_anterior, cantidad_nueva, tipo_movimiento, id_referencia, id_usuario)\n    VALUES\n      (NEW.id_producto, v_cant_anterior, GREATEST(v_cant_anterior - NEW.cantidad, 0), \'venta\', NEW.id_venta, NULL);\n  END IF;\nEND'
sql_modes=1073741824 1073741824
definers='root@localhost' 'root@localhost'
client_cs_names='utf8mb4' 'utf8mb4'
connection_cl_names='utf8mb4_uca1400_ai_ci' 'utf8mb4_uca1400_ai_ci'
db_cl_names='utf8mb4_unicode_ci' 'utf8mb4_unicode_ci'
created=1762702545671286 1762702545700576
