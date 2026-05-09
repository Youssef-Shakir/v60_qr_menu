from odoo import models, fields


class V60MenuItem(models.Model):
    _name = 'v60.menu.item'
    _description = 'V60 Manual Menu Item'
    _order = 'section, category_name, sequence, id'

    menu_config_id = fields.Many2one('v60.menu.config', string='Menu Configuration',
                                      required=True, ondelete='cascade')
    name = fields.Char(string='Item Name', required=True)
    price = fields.Float(string='Price', required=True, digits=(12, 2))
    description = fields.Text(string='Description')
    category_name = fields.Char(string='Category', required=True,
                                help='Category name to group items under (e.g., "HOT BEVERAGES", "COLD COFFEE")')
    section = fields.Selection([
        ('light', 'Light Section (White Background)'),
        ('dark', 'Dark Section (Black Background)'),
    ], string='Section', required=True, default='light',
       help='Which section of the menu to display this item in')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
