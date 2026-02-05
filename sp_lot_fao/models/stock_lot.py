# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = "stock.lot"

    # =========================
    # CAMPI FAO
    # =========================

    sp_production_method = fields.Selection(
        selection=[
            ("wild", "Pescato"),
            ("farmed", "Allevato"),
        ],
        string="Metodo di produzione",
        required=True,
        default="wild",
        index=True,
    )

    # Numero lotto visibile in etichetta del fornitore/produttore (quello che l’operatore ricerca)
    sp_supplier_lot = fields.Char(
        string="Lotto fornitore/produttore",
        index=True,
        help="Numero lotto riportato sull'etichetta del fornitore/produttore.",
    )

    # Pescato (wild) -> tabelle FAO
    sp_fao_zone_id = fields.Many2one(
        comodel_name="sp.fao.zone",
        string="Zona FAO",
        index=True,
        help="Zona di pesca (FAO). Obbligatoria per Pescato.",
    )

    sp_fishing_gear_id = fields.Many2one(
        comodel_name="sp.fishing.gear",
        string="Attrezzo di pesca",
        index=True,
        help="Attrezzo di pesca (FAO). Obbligatorio per Pescato.",
    )

    # Allevato (farmed) -> Paese di produzione (ISO + nome)
    sp_production_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Paese di produzione",
        help="Per Allevato: selezionare il Paese di produzione (sigla ISO + nome).",
    )

    # =========================
    # VINCOLI FAO
    # =========================

    @api.constrains(
        "sp_production_method",
        "sp_fao_zone_id",
        "sp_fishing_gear_id",
        "sp_production_country_id",
    )
    def _check_sp_fao_rules(self):
        for lot in self:
            if lot.sp_production_method == "wild":
                if not lot.sp_fao_zone_id or not lot.sp_fishing_gear_id:
                    raise ValidationError(
                        _("Per lotti 'Pescato' sono obbligatori Zona FAO e Attrezzo di pesca.")
                    )
            elif lot.sp_production_method == "farmed":
                if not lot.sp_production_country_id:
                    raise ValidationError(
                        _("Per lotti 'Allevato' è obbligatorio il Paese di produzione.")
                    )

    # =========================
    # EREDITARIETÀ PRODOTTO → LOTTO (SOLO CAMPI FAO, NO DATE)
    # =========================

    def _sp_prepare_fao_vals_from_product(self, product):
        """Prepara i valori FAO da copiare sul lotto prendendoli dai DEFAULT del prodotto."""
        if not product:
            return {}

        tmpl = product.product_tmpl_id

        return {
            "sp_production_method": tmpl.sp_production_method_default or False,
            "sp_fao_zone_id": tmpl.sp_fao_zone_id_default.id or False,
            "sp_fishing_gear_id": tmpl.sp_fishing_gear_id_default.id or False,
            "sp_production_country_id": tmpl.sp_production_country_id_default.id or False,
        }

    @api.onchange("product_id")
    def _onchange_product_id_sp_fill_fao(self):
        """Quando l'utente sceglie il prodotto, precompila i campi FAO."""
        for lot in self:
            if not lot.product_id:
                continue

            fao_vals = lot._sp_prepare_fao_vals_from_product(lot.product_id)

            # 1) Metodo di produzione: imposto dal prodotto (sovrascrive il default 'wild')
            if fao_vals.get("sp_production_method"):
                lot.sp_production_method = fao_vals["sp_production_method"]

            # 2) Altri campi: non sovrascrivere se l'utente li ha già compilati
            for field_name in [
                "sp_fao_zone_id",
                "sp_fishing_gear_id",
                "sp_production_country_id",
            ]:
                if not lot[field_name]:
                    lot[field_name] = fao_vals.get(field_name)

    @api.model_create_multi
    def create(self, vals_list):
        """Quando Odoo crea il lotto (anche automaticamente), copia i default FAO dal prodotto
        se i campi non sono già presenti in vals.
        """
        product_ids = {v.get("product_id") for v in vals_list if v.get("product_id")}
        products = {
            p.id: p for p in self.env["product.product"].browse(list(product_ids))
        }

        for vals in vals_list:
            product = products.get(vals.get("product_id"))
            if not product:
                continue

            fao_vals = self._sp_prepare_fao_vals_from_product(product)

            # Imposta solo se non già passato (o vuoto)
            for field_name, value in fao_vals.items():
                if not vals.get(field_name):
                    vals[field_name] = value

        return super().create(vals_list)
