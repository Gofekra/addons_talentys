#-*- coding:utf-8 -*-

from itertools import groupby
from odoo import api, fields, models
from odoo.tools import Number_To_Word


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('origin')
    def _getSaleOrder(self):
        if self.origin :
            sale_order = self.env['sale.order'].search([('name', '=', self.origin)])
            if sale_order :
                self.saleOrder_id = sale_order

    @api.depends('saleOrder_id')
    def _computeSaleOrder(self):
        return True


    @api.multi
    @api.depends('invoice_line_ids')
    def _get_amount_discount_total(self):
        self.ensure_one()
        res = {}
        total =0.0
        for line in self.invoice_line_ids:
            if line.discount :
                temp = line.price_unit * (1 - (line.discount or 0.0) / 100.0) * line.quantity
                total+= temp
        return total

    @api.multi
    @api.depends('amount_total')
    def _get_amount_total_to_letter(self):
        self.ensure_one()
        if self.amount_total :
            self.montant_lettre = Number_To_Word.Number_To_Word(self.amount_total, 'fr', self.currency_id.symbol, '')
            montant=(self.amount_untaxed * self.taux_acompte / 100) + ((self.amount_untaxed * self.taux_acompte / 100) * 18 / 100)
            self.montant_lettre_acompte = Number_To_Word.Number_To_Word(montant, 'fr', self.currency_id.symbol, '')
            montant_exo=self.amount_untaxed * self.taux_acompte / 100
            print montant_exo
            self.montant_lettre_exo = Number_To_Word.Number_To_Word(montant_exo, 'fr', self.currency_id.symbol, '')
            montant_sold = self.amount_total-self.acompte
            self.montant_lettre_solde = Number_To_Word.Number_To_Word(montant_sold, 'fr', self.currency_id.symbol, '')
            montant_sold_exo = self.amount_untaxed*self.taux_solde/100
            self.montant_lettre_solde_exo = Number_To_Word.Number_To_Word(montant_sold_exo, 'fr', self.currency_id.symbol, '')
            self.facture_exo = Number_To_Word.Number_To_Word(self.amount_untaxed, 'fr', self.currency_id.symbol, '')
            montant_fact_solde = ((self.amount_untaxed*self.taux_solde/100)*18/100)+(self.amount_untaxed*self.taux_solde/100)
            self.facture_solde = Number_To_Word.Number_To_Word(montant_fact_solde, 'fr', self.currency_id.symbol, '')


    @api.multi
    @api.depends('saleOrder_id')
    def _get_all_calcul(self):
        self.ensure_one()
        res = {}
        if self.saleOrder_id and self.type_facture not in ('normal', 'avoir'):

            return 0.0

    # @api.depends('order_id')
    # def compute_taux_acompte(self):
    #     if self.order_id:
    #         taux_acompte = (self.order_id.amount_untax/self.amount_untax)
    #         self.taux_acompte = taux_acompte
    #
    # @api.depends('order_id','type_facture')
    # def compute_net_ap(self):
    #     if self.order_id and self.type_facture == 'acompte':
    #         invoice_obj = self.env('account.invoice')
    #         invoice_ids = invoice_obj.search([('type_facture','=','acompte')])



    saleOrder_id= fields.Many2one('sale.order', 'Vente', required=False, store=False, compute=_getSaleOrder)
    type_facture= fields.Selection([('acompte','Acompte'),('acompte_exo','Acompte exonéré'),('solde','Solde 1'),
            ('solde2','Solde 2'),('solde_exo','Solde exonéré'),('exoneration','Exonération de taxe'),('avoir','Avoir'),
            ('normal', 'Normal')],'Type', select=True, readonly=False)
    mode_paiement= fields.Selection([('cheque','Chèque'), ('espece','Espèce'), ('virement','Virement')],
            'Mode de paiement', select=True, readonly=False)
    taux_amount= fields.Float('Taux montant', compute=_computeSaleOrder, store=False, digits=(10,2))
    montant_lettre = fields.Char(compute='_get_amount_total_to_letter')
    montant_lettre_acompte = fields.Char(compute='_get_amount_total_to_letter')
    montant_lettre_exo = fields.Char(compute='_get_amount_total_to_letter')
    montant_lettre_solde = fields.Char(compute='_get_amount_total_to_letter')
    montant_lettre_solde_exo = fields.Char(compute='_get_amount_total_to_letter')
    facture_exo = fields.Char(compute='_get_amount_total_to_letter')
    facture_solde = fields.Char(compute='_get_amount_total_to_letter')
    taux_acompte = fields.Float('Taux acompte')

    @api.multi
    def report_print(self):

        template = 'talentys_custom.report_talentys_custom'
        return self.env['report'].get_action(self, template)

class AccountInvoiceLine(models.Model):
    _inherit= 'account.invoice.line'

    quantity = fields.Float(string='Quantity', digits=(10,2), required=True, default=1)
    discount = fields.Float(string='Discount (%)', digits=(10,2),default=0.0)
    price_unit = fields.Float(string='Unit Price', required=True, digits=(10,0))

    # @api.one
    # @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
    #     'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    # def _compte_amount_tax(self):
    #     currency = self.invoice_id and self.invoice_id.currency_id or None
    #     price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
    #     taxes = False
    #     if self.invoice_line_tax_ids:
    #         taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
    #     return taxes


