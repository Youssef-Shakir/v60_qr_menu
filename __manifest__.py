{
    'name': 'V60 QR Menu',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Custom QR Menu with V60 Café Design',
    'description': """
        A custom QR menu module that displays POS products with
        the V60 Café design theme. Features include:
        - Beautiful black and white menu design
        - Categories with styled headers
        - Wavy line separators for items
        - Mobile-responsive layout
        - QR code generation for easy access
    """,
    'author': 'V60 Café',
    'website': '',
    'depends': ['point_of_sale', 'pos_restaurant'],
    'data': [
        'security/ir.model.access.csv',
        'views/v60_menu_config_views.xml',
        'views/v60_menu_template.xml',
        'views/v60_qr_code_views.xml',
        'views/menu_items.xml',
    ],
    'assets': {
        'v60_qr_menu.assets_frontend': [
            'v60_qr_menu/static/src/css/v60_menu.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
