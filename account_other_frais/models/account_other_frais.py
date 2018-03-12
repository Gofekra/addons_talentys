# -*- utf-8 -*-
'''
Created on 10 oct. 2016

@author: Jean Jonathan ARRA
@email: jonathan.arra@gmail.com
'''

from openerp import api, models, fields, exceptions

from openerp.tools.safe_eval import safe_eval as eval

class AccountFraisTimbre(models.Model):
    _name= 'account.other.charge'
    _description = """
    Gestion des autres frais
    """
    
    name= fields.Char('Nom', size=124, required=True)
    condition= fields.Boolean('Tout applicable', required=False, default=False)
    account_account_id = fields.Many2one('account.account', 'Compte', required=True)
#     account_analytic_id = fields.Many2one('account.analytic.account', 'Compte analytique', required=False)
    active= fields.Boolean('Actif', default=True)
    type= fields.Selection([('fixe', 'Montant fixe'),('pourcentage','Pourcentage'),('code_python','Code python')],
                           'Type de calcul', default='fixe', required=True)
    pourcentage= fields.Float('Pourcentage', required=False)
    amount_fixed = fields.Integer('Montant', required=False)
    code_python= fields.Text('Code python', required=False)
    
    
    _defaults = {
         'code_python':'''# amount_untaxed\n# or False\nresult = amount_untaxed * 0.10''',        
     }
    

    def _compute(self, amount_untaxed=0, amount_taxed=0, amount_total=0):
        data = {}
        if self.type=='pourcentage':
            amount = amount_untaxed * self.pourcentage
            data['amount'] = amount

        elif self.type=='fixed':
            data['amount'] = self.amount_fixed
           # data['amount'] = quantity
        elif self.type=='code_python':
            localdict = {'amount_untaxed':amount_untaxed, 'amount_taxed': amount_taxed, 'amount_total': amount_total}
            print localdict
            eval(self.code_python, localdict, mode="exec", nocopy=True)
            amount = localdict['result']
            data['amount'] = amount
        return data

    
