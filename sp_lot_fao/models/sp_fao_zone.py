from odoo import api, models, fields


class SpFaoZone(models.Model):
    _name = "sp.fao.zone"
    _description = "Zona FAO"
    _rec_name = "display_name"
    _order = "sequence, code, id"

    sequence = fields.Integer(string="Ordine", default=10, index=True)

    code = fields.Char(string="Codice", required=True, index=True)
    name_it = fields.Char(string="Nome area IT", required=True, index=True)
    name_en = fields.Char(string="Nome area EN")
    display_name = fields.Char(
        string="Nome",
        compute="_compute_display_name",
        store=True,
    )

    macro_area = fields.Char(string="Macroarea")

    active = fields.Boolean(default=True)

    def name_get(self):
        res = []
        for rec in self:
            name = f"{rec.code} - {rec.name_it}" if rec.code and rec.name_it else rec.code or rec.name_it
            res.append((rec.id, name))
        return res
    @api.depends("code", "name_it")
    def _compute_display_name(self):
        for rec in self:
            if rec.code and rec.name_it:
                rec.display_name = f"{rec.code} - {rec.name_it}"
            else:
                rec.display_name = rec.code or rec.name_it or ""
