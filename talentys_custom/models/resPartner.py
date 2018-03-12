#-*- coding:utf-8 -*-


from odoo import fields, api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    is_technicien = fields.Boolean('Est un technicien', default=False)
    is_cashier= fields.Boolean('Est un(e) Caissier(ière)', default=False)
    signature_talentys= fields.Binary('Signature Électronique', required=False)