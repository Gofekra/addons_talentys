#-*- encoding:utf-8 -*-

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.multi
    @api.depends('pricelist_id')
    def update_sale_order(self):
        self.ensure_one()
        if self.pricelist_id :
            self.order_line.write({'currency_id': self.pricelist_id.currency_id.id})
            self._amount_all()
