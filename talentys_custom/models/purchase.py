# -*- encoding: utf-8 -*-
##############################################################################
#
#    VEONE TECHNOLOGIES, Open Source Management Solution
#    Copyright (C) 2013 (<http://www.veone.net>).
#
##############################################################################

from odoo import fields, models, api
from odoo.tools.translate import _
from odoo import netsvc


class purchase_order(models.Model):
    _inherit = "purchase.order"
    # _logger = netsvc.Logger()
    @api.one
    def action_wait(self):
        cron_data = {
                        'name': _('Alert: '),
                        'nextcall' : '2017-11-01',
                        'model': 'mail.template',
                        'interval_number': 0,
                        'function': 'generate_mail',
                        'args': repr([self.id]),
                        'subscription_id': self.id,
                    }
        self.env['ir.cron'].create(cron_data)

    @api.one
    def _get_da(self):
        da_obj= self.env['purchase.exp.achat']
        da_ids= da_obj.search([('quotation_id', '=', self.id)])
        if da_ids :
            print da_ids
            self.achat_id = da_ids[0].id

    achat_id= fields.Many2one('purchase.exp.achat', "Demande d'achat", required=False, compute=_get_da)
    besoin_id= fields.Many2one('purchase.exp.besoin', "Expression de besoin", required=False)
    pricelist_id = fields.Many2one('product.pricelist', "Liste de prix d'achat")