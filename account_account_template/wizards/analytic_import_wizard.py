#-*- encoding:utf-8 -*-


from odoo import api, fields, models, exceptions, _
import base64
import xlrd


class AnalyticAccountImportWizard(models.TransientModel):
    _name = 'analytic.account.import.wizard'


    data_file= fields.Binary('Fichier à charger', required=True)
    company_id= fields.Many2one('res.company', 'Projet', required=True)
    sheet_ids= fields.One2many('chart.account.import.sheet.line', 'wizard_id', 'Feuilles')