# model.py

class cobro:
    def __init__(self,
                 id, fecha, nombreCompleto, numParcela,
                 imputacion1, concepto1, fecha1, importeBruto1,
                 imputacion2, concepto2, fecha2, importeBruto2,
                 imputacion3, concepto3, fecha3, importeBruto3,
                 numCuentaA, montoA, numCuentaB, montoB,
                 impuestoDBCRb, anticipoIIBB, iva, observaciones):
        # claves de la tupla: 0..19
        self.id = id
        self.fecha = fecha
        self.nombreCompleto = nombreCompleto
        self.numParcela = numParcela
        self.imputacion1 = imputacion1
        self.concepto1 = concepto1
        self.fecha1 = fecha1
        self.importeBruto1 = importeBruto1
        self.imputacion2 = imputacion2
        self.concepto2 = concepto2
        self.fecha2 = fecha2
        self.importeBruto2 = importeBruto2
        self.imputacion3 = imputacion3
        self.concepto3 = concepto3
        self.fecha3 = fecha3
        self.importeBruto3 = importeBruto3
        self.numCuentaA = numCuentaA
        self.montoA = montoA
        self.numCuentaB = numCuentaB
        self.montoB = montoB
        self.impuestoDBCRb = impuestoDBCRb
        self.anticipoIIBB = anticipoIIBB
        self.iva = iva
        self.observaciones = observaciones

    def __str__(self):
        return (
            f"Cobro(id={self.id}, fecha={self.fecha}, pagador={self.nombreCompleto}, "
            f"parcela={self.numParcela}, "
            f"[{self.imputacion1},{self.concepto1},{self.fecha1},{self.importeBruto1}], "
            f"[{self.imputacion2},{self.concepto2},{self.fecha2},{self.importeBruto2}], "
            f"[{self.imputacion3},{self.concepto3},{self.fecha3},{self.importeBruto3}], "
            f"CuentaA={self.numCuentaA}, MontoA={self.montoA}, "
            f"CuentaB={self.numCuentaB}, MontoB={self.montoB}, "
            f"DByCRbBnc={self.impuestoDBCRb}, IIBB={self.anticipoIIBB}, IVA={self.iva}, "
            f"Obs={self.observaciones})"
        )


class pago:
    def __init__(self,
                 id, fecha, razonSocial, concepto, tipoComprobante,
                 numCuenta, montoNeto, iva, cuentaAcreditar, impuestoDBCRb):
        # claves de la tupla: 0..8
        self.id = id
        self.fecha = fecha
        self.razonSocial = razonSocial
        self.concepto = concepto
        self.tipoComprobante = tipoComprobante
        self.numCuenta = numCuenta
        self.montoNeto = montoNeto
        self.iva = iva
        self.cuentaAcreditar = cuentaAcreditar
        self.impuestoDBCRb = impuestoDBCRb

    def __str__(self):
        return (
            f"Pago(id={self.id}, fecha={self.fecha}, razón={self.razonSocial}, "
            f"tipoComp={self.tipoComprobante}, cuenta={self.numCuenta}, neto={self.montoNeto}, "
            f"IVA={self.iva}, acreditada={self.cuentaAcreditar}, DByCRbBnc={self.impuestoDBCRb})"
        )


class cliente:
    def __init__(self, id, nombreCompleto, DNI, direccion,
                 telefono1, telefono2, email,
                 parcela1, parcela2, parcela3, superficie, observaciones):
        # claves de la tupla: 0..11
        self.id = id
        self.nombreCompleto = nombreCompleto
        self.DNI = DNI
        self.direccion = direccion
        self.telefono1 = telefono1
        self.telefono2 = telefono2
        self.email = email
        self.parcela1 = parcela1
        self.parcela2 = parcela2
        self.parcela3 = parcela3
        self.superficie = superficie
        self.observaciones = observaciones

    def __str__(self):
        return (
            f"Cliente(id={self.id}, nombre={self.nombreCompleto}, "
            f"DNI={self.DNI}, dir={self.direccion}, t1={self.telefono1}, t2={self.telefono2}, "
            f"email={self.email}, parcelas=[{self.parcela1},{self.parcela2},{self.parcela3}], "
            f"superficie={self.superficie}, obs={self.observaciones})"
        )
