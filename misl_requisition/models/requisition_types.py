from odoo import api, fields, models, _


class ProductServiceRequisition(models.Model):
    """
    This model is responsible for product and service requisition related data and workflows.

    """
    _name = 'requisition.product.service'
    _order = 'id desc'
    _description = 'This model is used for product and service requisition management.'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1) 

    requisition_id = fields.Many2one('requisition.master', ondelete='cascade',)
    requisition_reference = fields.Char(related="requisition_id.name")

    employee_id = fields.Many2one('hr.employee', 'Requisitioner', related='requisition_id.employee_id')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company, index=True,
                                 readonly=True)
    requisition_type = fields.Selection([
        ('use', "Master"),
        ('inventory', "Inventory"),
        ('purchase', "Purchase"),
        ('recruit', "Manpower"),
    ], related='requisition_id.requisition_type', string='Requisition Type')

    item_type = fields.Selection(related='requisition_id.item_type', string='Item Type')

    product_id = fields.Many2one('product.product', 'Item', required=True)
    default_code = fields.Char(related='product_id.default_code', string="Internal Reference")
    description = fields.Many2many(related='product_id.product_template_variant_value_ids', string="Description")
    product_qty = fields.Float('Requesting Quantity', digits='Product Unit of Measure', default=1.0, required=True)
    remaining_qty = fields.Float('Remaining Quantity', digits='Product Unit of Measure',
                                 compute='_compute_remaining_qty', store=True)
    received_qty = fields.Float('Received Qty', digits='Product Unit of Measure',
                                compute='_compute_qty_delivered', store=True, recursive=True)
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    delivery_date = fields.Date(string='Receiving Date')
    reason = fields.Char(string="Reason")
    purchase_line_ids = fields.One2many('purchase.order.line', 'custom_requisition_line_id', string='Purchase lines')
    move_ids = fields.One2many('stock.move', 'requisition_line_id', string='Stock Moves')
    master_requisition_line_id = fields.Many2one('requisition.product.service', string='Master Requisition Line Id')
    requisition_line_ids = fields.One2many('requisition.product.service', 'master_requisition_line_id',
                                           string='Requisition Line Ids',
                                           help='Requisition Line Ids that belongs to a master requisition line id')
    qty_in_hand = fields.Float(string='Quantity In Hand', digits='Product Unit of Measure')
    product_domain_ids = fields.Binary(compute='_compute_product_domain_ids')

    @api.depends('requisition_id.item_type')
    def _compute_product_domain_ids(self):
        for rec in self:
            if rec.requisition_id.item_type == "service":
                rec.product_domain_ids = self.env['product.product'].search([('detailed_type', '=', 'service')]).ids
            elif rec.requisition_id.item_type == "product":
                domain = [
                    ('detailed_type', 'in', ['consu', 'product']),
                ]
                rec.product_domain_ids = self.env['product.product'].search(domain).ids
            else:
                rec.product_domain_ids = []

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.product_uom_id = rec.product_id.uom_id.id if rec.product_id else False

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom',
                 'purchase_line_ids.qty_received', 'requisition_line_ids.received_qty')
    def _compute_qty_delivered(self):
        print('Calculating Received Qty')
        for line in self:
            # TODO: maybe one day, this should be done in SQL for performance sake
            # if line.requisition_type == 'budget':
            #     line.received_qty = sum(l.received_qty for l in line.budget_requisition_line_ids)
            if line.requisition_type == 'use':
                line.received_qty = sum(l.received_qty for l in line.requisition_line_ids)
            elif line.requisition_type == 'inventory':
                qty = 0.0
                outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
                for move in outgoing_moves:
                    if move.state != 'done':
                        continue
                    qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom_id,
                                                              rounding_method='HALF-UP')
                for move in incoming_moves:
                    if move.state != 'done':
                        continue
                    qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom_id,
                                                              rounding_method='HALF-UP')
                line.received_qty = qty
            elif line.requisition_type == 'purchase':
                line.received_qty = sum(purchase_line.qty_received for purchase_line in line.purchase_line_ids)
            else:
                line.received_qty = 0.0

    def action_open_quants(self):
        self.ensure_one()
        action = self.product_id.action_open_quants()
        action['name'] = _('Available Quantity')
        action['context'].update({'create': False, 'edit': False})
        return action

    @api.depends('product_qty', 'received_qty')
    def _compute_remaining_qty(self):
        for rec in self:
            rec.remaining_qty = rec.product_qty - rec.received_qty

    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        moves = self.move_ids.filtered(
            lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id)

        for move in moves:
            if move.location_dest_id.warehouse_id.id == self.requisition_id.warehouse_id.id:
                incoming_moves |= move
            elif move.location_id.warehouse_id.id == self.requisition_id.warehouse_id.id:
                outgoing_moves |= move

        return outgoing_moves, incoming_moves

    @api.model
    def create(self, vals):
        create_note = ''
        if vals.get('product_id'):
            product_name = self.env['product.product'].browse(vals['product_id']).name
            create_note = u'\u2022' + " Product Added. Name: {}, Requesting Qty: {} ".format(product_name, str(vals.get('product_qty', 0)))
        result = super(ProductServiceRequisition, self).create(vals)
        if len(create_note) > 0:
            result.requisition_id.message_post(body=create_note)

        return result

    def write(self, vals):
        tracking_notes = []
        if vals.get('product_qty'):
            qty_notes = "\t\t" + u'\u2022' + " Requested Quantity Updated for Product {}".format(self.product_id.display_name) + "\n" + str(self.product_qty) + u'\u2192' + str(vals['product_qty'])
            tracking_notes += [qty_notes]
        if vals.get('product_id'):
            product_change_notes = "\t\t" + u'\u2022' + " Product Changed" + "\n"  + str(self.product_id.name) + u'\u2192' + self.env['product.product'].browse(vals['product_id']).name
            tracking_notes += [product_change_notes]

        result = super(ProductServiceRequisition, self).write(vals)
        for note in tracking_notes:
            self.requisition_id.message_post(body=note)

        return result

    def unlink(self):
        for rec in self:
            delete_note = u'\u2022' + "Product Deleted. Name: {}, Requesting Qty: {} ".format(rec.product_id.name, str(rec.product_qty))
            rec.requisition_id.message_post(body=delete_note)
        return super(ProductServiceRequisition, self).unlink()

    # @api.depends('received_qty', 'budget_qty')
    # def compute_rem_budget_qty(self):
    #     for rec in self:
    #         if rec.requisition_type == 'budget':
    #             rec.rem_budget_qty = rec.budget_qty - sum(mr.received_qty for mr in rec.budget_requisition_line_ids)
    #         elif rec.requisition_type == 'use':
    #             rec.rem_budget_qty = rec.budget_requisition_line_id.rem_budget_qty\
    #                 if rec.budget_requisition_line_id else 0
    #         else:
    #             if rec.master_requisition_line_id:
    #                 rec.rem_budget_qty = rec.master_requisition_line_id.budget_requisition_line_id.rem_budget_qty\
    #                     if rec.master_requisition_line_id.budget_requisition_line_id else 0
    #             else:
    #                 rec.rem_budget_qty = 0
