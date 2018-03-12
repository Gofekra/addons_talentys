# -*- encoding: utf-8 -*-
##############################################################################
#
#    VEONE TECHNOLOGIES, Open Source Management Solution
#    Copyright (C) 2013 (<http://www.veone.net>).
#
##############################################################################
from odoo import fields, models, api

class ir_cron(models.Model):
    _inherit = "ir.cron"

    purchase_id = fields.Many2one('purchase.order.line', 'Demande de cotation')
