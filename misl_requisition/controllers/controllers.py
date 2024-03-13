# -*- coding: utf-8 -*-
# from odoo import http


# class EvlRequisition(http.Controller):
#     @http.route('/evl_requisition/evl_requisition', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evl_requisition/evl_requisition/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('evl_requisition.listing', {
#             'root': '/evl_requisition/evl_requisition',
#             'objects': http.request.env['evl_requisition.evl_requisition'].search([]),
#         })

#     @http.route('/evl_requisition/evl_requisition/objects/<model("evl_requisition.evl_requisition"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evl_requisition.object', {
#             'object': obj
#         })
