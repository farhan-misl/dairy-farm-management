# -*- coding: utf-8 -*-
{
    "name": "MISL Approvals",
    "summary": "Create and validate approvals requests",
    "description": """
        Manage your dynamic approval activities
    """,
    "author": "Mir Info Systems Ltd.",
    "website": "https://www.mirinfosys.com",
    "category": "Human Resources/Approvals",
    "version": "0.1",
    "depends": ["base", "hr"],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/approval_config_view.xml",
        "views/approval_module_view.xml",
        "views/approval_type_view.xml",
    ],
    "application": True,
    "license": "LGPL-3",
}
