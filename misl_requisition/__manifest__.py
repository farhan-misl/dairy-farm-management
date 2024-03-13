# -*- coding: utf-8 -*-
{
    "name": "Requisition Management",
    "summary": """
       Requisition Management.""",
    "description": """
        This module contains requisition related customization with specific workflow.
    """,
    "author": "MISL",
    "website": "",
    "category": "Procurement",
    "version": "16.0.0.3",
    "application": True,
    # any module necessary for this one to work correctly
    "depends": [
        "purchase",
        "hr",
        "uom",
        "stock_account",
        "purchase_stock",
        "purchase_requisition",
        "purchase_requisition_stock",
        "misl_approval"
    ],
    # always loaded
    "data": [
        "security/requisition_approval_security.xml",
        "security/ir.model.access.csv",
        # "security/requisition_record_rules.xml",
        "data/approval_type.xml",
        "views/requisition_views.xml",
        "views/requisition_sequences.xml",
        "views/product_service_requisition_line_view.xml",
        "views/approval_config_view.xml",
        "views/requisition_menus.xml",
        "views/res_config.xml",
        "views/inherit_purchase_order_view.xml",
        "views/inherit_stock_picking_view.xml",
        "views/inherit_stock_picking_views.xml",

        "views/requisition_form_format.xml",  
        "report/requisition_form.xml",
        "report/requisition_form_table_layout_template.xml",
        "views/inherit_purchase_requisition.xml"
        
    ],
    "assets": {
            "web.assets_backend": [
                "misl_requisition/static/src/css/custom_style.css",
            ],
        },
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
    "license": "LGPL-3",
}
