
# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_misl_requisition_sale_order = fields.Boolean("Create Requisition from Sales Order")
    module_misl_requisition_mo = fields.Boolean("Use Requisition for Manufacturing Order")
    module_misl_requisition_bill = fields.Boolean("Use Requisition for Vendor Bill Register Payment")
