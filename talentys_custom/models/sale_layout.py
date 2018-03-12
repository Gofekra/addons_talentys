# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from itertools import groupby
import odoo.addons.decimal_precision as dp


def grouplines(self, ordered_lines, sortkey):
    """Return lines from a specified invoice or sale order grouped by category"""
    grouped_lines = []
    for key, valuesiter in groupby(ordered_lines, sortkey):
        group = {}
        group['category'] = key
        group['lines'] = list(v for v in valuesiter)

        if 'subtotal' in key and key.subtotal is True:
            group['subtotal'] = sum(line.price_subtotal for line in group['lines'])
        grouped_lines.append(group)

    return grouped_lines


class SaleLayoutCategory(models.Model):
    _name = 'sale_layout.category'
    _order = 'sequence, id'

    name= fields.Char('Name', required=True, translate=True)
    sequence= fields.Integer('Sequence', required=True, default=10)
    subtotal= fields.Boolean('Add subtotal', default=True)
    separator= fields.Boolean('Add separator', default=True)
    pagebreak= fields.Boolean('Add pagebreak', default=False)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def sale_layout_lines(self, invoice_id=None):
        """
        Returns invoice lines from a specified invoice ordered by
        sale_layout_category sequence. Used in sale_layout module.

        :Parameters:
            -'invoice_id' (int): specify the concerned invoice.
        """
        self.ensure_one()
        ordered_lines = self.invoice_line_ids
        # We chose to group first by category model and, if not present, by invoice name
        sortkey = lambda x: x.sale_layout_cat_id if x.sale_layout_cat_id else ''

        return grouplines(self, ordered_lines, sortkey)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    _order = 'invoice_id, categ_sequence, sequence, id'

    sale_layout_cat_id = fields.Many2one('sale_layout.category', string='Section')
    categ_sequence = fields.Integer(related='sale_layout_cat_id.sequence', string='Layout Sequence', store=True)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def sale_layout_lines(self, order_id=None):
        """
        Returns order lines from a specified sale ordered by
        sale_layout_category sequence. Used in sale_layout module.

        :Parameters:
            -'order_id' (int): specify the concerned sale order.
        """
        self.ensure_one()
        ordered_lines = self.order_line
        sortkey = lambda x: x.sale_layout_cat_id if x.sale_layout_cat_id else ''

        return grouplines(self, ordered_lines, sortkey)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'order_id, categ_sequence, sale_layout_cat_id, sequence, id'




    @api.multi
    def _prepare_order_line_invoice_line(self,  account_id=False):
        """Save the layout when converting to an invoice line."""
        invoice_vals = super(SaleOrderLine, self)._prepare_order_line_invoice_line(account_id=account_id)
        if self.sale_layout_cat_id:
            invoice_vals['sale_layout_cat_id'] = self.sale_layout_cat_id.id
        if self.categ_sequence:
            invoice_vals['categ_sequence'] = self.categ_sequence
        return invoice_vals

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.sale_layout_cat_id:
            res['sale_layout_cat_id'] = self.sale_layout_cat_id.id
        return res
