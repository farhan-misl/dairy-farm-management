from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

RECEIVING_STATUS = [
    ('full_pending', 'Fully Pending'),
    ('partial', 'Partially Received'),
    ('full', 'Fully Received')
]


class RequisitionMain(models.Model):
    """
    This model is responsible for all requisition related data and workflows.

    """

    _name = "requisition.master"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _description = "Requisition"

    def _default_employee(self):
        return self.env["hr.employee"].search(
            [("user_id", "=", self.env.user.id)], limit=1
        )

    def _get_default_department(self):
        emp = self.env["hr.employee"].search(
            [("user_id", "=", self.env.user.id), ('company_id', '=', self.env.company.id)], limit=1
        )
        return emp.department_id if emp.department_id else False

    # def _get_default_warehouse_id(self):
    #     default_warehouse_id = self.env.user.property_warehouse_id
    #     if default_warehouse_id:
    #         return default_warehouse_id.id
    #     return False

    name = fields.Char(string="Requisition ID", copy=False, default='/')
    master_requisition = fields.Many2one(
        "requisition.master",
        string="Master Requisition",
        domain=[("requisition_type", "=", "use"), ("state", "=", "approved")], tracking=True
    )

    requisition_line_ids = fields.One2many(
        "requisition.line", "requisition_id", string="Requisition Line"
    )

    prod_serv_requisition_id = fields.One2many(
        "requisition.product.service", "requisition_id", ondelete="cascade", copy=True
    )
    initiator_id = fields.Many2one(
        "res.users", string="Creator", default=lambda self: self.env.user, tracking=True
    )

    employee_id = fields.Many2one(
        "hr.employee",
        "Requisitioner",
        default=lambda self: self._default_employee(),
        required=True, tracking=True
    )
    # emp_id = fields.Char(string='Employee ID', related='employee_id.emp_id', store=True)
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env.company,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        required=True, tracking=True
    )

    department_id = fields.Many2one(
        "hr.department", string="Department", related="employee_id.department_id"
    )
    job_title = fields.Char(
        related="employee_id.job_title", string="Designation", index=True, readonly=True
    )

    item_type = fields.Selection(
        [
            ("product", "Product/Goods"),
            ("service", "Service"),
        ],
        default="product",
        string="Item Type",
        required=True, tracking=True
    )
    requisition_date = fields.Datetime(
        "Requisition Date", copy=False, default=fields.Datetime.now, index=True, tracking=True
    )
    date_required = fields.Datetime(
        "Date Required", copy=False, index=True, default=fields.Datetime.now, tracking=True
    )
    description = fields.Text(string="Description", tracking=True)
    requester_department_id = fields.Many2one('hr.department', string='Requesting Department',
                                              default=_get_default_department, tracking=True)

    requisition_type = fields.Selection(
        [
            ("use", "Master"),
            ("inventory", "Inventory"),
            ("purchase", "Purchase"),
        ],
        default="use",
        string="Requisition Type",
        required=True, tracking=True
    )

    ################### APPROVAL PROCESS CODE START ###################### noqa

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Approval Pending"),
            ("approved", "Approved"),
            ('closed', "Closed"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        copy=False,
        default="draft",
        readonly=True,
        required=True,
        tracking=True,
    )

    stage_id = fields.Many2one(
        "approval.config",
        "Approval Stage",
        copy=False,
        tracking=True,
        group_expand="_read_group_stage_ids",
        default=lambda self: self.env["approval.config"].search(
            [("approval_type", "=", self.requisition_type)],
            order="sequence asc",
            limit=1,
        ),
    )
    is_final = fields.Boolean(related="stage_id.final_stage")

    source_type = fields.Selection(
        [("none", "None")], string="Source Type", default="none", tracking=True
    )

    agreement_ids = fields.One2many(
        "purchase.requisition",
        "custom_requisition_id",
        string="Purchase Agreements",
        copy=False,
        readonly=False,
    )
    create_po = fields.Boolean(related="stage_id.create_po")
    create_agreement = fields.Boolean(related="stage_id.create_agreement")
    create_internal_transfer = fields.Boolean(
        related="stage_id.create_internal_transfer"
    )

    purchase_ids = fields.One2many(
        "purchase.order",
        "custom_requisition_id",
        string="RFQs/Orders",
        copy=False,
        readonly=False,
    )
    po_count = fields.Integer(compute="_compute_po_number", string="Number of Orders")

    next_stage_id = fields.Many2one(
        related="stage_id.next_stage_id", string="Next Stage", store=True
    )
    transfer_ids = fields.One2many(
        "stock.picking", "custom_requisition_id", string="Transfer Ids"
    )
    transfer_count = fields.Integer(
        compute="_compute_transfer_number", string="Number Of Transfers"
    )
    purchase_requisition_ids = fields.One2many(
        "requisition.master",
        "master_requisition",
        string="Purchase Requisitions",
        domain=[("requisition_type", "=", "purchase")],
    )
    purchase_requisition_count = fields.Integer(
        compute="_compute_purchase_requisition", string="No of Purchase Requisition"
    )
    inventory_requisition_ids = fields.One2many(
        "requisition.master",
        "master_requisition",
        string="Inventory Requisitions",
        domain=[("requisition_type", "=", "inventory")],
    )
    inventory_requisition_count = fields.Integer(
        compute="_compute_inventory_requisition", string="No of Inventory Requisition"
    )

    user_can_approve = fields.Boolean(
        "Can Approve",
        default="False",
        compute="_compute_user_can_approve",
    )

    agreement_count = fields.Integer(
        compute="_compute_agreement_number", string="Number of Orders"
    )
    create_employee_transfer = fields.Boolean(
        related="stage_id.create_employee_transfer"
    )

    # budget_requisition_id = fields.Many2one('requisition.master', string='Budget Requisition',
    #                                         domain=[('requisition_type', '=', 'budget')])
    # master_requisition_ids = fields.One2many('requisition.master', 'budget_requisition_id',
    #                                          string='Master Requisitions',
    #                                          domain=[('requisition_type', '=', 'use')])
    # master_requisition_count = fields.Integer(compute='compute_master_requisition_count',
    #                                           string='No. of Master Requisitions')
    color = fields.Integer(string="Color Index", help="Color")
    is_fully_received = fields.Boolean(string='Is Fully Received', compute='compute_is_fully_received')
    approval_history_ids = fields.One2many('approval.history', 'requisition_id', string='Approval History',
                                           readonly=True)
    method = fields.Selection(
        [
            ('internal', 'Internal'),
            ('external', 'External')
        ], string='Requisition Method', tracking=True, default='internal'
    )
    master_requisition_domain_ids = fields.Binary(compute='_compute_master_requisition_domain_ids')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', domain="[('company_id', '=', company_id)]")
    warehouse_src_id = fields.Many2one('stock.warehouse', string='Source Warehouse',
                                       domain="[('company_id', '=', company_id)]")
    receiving_status = fields.Selection(selection=RECEIVING_STATUS, string='Receiving Status',
                                        compute='_compute_receiving_status', store=True)

    _sql_constraints = [('name_uniq', 'unique (name)', "Requisition name already exists !")]

    @api.depends('prod_serv_requisition_id.product_qty', 'prod_serv_requisition_id.received_qty', 'state', 'item_type')
    def _compute_receiving_status(self):
        for rec in self:
            if rec.state == 'approved' and rec.item_type == 'product':
                total_received_qty = sum(line.received_qty for line in rec.prod_serv_requisition_id)
                total_requested_qty = sum(line.product_qty for line in rec.prod_serv_requisition_id)
                if total_received_qty == 0:
                    rec.receiving_status = 'full_pending'
                elif total_received_qty < total_requested_qty:
                    rec.receiving_status = 'partial'
                elif total_received_qty >= total_requested_qty:
                    rec.receiving_status = 'full'
                    rec.action_close()

    @api.depends('requisition_type')
    def _compute_master_requisition_domain_ids(self):
        for rec in self:
            domain = self.get_master_req_domain(rec)

            master_requisitions_ids = self.env['requisition.master'].search(domain).ids
            rec.master_requisition_domain_ids = master_requisitions_ids

    def get_master_req_domain(self, rec):
        if rec.requisition_type in ('purchase', 'inventory'):
            domain = [("requisition_type", "=", "use"),
                      ("state", "=", "approved"),
                      ("item_type", "in", ("product", "service"))]

        else:
            domain = [("requisition_type", "=", "use"),
                      ("state", "=", "approved"),
                      ("item_type", "=", "product")]
        return domain

    @api.depends('prod_serv_requisition_id.remaining_qty')
    def compute_is_fully_received(self):
        for rec in self:
            if rec.item_type in ('product', 'service'):
                if any(rec.prod_serv_requisition_id.mapped('remaining_qty')):
                    rec.is_fully_received = False
                else:
                    rec.is_fully_received = True

            else:
                rec.is_fully_received = False

    def _compute_po_number(self):
        for requisition in self:
            requisition.po_count = len(requisition.purchase_ids)

    def _compute_purchase_requisition(self):
        for requisition in self:
            requisition.purchase_requisition_count = len(
                requisition.purchase_requisition_ids
            )

    def _compute_inventory_requisition(self):
        for requisition in self:
            requisition.inventory_requisition_count = len(
                requisition.inventory_requisition_ids
            )

    def _compute_transfer_number(self):
        for requisition in self:
            requisition.transfer_count = len(requisition.transfer_ids)

    # def compute_master_requisition_count(self):
    #     for requisition in self:
    #         requisition.master_requisition_count = len(requisition.master_requisition_ids)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env["approval.config"].search([], order=order)
        # search_domain = []
        # stage_ids = stages._search(
        #     search_domain, order=order, access_rights_uid=SUPERUSER_ID
        # )
        # return stages.browse(stage_ids)

    @api.onchange("requisition_type", "item_type")
    def onchange_type_id(self):
        for rec in self:
            domain_approval_conf = [("approval_type", "=", rec.requisition_type)]
            rec.stage_id = (
                self.env["approval.config"].search(domain_approval_conf, limit=1).id
            )
            if rec.requisition_type == "inventory":
                rec.item_type = "product"

    def _compute_agreement_number(self):
        for requisition in self:
            requisition.agreement_count = len(requisition.agreement_ids)

    @api.onchange("master_requisition")
    def onchange_master_requisition(self):
        for rec in self:
            if rec.requisition_type != "use" and rec.item_type in (
                    "product",
                    "service",
            ):
                req_type = rec.requisition_type
                if rec.master_requisition:
                    line_dict_list = self._prepare_requisition_line_vals(rec)
                    rec.prod_serv_requisition_id = [(6, 0, [])]
                    rec.prod_serv_requisition_id = [
                        (0, 0, dict_item) for dict_item in line_dict_list
                    ]
                    rec.requester_department_id = rec.master_requisition.requester_department_id.id
                    rec.description = rec.master_requisition.description
                    rec.date_required = rec.master_requisition.date_required
                    rec.warehouse_id = rec.master_requisition.warehouse_id.id
                else:
                    rec.prod_serv_requisition_id = [(6, 0, [])]
                    rec.master_requisition = False
                    rec.requisition_type = req_type
                    rec.description = ''
                    rec.date_required = fields.Datetime.today()

    # @api.onchange('budget_requisition_id')
    # def onchange_budget_requisition_id(self):
    #     for rec in self:
    #         if rec.requisition_type == 'use' and rec.item_type in (
    #                 "product",
    #                 "service",
    #         ):
    #             if rec.budget_requisition_id:
    #                 line_dict_list = self._prepare_master_requisition_line_vals(rec)
    #                 rec.prod_serv_requisition_id = [(6, 0, [])]
    #                 rec.prod_serv_requisition_id = [
    #                     (0, 0, dict_item) for dict_item in line_dict_list
    #                 ]
    #                 rec.requester_department_id = rec.budget_requisition_id.requester_department_id.id
    #             else:
    #                 rec.prod_serv_requisition_id = [(6, 0, [])]
    #                 rec.budget_requisition_id = False

    # def _prepare_master_requisition_line_vals(self, rec):
    #     line_dict_list = []
    #     for line in rec.budget_requisition_id.prod_serv_requisition_id:
    #         line_dict_list.append(
    #             {
    #                 "product_id": line.product_id,
    #                 "product_uom_id": line.product_uom_id,
    #                 # "product_qty": line.rem_budget_qty,
    #                 "requisition_id": rec.id,
    #                 # "budget_qty": line.budget_qty,
    #                 "received_qty": 0,
    #                 "reason": line.reason,
    #                 # "budget_requisition_line_id": line.id,
    #                 # 'periodic_budget_qty': line.periodic_budget_qty
    #             }
    #         )
    #     return line_dict_list

    @api.onchange("employee_id")
    def onchange_employee_id(self):
        if not self.employee_id:
            self.requester_department_id = False
        self.requester_department_id = self.employee_id.department_id

    def _prepare_requisition_line_vals(self, rec):
        line_dict_list = []
        for line in rec.master_requisition.prod_serv_requisition_id:
            if line.remaining_qty > 0:
                line_dict_list.append(
                    {
                        "product_id": line.product_id,
                        "product_uom_id": line.product_uom_id,
                        "product_qty": line.remaining_qty,
                        "requisition_id": rec.id,
                        # "budget_qty": line.budget_qty,
                        "received_qty": 0,
                        "reason": line.reason,
                        "master_requisition_line_id": line.id,
                        # 'periodic_budget_qty': line.periodic_budget_qty
                    }
                )
        return line_dict_list

    @api.constrains("prod_serv_requisition_id")
    def check_quantity(self):
        for rec in self:
            for line in rec.prod_serv_requisition_id:
                if line.product_qty <= 0:
                    raise ValidationError("Requesting Quantity can not be Zero or negative")

    # @api.constrains("requester_operating_unit", "budget_requisition_id", "master_requisition")
    # def check_operating_unit(self):
    #     for rec in self:
    #         if rec.requisition_type == 'use' and rec.budget_requisition_id:
    #             if rec.requester_operating_unit.id != rec.budget_requisition_id.requester_operating_unit.id:
    #                 raise ValidationError(
    #                     _('Budget operating unit and master requisition operating unit must be same.'))
    #         if rec.requisition_type not in ('use', 'budget') and rec.master_requisition:
    #             if rec.requester_operating_unit.id != rec.master_requisition.requester_operating_unit.id:
    #                 raise ValidationError(
    #                     _('Requesting operating unit and master requisition operating unit must be same.'))

    def _compute_user_can_approve(self):
        for records in self:
            if records.sudo().stage_id.self_approval:
                if self.env.user in records.initiator_id:
                    records.sudo().user_can_approve = True
                    return
            records.sudo().user_can_approve = records.sudo().stage_id.user_can_approve

    def confirm(self):
        for records in self:
            records.sudo().write({"state": "confirmed"})
            if records.stage_id.self_approval:
                records.approve()

    def approve(self):
        for records in self:
            history_data = {
                'action_type': 'approval',
                'from_stage': records.stage_id.id,
                'to_stage': records.next_stage_id.id,
                'requisition_id': records.id,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now()
            }
            if not records.next_stage_id.final_stage:

                res = records.write(  # noqa
                    {
                        "state": "confirmed",
                        "stage_id": records.next_stage_id,
                    }
                )
            elif records.next_stage_id.final_stage:
                vals = records.write(  # noqa
                    {"state": "approved", "stage_id": records.next_stage_id}
                )

            self.env['approval.history'].create(history_data)

    def action_cancel(self):
        for record in self:
            if not record.state == "cancel":
                record.state = "cancel"
                history_data = {
                    'action_type': 'cancel',
                    'from_stage': record.stage_id.id,
                    'to_stage': False,
                    'requisition_id': record.id,
                    'user_id': self.env.user.id,
                    'date': fields.Datetime.now()
                }
                self.env['approval.history'].create(history_data)
            else:
                raise ValidationError(_("This Requisition is already in Cancel Stage"))

    def action_draft(self):
        for record in self:
            if record.state == "cancel":
                record.state = "draft"
                history_data = {
                    'action_type': 'reset',
                    'from_stage': record.stage_id.id,
                    'to_stage': False,
                    'requisition_id': record.id,
                    'user_id': self.env.user.id,
                    'date': fields.Datetime.now()
                }
                new_stage_id = self.env["approval.config"].search(
                    [("approval_type", "=", self.requisition_type)],
                    order="sequence asc",
                    limit=1,
                )
                record.stage_id = new_stage_id.id
                history_data['to_stage'] = new_stage_id.id
                self.env['approval.history'].create(history_data)

            else:
                raise ValidationError(
                    _("Requisition can only be set to draft from cancel stage")
                )

    def action_close(self):
        self.ensure_one()
        if self.state == 'approved':
            self.state = 'closed'

    def unlink(self):
        for req in self:
            if req.state != "draft":
                raise ValidationError(
                    _("Requisition can be deleted only in draft mode")
                )
        return super(RequisitionMain, self).unlink()

    # def create_transfer(self):
    #     pass

    ###################### APPROVAL PROCESS CODE END ##################### noqa

    @api.model
    def create(self, vals):
        # We generate a standard reference
        if vals.get('name', '/') == '/':
            requisition_type = vals.get('requisition_type')

            if requisition_type == 'use':
                sequence = self.env["ir.sequence"].next_by_code("requisition.master")

            elif requisition_type == 'purchase':
                sequence = self.env["ir.sequence"].next_by_code("requisition.purchase")

            elif requisition_type == 'inventory':
                sequence = self.env["ir.sequence"].next_by_code("requisition.inventory")

            else:
                sequence = '/'

            if sequence != '/':

                code = 'REQ-'

                if vals.get('requester_department_id'):
                    dept_name = self.env["hr.department"].browse(vals.get('requester_department_id')).name[:3].upper()
                    code += dept_name + "-"

                code += sequence
            else:
                code = sequence
            vals['name'] = code

        if vals.get("item_type") and vals.get("item_type") in (
                "product",
                "service",
        ):
            if not (
                    vals.get("prod_serv_requisition_id")
            ):
                raise UserError(_("You cannot create an empty requisition!"))
        if vals.get("requisition_type") == "purchase" and not self.user_has_groups(
                "misl_requisition.misl_requisition_purchase"
        ):
            raise UserError(_("You dont have access to create Purchase Requisition"))
        if vals.get("requisition_type") == "use" and not self.user_has_groups(
                "misl_requisition.misl_requisition_master"
        ):
            raise UserError(_("You dont have access to create Master Requisition"))
        if vals.get("requisition_type") == "inventory" and not self.user_has_groups(
                "misl_requisition.misl_requisition_inventory"
        ):
            raise UserError(_("You dont have access to create Inventory Requisition"))

        requisition = super(RequisitionMain, self).create(vals)

        approval_history = self.env['approval.history'].create(
            {
                'action_type': 'create',
                'from_stage': False,
                'to_stage': requisition.stage_id.id,
                'requisition_id': requisition.id,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now()
            }
        )

        return requisition

    ##################################### Requisition Report #########################################

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(RequisitionMain, self).fields_view_get(
    #         view_id=view_id,
    #         view_type=view_type,
    #         toolbar=toolbar,
    #         submenu=submenu)

    #     if view_type=='form':
    #         view_vals = res.get('view_id', False) and self.env['ir.ui.view'].browse(res['view_id']).read()[0] or {}
    #         field_value = view_vals.get('state', False)    
    #         if res.get('toolbar', False) and res.get('toolbar').get('print', False):
    #             reports = res.get('toolbar').get('print')
    #             for report in reports:
    #                 if report.get('report_file', False) and report.get('report_file') == 'misl_requisition.report_requisition':
    #                     res['toolbar']['print'].remove(report)

    #     return res

    def get_approval_history(self):
        for rec in self:
            approval_history_dict_list = []
            if rec.approval_history_ids:
                for approval in reversed(rec.approval_history_ids):
                    if approval.action_type == 'approval' and approval.to_stage.final_stage:
                        action = 'final_approval'
                    elif approval.action_type == 'approval' and not approval.to_stage.final_stage:
                        action = 'approval'
                    elif approval.action_type == 'cancel' or approval.action_type == 'create':
                        break

                    approver_employee_id = self.env['hr.employee'].search([('user_id', '=', approval.user_id.id)])
                    approval_history_dict = {
                        'employee': approver_employee_id,
                        'user': approval.user_id,
                        'action': action,
                    }
                    approval_history_dict_list.append(approval_history_dict)
            return approval_history_dict_list

    def download_requisition(self):
        return self.env.ref('misl_requisition.report_requisition').report_action(self)

    def batch_approve(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(_('You cannot approve this order'))
            rec.approve()
