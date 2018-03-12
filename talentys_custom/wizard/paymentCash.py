#-*- encoding:utf-8 -*-


from odoo import api, fields, models, exceptions, _

class AccountPaymentCash(models.TransientModel):
    _name= 'account.payment.cash'
    _description = "Gestion des payment de DA"

    def _get_defaultVals(self):
        active_id = self._context.get('active_id')
        request_obj = self.env['purchase.exp.achat']
        if active_id :
            request = request_obj.browse(active_id)
            if request.demande_id and request.demande_id.quotation_ids :
                result =  [
                    (0, 0, {'partner_id': purchase.partner_id.id,
                            'ref': purchase.name,
                            'amount': (-1) * purchase.amount_total,
                            })
                    for purchase in request.demande_id.quotation_ids
                ]
                return result



    name= fields.Char('Description', required=True)
    bank_statement_id= fields.Many2one('account.bank.statement', 'Caisse', domain=[('state', '=', 'open')], required=True)
    user_id= fields.Many2one('res.users', 'Caissier (ère)', default= lambda self: self.env.user.id)
    date_payment= fields.Date("Date de paiement", required=True)
    line_ids= fields.One2many('account.payment.cash.line', 'cash_id', string='Lignes', default=_get_defaultVals, readonly=True)
    request_id= fields.Many2one('purchase.exp.achat', 'DA', required=False)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
              default=lambda self: self.env.user.company_id.currency_id.id, readonly=True)


    @api.one
    def validateAction(self):
        line_obj = self.env['account.bank.statement.line']
        if self.bank_statement_id :
            for line in self.line_ids :
                vals = {
                    'date': self.date_payment,
                    'name': self.name,
                    'partner_id': line.partner_id.id,
                    'ref': line.ref,
                    'amount': line.amount,
                    'statement_id': self.bank_statement_id.id
                }
                line_obj.create(vals)
            active_id = self._context.get('active_id')
            request_obj = self.env['purchase.exp.achat']
            if active_id :
                request = request_obj.browse(active_id)
                request.write({'state': 'done'})
        else :
            raise exceptions.MissingError(_("Vous devez obligatoirement ajouter une caisse afin de valider les éecritures"))





class AccountPaymentCashLine(models.TransientModel):
    _name= 'account.payment.cash.line'
    _description= "Lgnes de Payement des demandes d'achats"

    partner_id= fields.Many2one('res.partner','Parténaire', required=False)
    ref= fields.Char("Référence", required=False)
    amount= fields.Monetary('Montant')
    cash_id= fields.Many2one('account.payment.cash', 'Payment', required=False)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
              default=lambda self: self.env.user.company_id.currency_id.id)