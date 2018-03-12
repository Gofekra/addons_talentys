from odoo import fields,models,api
from odoo.tools import Number_To_Word


class ReportTalentys(models.AbstractModel):
    _name = "report.talentys_custom.report_talentys_custom"
    @api.multi
    def _get_amount_total_to_letter(self,amount):
        self.ensure_one()
        amount_total_letter = ''
        if amount:
            amount_total_letter = Number_To_Word.Number_To_Word(amount, 'fr', self.currency_id.symbol, '')
        return amount_total_letter

    @api.model
    def render_html(self, docids, data=None):
        self.model =self.env['account.invoice']
        docs = self.env[self.model].browse(data['ids'])
        montant = "self._get_amount_total_to_letter(docs['amount_total'])"
        print "montant"
        print montant
        docargs = {
            'doc_ids': self.ids,
            'model': self.model,
            'docs': docs,
            'montant':montant,
        }
        return self.env['report'].render('talentys_custom.report_talentys_custom', docargs)