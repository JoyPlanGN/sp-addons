from odoo import api, fields, models


def _sp_line_weight_kg(env, qty, uom, product):
    """
    Peso riga in KG:
    - se UoM è di tipo 'weight' => converte qty in KG (kgm)
    - altrimenti => qty è "unità/pezzi" => usa peso prodotto (kg) * qty
    """
    qty = qty or 0.0
    kg_uom = env.ref("uom.product_uom_kgm", raise_if_not_found=False)

    # 1) Se UoM è peso, converto a KG
    if uom and kg_uom:
        cat = getattr(uom, "category_id", None)
        mtype = getattr(cat, "measure_type", None) if cat else None
        if mtype == "weight":
            return uom._compute_quantity(qty, kg_uom)

    # 2) Altrimenti: considero qty come pezzi
    # peso standard Odoo è in KG (su product.template e/o product.product)
    weight = 0.0
    if product:
        weight = (
            getattr(product, "weight", 0.0)
            or getattr(getattr(product, "product_tmpl_id", None), "weight", 0.0)
            or getattr(getattr(product, "product_variant_id", None), "weight", 0.0)
        ) or 0.0

    return weight * qty

    kg_uom = env.ref("uom.product_uom_kgm", raise_if_not_found=False) or env.ref("uom.product_uom_kg", raise_if_not_found=False)

    if uom and kg_uom:
        # Prova conversione verso KG: se funziona, l'UoM è di PESO.
        # Se fallisce, è un'altra categoria (es. Unità/PZ) e useremo product.weight.
        try:
            return uom._compute_quantity(qty, kg_uom, round=False)
        except Exception:
            pass

    weight = float(getattr(product, "weight", 0.0) or 0.0) if product else 0.0
    return qty * weight
# -------------------------
# SALE
# -------------------------
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    sp_colli_qty = fields.Integer(string="Colli", default=0)

    sp_weight_line_kg = fields.Float(
        string="Peso riga (KG)",
        compute="_compute_sp_weight_line_kg",
        inverse="_inverse_sp_weight_line_kg",
        store=True,
        digits="Product Unit of Measure",
        help="Peso riga in KG. Calcolato automaticamente ma modificabile per casi reali (peso variabile).",
    )

    sp_weight_manual = fields.Boolean(
        string="Peso manuale",
        default=False,
        help="Se attivo, il peso riga non viene ricalcolato automaticamente cambiando qty/prodotto/UoM.",
    )

    @api.depends("product_uom_qty", "product_uom_id", "product_id", "product_id.weight", "sp_weight_manual")
    def _compute_sp_weight_line_kg(self):
        kg_uom = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False)
        for line in self:
            if line.display_type:
                line.sp_weight_line_kg = 0.0
                continue
            if line.sp_weight_manual:
                # non ricalcolare se l'utente ha messo peso manuale
                continue

            qty = float(line.product_uom_qty or 0.0)
            # Se la UoM è proprio "kgm" (kg), peso = qty
            if kg_uom and line.product_uom_id and line.product_uom_id.id == kg_uom.id:
                line.sp_weight_line_kg = qty
            else:
                # altrimenti: trattiamo come pezzi => qty * peso prodotto (kg)
                w = float(line.product_id.weight or 0.0) if line.product_id else 0.0
                line.sp_weight_line_kg = qty * w

    def _inverse_sp_weight_line_kg(self):
        # se l'utente scrive un peso manuale, blocchiamo il ricalcolo automatico
        for line in self:
            if not line.display_type:
                line.sp_weight_manual = True

    sp_colli_qty = fields.Integer(string="Colli", default=0)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sp_colli_total = fields.Integer(
        string="Totale Colli",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
    )
    sp_weight_total_kg = fields.Float(
        string="Totale Peso (KG)",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
        digits="Product Unit of Measure",
    )

    @api.depends(
        "order_line.sp_colli_qty",
        "order_line.product_uom_qty",
        "order_line.product_uom_id",
        "order_line.product_id.weight",
    )
    def _compute_sp_totals(self):
        for order in self:
            colli_sum = 0
            weight_sum = 0.0

            for line in order.order_line:
                colli_sum += (line.sp_colli_qty or 0)
                weight_sum += _sp_line_weight_kg(
                    self.env,
                    line.product_uom_qty,
                    line.product_uom_id,
                    line.product_id,
                )

            order.sp_colli_total = colli_sum
            order.sp_weight_total_kg = weight_sum


# -------------------------
# PURCHASE
# -------------------------
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sp_colli_qty = fields.Integer(string="Colli", default=0)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sp_colli_total = fields.Integer(
        string="Totale Colli",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
    )
    sp_weight_total_kg = fields.Float(
        string="Totale Peso (KG)",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
        digits="Product Unit of Measure",
    )

    @api.depends(
        "order_line.sp_colli_qty",
        "order_line.product_qty",
        "order_line.product_uom_id",
        "order_line.product_id.weight",
    )
    def _compute_sp_totals(self):
        for order in self:
            colli_sum = 0
            weight_sum = 0.0

            for line in order.order_line:
                colli_sum += (line.sp_colli_qty or 0)
                weight_sum += _sp_line_weight_kg(
                    self.env,
                    line.product_qty,
                    line.product_uom_id,
                    line.product_id,
                )

            order.sp_colli_total = colli_sum
            order.sp_weight_total_kg = weight_sum


# -------------------------
# STOCK (PICKING)
# -------------------------
class StockMove(models.Model):
    _inherit = "stock.move"

    sp_colli_qty = fields.Integer(string="Colli", default=0)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sp_colli_total = fields.Integer(
        string="Totale Colli",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
    )
    sp_weight_total_kg = fields.Float(
        string="Totale Peso (KG)",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
        digits="Product Unit of Measure",
    )

    @api.depends(
        "move_ids.sp_colli_qty",
        "move_ids.product_uom_qty",
        "move_ids.product_uom",
        "move_ids.product_id.weight",
    )
    def _compute_sp_totals(self):
        for picking in self:
            colli_sum = 0
            weight_sum = 0.0

            for move in picking.move_ids:
                colli_sum += (move.sp_colli_qty or 0)
                weight_sum += _sp_line_weight_kg(
                    self.env,
                    move.product_uom_qty,
                    move.product_uom,
                    move.product_id,
                )

            picking.sp_colli_total = colli_sum
            picking.sp_weight_total_kg = weight_sum


# -------------------------
# ACCOUNT (INVOICE)
# -------------------------
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sp_colli_qty = fields.Integer(string="Colli", default=0)


class AccountMove(models.Model):
    _inherit = "account.move"

    sp_colli_total = fields.Integer(
        string="Totale Colli",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
    )
    sp_weight_total_kg = fields.Float(
        string="Totale Peso (KG)",
        compute="_compute_sp_totals",
        store=True,
        readonly=True,
        digits="Product Unit of Measure",
    )

    @api.depends(
        "invoice_line_ids.sp_colli_qty",
        "invoice_line_ids.quantity",
        "invoice_line_ids.product_uom_id",
        "invoice_line_ids.product_id.weight",
        "invoice_line_ids.display_type",
    )
    def _compute_sp_totals(self):
        for move in self:
            colli_sum = 0
            weight_sum = 0.0

            lines = move.invoice_line_ids.filtered(lambda l: l.display_type == "product")
            for line in lines:
                colli_sum += (line.sp_colli_qty or 0)
                weight_sum += _sp_line_weight_kg(
                    self.env,
                    line.quantity,
                    line.product_uom_id,
                    line.product_id,
                )

            move.sp_colli_total = colli_sum
            move.sp_weight_total_kg = weight_sum

