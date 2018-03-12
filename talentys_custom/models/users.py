# -*- encoding: utf-8 -*-

from odoo import fields, models, api
from odoo import exceptions

class res_users(models.Model):
    _inherit="res.users"

    project_responsible_ids = fields.Many2many('res.users', 'user_project_rel', 'user_id', 'project_id', 'Responsables')
    responsable_achat = fields.Boolean('Responsable des achats')
    signature_numerique = fields.Binary('Signature numérique')
    technicien = fields.Boolean('Technicien')
    is_cashier= fields.Boolean('Est un(e) Caissier(ière)', default=False)

