from odoo import models, fields, api, _
import datetime
from odoo.exceptions import ValidationError


class InheritPurchaseRequisition(models.Model):
    _order = 'id desc'
    _inherit = 'purchase.requisition'

    custom_requisition_id = fields.Many2one('requisition.master', string="Requisition Reference")

    @api.onchange('custom_requisition_id')
    def onchange_custom_requisition_id(self):
        for rec in self:
            if rec.custom_requisition_id:
                # noinspection PyUnresolvedReferences
                rec.date_end = rec.custom_requisition_id.date_required
                rec.ordering_date = datetime.date.today()
                rec.schedule_date = rec.custom_requisition_id.date_required
                rec.company_id = rec.company_id

                line_dict_list = []
                for line in rec.custom_requisition_id.prod_serv_requisition_id:
                    line_vals = {
                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty - line.received_qty,
                        'product_uom_id': line.product_uom_id.id,
                        'schedule_date': rec.custom_requisition_id.date_required,
                        'custom_requisition_line_id': line.id
                    }
                    line_dict_list.append(line_vals)
                rec.line_ids = [(6, 0, [])]
                rec.line_ids = [(0, 0, dict_item) for dict_item in line_dict_list]

                if rec.custom_requisition_id.master_requisition:
                    rec.origin = rec.custom_requisition_id.master_requisition.name
                else:
                    rec.origin = rec.custom_requisition_id.name

            else:
                rec.custom_requisition_id = False
                rec.date_end = None
                rec.ordering_date = False
                rec.origin = False
                rec.schedule_date = False
                rec.line_ids = [(6, 0, [])]
                rec.warehouse_id = False
                rec.picking_type_id = False



class InheritPurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    custom_requisition_line_id = fields.Many2one('requisition.product.service', string='Requisition Line ID')

    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        res = super(InheritPurchaseRequisitionLine, self)._prepare_purchase_order_line(name, product_qty, price_unit, taxes_ids)
        res['custom_requisition_line_id'] = self.custom_requisition_line_id.id
        return res




