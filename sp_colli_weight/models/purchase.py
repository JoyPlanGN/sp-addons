# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sp_colli_qty = fields.Integer(string="Colli", default=0)

    sp_weight_manual = fields.Boolean(
        string="Peso manuale",
        default=False,
        copy=False,
    )

    sp_weight_line_kg = fields.Float(
        string="Peso riga (Kg)",
        compute="_compute_sp_weight_line_kg",
        inverse="_inverse_sp_weight_line_kg",
        store=True,
        readonly=False,
    )

    @api.depends(
        "display_type",
        "sp_weight_manual",
        "product_qty",
        "product_uom_id",
        "product_id",
        "product_id.weight",
    )
    def _compute_sp_weight_line_kg(self):
        kg_uom = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False)

        for line in self:
            if line.display_type:
                line.sp_weight_line_kg = 0.0
                continue

            if line.sp_weight_manual:
                continue

            qty = line.product_qty or 0.0

            if kg_uom and line.product_uom_id and line.product_uom_id.id == kg_uom.id:
                line.sp_weight_line_kg = qty
            else:
                line.sp_weight_line_kg = qty * (line.product_id.weight or 0.0)

    def _inverse_sp_weight_line_kg(self):
        for line in self:
            if line.display_type:
                continue
            line.sp_weight_manual = True


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sp_colli_total = fields.Integer(
        string="Totale Colli",
        compute="_compute_sp_totals",
        store=True,
    )

    sp_weight_total_kg = fields.Float(
        string="Totale Peso (Kg)",
        compute="_compute_sp_totals",
        store=True,
    )

    @api.depends(
        "order_line.sp_colli_qty",
        "order_line.sp_weight_line_kg",
        "order_line.display_type",
    )
    def _compute_sp_totals(self):
        for order in self:
            lines = order.order_line.filtered(lambda l: not l.display_type)
            order.sp_colli_total = sum(lines.mapped("sp_colli_qty"))
            order.sp_weight_total_kg = sum(lines.mapped("sp_weight_line_kg"))
