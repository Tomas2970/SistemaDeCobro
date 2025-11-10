TYPE=TRIGGERS
triggers='CREATE DEFINER=`root`@`localhost` TRIGGER trg_detalle_compra_ai_total\nAFTER INSERT ON DetalleCompra\nFOR EACH ROW\nBEGIN\n  UPDATE Compra\n  SET total = (\n    SELECT COALESCE(SUM(subtotal),0)\n    FROM DetalleCompra\n    WHERE id_compra = NEW.id_compra\n  )\n  WHERE id_compra = NEW.id_compra;\nEND'
sql_modes=1073741824
definers='root@localhost'
client_cs_names='utf8mb4'
connection_cl_names='utf8mb4_uca1400_ai_ci'
db_cl_names='utf8mb4_unicode_ci'
created=1762702545687307
