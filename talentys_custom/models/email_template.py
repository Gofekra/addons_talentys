# -*- encoding: utf-8 -*-
##############################################################################
#
#    VEONE TECHNOLOGIES, Open Source Management Solution
#    Copyright (C) 2013 (<http://www.veone.net>).
#
##############################################################################

# from osv import osv, fields
# from tools.translate import _
from odoo import fields, models, api
from odoo.tools.translate import _
class email_template(models.Model):
    _inherit = 'mail.template'

    @api.model
    def _get_order_line_model_id(self):
        return self.env['ir.model'].search([('model', '=', 'purchase.order')])[0]

    _defaults = {
        'object_name': _get_order_line_model_id,
        'def_to': '${object.order_id.partner_id.email}',
        #'def_cc': '${object.order_id.shop_id.company_id.partner_id.email}',
        }
