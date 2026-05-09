import uuid
from odoo import models, fields, api


class V60MenuConfig(models.Model):
    _name = 'v60.menu.config'
    _description = 'V60 QR Menu Configuration'

    name = fields.Char(string='Menu Name', required=True, default='V60 Café Menu')
    pos_config_id = fields.Many2one('pos.config', string='POS Configuration', required=True,
                                     help='Select the POS configuration to fetch products from')
    active = fields.Boolean(default=True)
    access_token = fields.Char(string='Access Token', copy=False, readonly=True)

    # Branding
    logo = fields.Binary(string='Logo', attachment=True)
    cafe_name = fields.Char(string='Café Name', default='V60 Café')
    instagram_url = fields.Char(string='Instagram URL', help='Full Instagram profile URL (e.g., https://instagram.com/v60cafe)')

    # Colors (following the V60 design)
    primary_bg_color = fields.Char(string='Primary Background', default='#FFFFFF',
                                    help='Background color for hot beverages section')
    secondary_bg_color = fields.Char(string='Secondary Background', default='#000000',
                                      help='Background color for cold beverages section')
    primary_text_color = fields.Char(string='Primary Text Color', default='#000000')
    secondary_text_color = fields.Char(string='Secondary Text Color', default='#FFFFFF')

    # Category mappings - Light sections (white background)
    hot_category_ids = fields.Many2many(
        'pos.category',
        'v60_menu_hot_category_rel',
        'menu_id',
        'category_id',
        string='Light Section Categories',
        help='Categories to display in the light section (white background)'
    )
    # Category mappings - Dark sections (black background)
    cold_category_ids = fields.Many2many(
        'pos.category',
        'v60_menu_cold_category_rel',
        'menu_id',
        'category_id',
        string='Dark Section Categories',
        help='Categories to display in the dark section (black background)'
    )

    # Currency
    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)

    # URL fields
    menu_url = fields.Char(string='Menu URL', compute='_compute_menu_url', store=False)
    qr_code_url = fields.Char(string='QR Code URL', compute='_compute_qr_code_url', store=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('access_token'):
                vals['access_token'] = uuid.uuid4().hex[:16]
        return super().create(vals_list)

    def _generate_access_token(self):
        """Generate a new access token"""
        for record in self:
            record.access_token = uuid.uuid4().hex[:16]

    def action_regenerate_token(self):
        """Button action to regenerate access token"""
        self._generate_access_token()
        return True

    def _compute_menu_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.menu_url = f"{base_url}/v60-menu/{record.id}?token={record.access_token}"

    def _compute_qr_code_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            menu_url = f"{base_url}/v60-menu/{record.id}?token={record.access_token}"
            record.qr_code_url = f"/report/barcode/QR/{menu_url}?width=300&height=300"

    def get_menu_data(self):
        """Get all menu data for rendering"""
        self.ensure_one()

        # Get hot beverage products
        hot_products = []
        if self.hot_category_ids:
            hot_domain = [
                ('available_in_pos', '=', True),
                ('pos_categ_ids', 'in', self.hot_category_ids.ids),
            ]
            hot_products = self.env['product.product'].sudo().search(hot_domain, order='sequence, name')

        # Get cold beverage products
        cold_products = []
        if self.cold_category_ids:
            cold_domain = [
                ('available_in_pos', '=', True),
                ('pos_categ_ids', 'in', self.cold_category_ids.ids),
            ]
            cold_products = self.env['product.product'].sudo().search(cold_domain, order='sequence, name')

        # Group by category
        hot_by_category = {}
        for product in hot_products:
            for categ in product.pos_categ_ids:
                if categ.id in self.hot_category_ids.ids:
                    if categ.name not in hot_by_category:
                        hot_by_category[categ.name] = []
                    hot_by_category[categ.name].append({
                        'id': product.id,
                        'name': product.name,
                        'price': product.lst_price,
                        'description': product.description_sale or '',
                    })
                    break

        cold_by_category = {}
        for product in cold_products:
            for categ in product.pos_categ_ids:
                if categ.id in self.cold_category_ids.ids:
                    if categ.name not in cold_by_category:
                        cold_by_category[categ.name] = []
                    cold_by_category[categ.name].append({
                        'id': product.id,
                        'name': product.name,
                        'price': product.lst_price,
                        'description': product.description_sale or '',
                    })
                    break

        return {
            'config': {
                'id': self.id,
                'name': self.name,
                'cafe_name': self.cafe_name,
                'logo': self.logo,
                'primary_bg_color': self.primary_bg_color,
                'secondary_bg_color': self.secondary_bg_color,
                'primary_text_color': self.primary_text_color,
                'secondary_text_color': self.secondary_text_color,
                'currency_symbol': self.currency_id.symbol,
                'currency_position': self.currency_id.position,
            },
            'hot_categories': hot_by_category,
            'cold_categories': cold_by_category,
        }
