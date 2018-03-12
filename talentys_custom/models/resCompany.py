#-*- coding:utf-8 -*-

from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit='res.company'

    header_logo= fields.Binary('Entête de rapport', required=False)
    footer_logo= fields.Binary('Pied de page rapport', required=False)
    # registre_commerce= fields.Char('RCCM', required=True)
    ifu= fields.Char("IFU", required=True)
    fiscale= fields.Char('Division fiscale de rattachement', required=True)








