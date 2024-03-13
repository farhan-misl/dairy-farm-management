from odoo import api, fields, models


class ApprovalConfig(models.Model):
    _name = "approval.config"
    _description = "Approval Config"
    _order = "sequence, id"

    @api.model
    def _get_sequence(self):
        others = self.search(
            [("sequence", "<>", False)], order="sequence desc", limit=1
        )
        if others:
            return (others[0].sequence or 0) + 1
        return 1

    name = fields.Char("Name", required=True, translate=True)
    sequence = fields.Integer("Sequence", default=_get_sequence, copy=False)

    is_initial = fields.Boolean(string="Initial Stage")
    final_stage = fields.Boolean(string="Final Stage")
    approval_module_id = fields.Many2one(
        "approval.module",
        "Approval Module",
        store=True,
        required=True,
        ondelete="cascade",
    )
    approval_module = fields.Char(
        related="approval_module_id.technical_name", string="Module Technical Name"
    )
    approval_template_ids = fields.One2many(
        "approval.template",
        "approval_config_id",
        "Approvals",
    )
    approval_type_id = fields.Many2one(
        "approval.type", "Approval Type", store=True, required=True, ondelete="cascade"
    )
    approval_type = fields.Char(
        related="approval_type_id.code", string="Approval Type Code", store=True
    )

    next_stage_id = fields.Many2one(
        "approval.config", compute="_compute_next_stage_id", string="Next Stage"
    )
    user_can_approve = fields.Boolean(
        "Can Approve",
        default="False",
        compute="_compute_user_can_approve",
    )

    has_employee_id = fields.Boolean(related="approval_type_id.has_employee_id", store=True)
    supervisor_can_approve = fields.Boolean(default=False)
    department_head_can_approve = fields.Boolean(default=False)

    def _compute_next_stage_id(self):
        for rec in self:
            rec = rec.sudo()
            current_sequence = rec.sequence
            next_stage = rec.search(
                [
                    ("sequence", ">", current_sequence),
                    ("approval_module_id", "=", rec.approval_module_id.id),
                    ("approval_type_id", "=", rec.approval_type_id.id),
                ],
                limit=1,
            )
            rec.next_stage_id = next_stage.id if next_stage else rec.id

    def _compute_user_can_approve(self):
        for rec in self:
            rec.sudo().user_can_approve = (
                self.env.user
                in rec.sudo().next_stage_id.approval_template_ids.mapped("user_ids")
                + rec.next_stage_id.approval_template_ids.mapped("group_ids.users")
            )


class ApprovalType(models.Model):
    _name = "approval.type"
    _description = "Approval Type"
    _order = "name"

    name = fields.Char("Name", required=True, translate=True, readonly=True)
    code = fields.Char("Short Code", readonly=True, required=True)
    approval_module_id = fields.Many2one(
        "approval.module", "Approval Module", store=True, readonly=True
    )
    has_employee_id = fields.Boolean(default=False)

    _sql_constraints = [
        (
            "code_unique",
            "unique(code)",
            "The short code must be unique!",
        )
    ]


class ApprovalModule(models.Model):
    _name = "approval.module"
    _description = "Approval Module"
    _order = "name"

    name = fields.Char("Name", required=True, readonly=True)
    technical_name = fields.Char("Technical Name", required=True, readonly=True)
    _sql_constraints = [
        (
            "technical_name_unique",
            "unique(technical_name)",
            "The technical name must be unique!",
        )
    ]


class ApprovalRolesLines(models.Model):
    _name = "approval.template"
    _description = "Approval Template"
    _order = "sequence"

    sequence = fields.Integer("Sequence")
    user_ids = fields.Many2many(
        "res.users",
        string="Users",
    )
    approval_config_id = fields.Many2one(
        "approval.config",
        "Approval Config",
    )
    group_ids = fields.Many2many(
        "res.groups",
        string="Groups",
    )
