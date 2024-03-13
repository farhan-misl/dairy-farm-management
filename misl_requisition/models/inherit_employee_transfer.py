from odoo import models, fields, api, _


class MislEmployeeTransfer(models.Model):
    _inherit = 'misl.hr.transfer'

    requisition_id = fields.Many2one('requisition.master', string='Requisition')

    @api.onchange('requisition_id')
    def onchange_requisition_id(self):
        if self.requisition_id:
            self.to_company_id = self.requisition_id.company_id.id
            self.to_operating_unit_id = self.requisition_id.requester_operating_unit.id
            self.to_department_id = self.requisition_id.requester_department_id.id

        else:
            self.to_company_id = False
            self.to_operating_unit_id = False
            self.to_department_id = False

