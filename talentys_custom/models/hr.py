#-*- coding:utf-8 -*-

from odoo import api, fields, models, _


class HrDepartment(models.Model):
    _inherit = 'hr.department'


    code= fields.Char('Code', required=True, size=10)
    type= fields.Selection([('service', 'Service'),('department', 'Departement')], 'Type', required=True)