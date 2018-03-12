#-*- coding:utf-8 -*-


from odoo import models, api, fields

class AffectedTechnicien(models.TransientModel):
    _name= "affected.technicien"


    user_id= fields.Many2one('res.users', "Technicien", domain="[('technicien', '=', True)]")

    @api.one
    def send_notification_2(self, email_id, context=None):
        template_id = self.env['ir.model.data'].get_object_reference('talentys_custom', email_id)
        try:
            mail_templ = self.env['mail.template'].browse(template_id[1])
            result = mail_templ.send_mail(res_id=self.id, force_send=True)
            print result
            return True
        except:
            return False

    @api.one
    def affectedTechnicien(self):
        context = self._context
        active_model = context.get('active_model')
        active_id= context.get('active_id')
        self.env[active_model].browse(active_id).\
            write({
            'technician_id': self.user_id.id,
            'state': 'affected',
        })
        self.send_notification_2('affectedTechnicien', self._context),
