# -*- coding: utf-8 -*-

from datetime import datetime
import time
from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ReportExpresionBesoin(models.AbstractModel):
    _name = 'report.talentys_custom.report_exprbesoin'

    def getNameByCode(self, obj, code):
        print obj.name
        return obj.name


    @api.model
    def render_html(self, docids, data=None):
        data['computed'] = {}

        obj_partner = self.env['purchase.expression.besoin']
        partners = obj_partner.browse(docids)

        docargs = {
            'doc_ids': docids,
            'doc_model': self.env['purchase.expression.besoin'],
            'data': data,
            'docs': partners,
            'get_name': self.getNameByCode,
            'time': time,
        }
        return self.env['report'].render('talentys_custom.report_exprbesoin', docargs)
