from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sp_production_method_default = fields.Selection(
        selection=[
            ("wild", "Pescato"),
            ("farmed", "Allevato"),
        ],
        string="Metodo di produzione (default)",
        default="wild",
        index=True,
    )

    sp_fao_zone_id_default = fields.Many2one(
        comodel_name="sp.fao.zone",
        string="Zona FAO (default)",
        index=True,
    )

    sp_fishing_gear_id_default = fields.Many2one(
        comodel_name="sp.fishing.gear",
        string="Attrezzo di pesca (default)",
        index=True,
    )

    sp_production_country_id_default = fields.Many2one(
        comodel_name="res.country",
        string="Paese di produzione (default)",
        help="Usato quando il metodo di produzione è 'Allevato'.",
        index=True,
    )
