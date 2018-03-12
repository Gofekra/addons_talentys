#-*- encofing:utf-8 -*-


from odoo import api, fields, models, exceptions

class AccountAccountType(models.Model):
    _inherit='account.account.type'

    def get_type_by_name(self, name):
        if name is not None :
            type = self.search([('name', '=', name)])
            if type :
                return type
        return False

class AccountAccount(models.Model):
    _inherit= "account.account"

    def get_by_code(self, code, company_id):
        if code is not  None and company_id is not None:
            account = self.search([('code', '=', code),('company_id', '=', company_id)])
            if account :
                return account
        return False