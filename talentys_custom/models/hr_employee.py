# -*- encoding: utf-8 -*-

from odoo import fields, models, api
from odoo import exceptions

class employee(models.Model):
    _inherit='hr.employee'

    besoin_ids = fields.One2many('purchase.exp.besoin', 'demandeur_id', 'Expressions de besoin', required=False)
    da_ids = fields.One2many('purchase.exp.achat', 'demandeur_id', "Demande d'achat", required=False)
