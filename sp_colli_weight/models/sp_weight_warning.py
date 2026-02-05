from odoo import api, fields, models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sp_missing_weight = fields.Boolean(
        compute="_compute_sp_missing_weight",
        store=False,
        help="Vero se l'UoM non è di peso (es. PZ) e il prodotto non ha il campo Peso valorizzato.",
    )
    sp_weight_warning = fields.Char(
        compute="_compute_sp_missing_weight",
        store=False,
    )

    @api.depends("product_id", "product_id.weight", "product_uom_id", "product_uom_qty", "display_type")
    def _compute_sp_missing_weight(self):
        kg_uom = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False) or self.env.ref("uom.product_uom_kg", raise_if_not_found=False)
        for line in self:
            if line.display_type:
                line.sp_missing_weight = False
                line.sp_weight_warning = False
                continue

            missing = False
            msg = False

            if line.product_id and line.product_uom_id and kg_uom:
                # Se la UoM è convertibile in KG => UoM di peso (kg/g), quindi no warning
                is_weight_uom = True
                try:
                    line.product_uom_id._compute_quantity(1.0, kg_uom, round=False)
                except Exception:
                    is_weight_uom = False

                # Se NON è UoM peso (es. PZ), allora serve product.weight
                if not is_weight_uom and float(line.product_id.weight or 0.0) <= 0.0:
                    missing = True
                    msg = "ATTENZIONE: U.M. non a peso (es. PZ) ma il prodotto non ha 'Peso' (kg/pezzo). Il Totale Peso (KG) risulterà 0."

            line.sp_missing_weight = missing
            line.sp_weight_warning = msg
