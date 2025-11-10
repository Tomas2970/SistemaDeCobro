TYPE=TRIGGERS
triggers='CREATE DEFINER=`root`@`localhost` TRIGGER trg_venta_au_cuentacorriente\nAFTER UPDATE ON Venta\nFOR EACH ROW\nBEGIN\n  IF NEW.id_cliente IS NOT NULL THEN\n    IF NEW.tipo_pago = \'cuenta_corriente\' AND OLD.tipo_pago <> \'cuenta_corriente\' THEN\n      UPDATE CuentaCorriente\n      SET saldo = saldo - NEW.total \n      WHERE id_cliente = NEW.id_cliente;\n    ELSEIF NEW.tipo_pago = \'cuenta_corriente\' AND NEW.total <> OLD.total THEN\n      UPDATE CuentaCorriente\n      SET saldo = saldo - (NEW.total - OLD.total) \n      WHERE id_cliente = NEW.id_cliente;\n    ELSEIF OLD.tipo_pago = \'cuenta_corriente\' AND NEW.tipo_pago <> \'cuenta_corriente\' THEN\n      UPDATE CuentaCorriente\n      SET saldo = saldo + OLD.total \n      WHERE id_cliente = NEW.id_cliente;\n    END IF;\n  END IF;\nEND'
sql_modes=1073741824
definers='root@localhost'
client_cs_names='utf8mb4'
connection_cl_names='utf8mb4_uca1400_ai_ci'
db_cl_names='utf8mb4_unicode_ci'
created=1762702545730181
