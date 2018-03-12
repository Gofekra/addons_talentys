#-*- coding:utf-8 -*-

from odoo import models, fields

class StockMove(models.Model):
    _inherit= 'stock.move'


    ordered_qty = fields.Float('Ordered Quantity', digits=(10,2))
    product_uom_qty = fields.Float(
        'Quantity',
        digits=(10,2),
        default=1.0, required=True, states={'done': [('readonly', True)]},
        help="This is the quantity of products from an inventory "
             "point of view. For moves in the state 'done', this is the "
             "quantity of products that were actually moved. For other "
             "moves, this is the quantity of product that is planned to "
             "be moved. Lowering this quantity does not generate a "
             "backorder. Changing this quantity on assigned moves affects "
             "the product reservation, and should be done with care.")





class PackOperation(models.Model):
    _inherit = "stock.pack.operation"


    product_qty = fields.Float('To Do', default=0.0, digits=(10,2), required=True)
    ordered_qty = fields.Float('Ordered Quantity', digits=(10,2))
    qty_done = fields.Float('Done', default=0.0, digits=(10,2))