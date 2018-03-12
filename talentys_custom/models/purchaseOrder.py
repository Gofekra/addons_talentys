#-*- coding:utf-8 -*-

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit= 'purchase.order.line'

    @api.depends("discount", 'price_unit', 'product_qty')
    def _get_amount_discount(self):
        for line in self:
            amount = 0.0
            if line.discount and line.discount != 0.0:
                amount = line.price_unit * line.discount * line.product_qty/100
                line.update({
                    'amount_discount': amount
                })

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_amount(self):
        for line in self:
            price_subtotal = 0.0
            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            if line.discount != 0.0:
                price_subtotal= taxes['total_excluded'] - (taxes['total_excluded'] * line.discount / 100)
            else :
                price_subtotal= taxes['total_excluded']
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': price_subtotal,
            })





    discount= fields.Float('Remise (%)', required=False, default=0.0)
    amount_discount= fields.Float('Montant de la remise', compute=_get_amount_discount, store=True)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)


class PurchaseOrder(models.Model):
    _inherit='purchase.order'

    @api.one
    def _get_da(self):
        da_obj= self.env['purchase.exp.achat']
        da_ids= da_obj.search([('quotation_id', '=', self.id)])
        if da_ids :
            print da_ids


    da_id= fields.Many2one('purchase.exp.achat', 'Référence de la DA', compute=_get_da)


