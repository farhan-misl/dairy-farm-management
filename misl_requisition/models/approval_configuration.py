from odoo import fields, models


class ApprovalConfig(models.Model):
    _inherit = "approval.config"

    self_approval = fields.Boolean(string="Self Approval")
    create_po = fields.Boolean(string="Create PO")
    create_agreement = fields.Boolean(string="Create Agreement")
    create_internal_transfer = fields.Boolean(string="Create Internal Transfer")
    create_employee_transfer = fields.Boolean(string="Create Employee Transfer")
    process_recruitment = fields.Boolean(string="Process Recruitment")
    approve_money = fields.Boolean(string='Approve/Refuse Money')
