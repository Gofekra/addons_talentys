#-*- coding:utf-8 -*-

from odoo import api, fields, models

class AccountTax(models.Model):
    _inherit = "account.tax"


    type= fields.Selection([('tva', 'TVA'),('other', 'Autres')], 'Type', required=False, default='other')
    amount_type = fields.Selection(selection_add=[('based_other', "Basée sur d'autres taxes")])
    depend_tax_ids = fields.Many2many('account.tax', 'account_tax_depend_rel', 'parent_tax', 'child_tax', string='Children Taxes')
    perc_amount= fields.Float('Pourcentage de la Taxe', required=True)

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        self.ensure_one()
        if self.amount_type == 'based_other':
            amount = 0.0
            if self.depend_tax_ids :
                for tax in self.depend_tax_ids :
                    print base_amount
                    result = tax._compute_amount(base_amount, price_unit, quantity, product, partner)
                    amount+= result + base_amount
            print amount
            if amount != 0:
                if self.amount_type == 'based_other' and self.price_include:
                    return amount - (amount / (1 + self.perc_amount / 100))
                else :
                    return amount * self.perc_amount / 100
        return super(AccountTax, self)._compute_amount(base_amount, price_unit, quantity, product, partner)