#-*- encoding:utf-8 -*-


from odoo import api, fields, models, exceptions, _
import base64
import xlrd

class AccountImportChartAccountWizard(models.TransientModel):
    _name= "account.import.chart.account"
    _description=""


    company_id= fields.Many2one('res.company', 'Projet', required=True)
    data_file= fields.Binary('Fichier à charger', required=True)
    sheet_ids= fields.One2many('chart.account.import.sheet.line', 'wizard_id', 'Feuilles')
    # type= fields.Selection([('account', 'Plan comptable général'),('analytic', 'Plan comptale analytique')], 'Type', required=True)

    def computeData(self, sheet):
        try :
            keys = [sheet.cell(0, col_index).value for col_index in xrange(sheet.ncols)]

            dict_list = []
            for row_index in xrange(1, sheet.nrows):
                d = {keys[col_index]: sheet.cell(row_index, col_index).value
                     for col_index in xrange(sheet.ncols)}
                dict_list.append(d)
            return dict_list
        except :
            raise exceptions.Warning(_("Erreur lors du chargement de la feuille %s"%sheet.name))

    @api.onchange('data_file')
    def onChangeDataFile(self):
        if self.data_file :
            try :
                lines = []
                data_file = base64.b64decode(self.data_file)
                book = xlrd.open_workbook(file_contents=data_file)
                sheet_names = book.sheet_names()
                if sheet_names :
                    for name in sheet_names :
                        vals = {
                            "name": name,
                            'active': False
                        }
                        lines+=[vals]
                self.sheet_ids = lines
            except :
                raise exceptions.Warning("Erreur lors de la lecture du fichier.")

    def importLine(self, data, company_id):
        is_ok = True
        for key in data.keys():
            if key == 'type':
                type = self.env['account.account.type'].get_type_by_name(data[key])
                if type :
                    data['user_type_id'] = type.id
                else :
                    is_ok = False
            elif key == 'code':
                data[key] = int(data[key])
                account = self.env['account.account'].get_by_code(data[key], company_id)
                if account :
                    is_ok = False
        if is_ok :
            print data
            if company_id :
                data['company_id'] = company_id
            acc = self.env['account.account'].create(data)
            print acc
        #     print data
        else :
            print 'Le compte existe déjà'

    @api.one
    def action_import(self):
        if self.data_file :
            try :
                lines = []
                data_file = base64.b64decode(self.data_file)
                book = xlrd.open_workbook(file_contents=data_file)
                sheet_names = book.sheet_names()
                for line in self.sheet_ids :
                    sheet = book.sheet_by_name(line.name)
                    data = self.computeData(sheet)
                    for dt in data :
                        if self.company_id.child_ids :
                            for company in self.company_id.child_ids :
                                self.importLine(dt, company.id)
                        self.importLine(dt, self.company_id.id)
            except :
                raise exceptions.Warning("Erreur lors de la lecture du fichier.")

class ChartAccountImportSheetLine(models.TransientModel):
    _name='chart.account.import.sheet.line'

    name= fields.Char('Libellé', required=True)
    active= fields.Boolean('A prendre en compte')
    wizard_id= fields.Many2one('account.import.chart.account', 'Wizard')
    aa_wizard_id= fields.Many2one('analytic.account.import.wizard', 'Wizard')


# class AccountImportMapping(models.TransientModel):
#     _name= 'account.import.mapping'
#
#     field_name= fields.Selection([], 'Colonne Odoo', required=True)
#     sheet_column= fields.Selection([], '')
