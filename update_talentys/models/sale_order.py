#-*- coding:utf-8 -*-

from odoo import api, models

class SaleOrderLine(models.Model):
    _inherit="sale.order.line"