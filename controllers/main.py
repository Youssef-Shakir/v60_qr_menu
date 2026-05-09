from odoo import http
from odoo.http import request


class V60MenuController(http.Controller):

    @http.route(['/v60-menu/<int:config_id>'], type='http', auth='public', website=True, sitemap=False)
    def v60_landing_page(self, config_id, token=None, **kwargs):
        """Landing page with Menu and Instagram options"""
        menu_config = request.env['v60.menu.config'].sudo().browse(config_id)

        if not menu_config.exists() or not menu_config.active:
            return request.not_found()

        # Validate token
        if menu_config.access_token and token != menu_config.access_token:
            return request.not_found()

        # Convert logo to base64 for template
        logo_base64 = None
        if menu_config.logo:
            logo_base64 = menu_config.logo.decode('utf-8') if isinstance(menu_config.logo, bytes) else menu_config.logo

        # Build menu URL with token
        menu_url = f"/v60-menu/{config_id}/menu?token={token}" if token else f"/v60-menu/{config_id}/menu"

        return request.render('v60_qr_menu.v60_landing_page', {
            'menu_config': menu_config,
            'logo_base64': logo_base64,
            'menu_url': menu_url,
            'instagram_url': menu_config.instagram_url,
        })

    @http.route(['/v60-menu/<int:config_id>/menu'], type='http', auth='public', website=True, sitemap=False)
    def v60_menu_page(self, config_id, token=None, **kwargs):
        """Main QR menu page"""
        menu_config = request.env['v60.menu.config'].sudo().browse(config_id)

        if not menu_config.exists() or not menu_config.active:
            return request.not_found()

        # Validate token
        if menu_config.access_token and token != menu_config.access_token:
            return request.not_found()

        # Get menu data
        menu_data = menu_config.get_menu_data()

        # Convert logo to base64 for template
        logo_base64 = None
        if menu_config.logo:
            logo_base64 = menu_config.logo.decode('utf-8') if isinstance(menu_config.logo, bytes) else menu_config.logo

        return request.render('v60_qr_menu.v60_menu_page', {
            'menu_config': menu_config,
            'menu_data': menu_data,
            'logo_base64': logo_base64,
        })

    @http.route(['/v60-menu/print-qr/<int:config_id>'], type='http', auth='user', website=False)
    def print_qr_code(self, config_id, **kwargs):
        """Print QR code page for backend users"""
        menu_config = request.env['v60.menu.config'].sudo().browse(config_id)

        if not menu_config.exists():
            return request.not_found()

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_url = f"{base_url}/v60-menu/{menu_config.id}?token={menu_config.access_token}"

        return request.render('v60_qr_menu.v60_qr_code_page', {
            'menu_config': menu_config,
            'menu_url': menu_url,
            'base_url': base_url,
        })
