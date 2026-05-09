from odoo import http, SUPERUSER_ID
from odoo.http import request, Response
from odoo import registry as odoo_registry
from odoo.api import Environment
import json


class V60MenuController(http.Controller):

    def _get_menu_config_direct(self, db_name, config_id, token):
        """Get menu config by directly accessing the database registry"""
        try:
            reg = odoo_registry(db_name)
            with reg.cursor() as cr:
                env = Environment(cr, SUPERUSER_ID, {})
                menu_config = env['v60.menu.config'].browse(config_id)

                if not menu_config.exists() or not menu_config.active:
                    return None, None, "not_found"

                # Validate token
                if menu_config.access_token and token != menu_config.access_token:
                    return None, None, "invalid_token"

                # Get logo
                logo_base64 = None
                if menu_config.logo:
                    logo_base64 = menu_config.logo.decode('utf-8') if isinstance(menu_config.logo, bytes) else menu_config.logo

                # Build config data dict (to use outside cursor context)
                config_data = {
                    'id': menu_config.id,
                    'cafe_name': menu_config.cafe_name or 'V60 Café',
                    'instagram_url': menu_config.instagram_url,
                    'access_token': menu_config.access_token,
                }

                return config_data, logo_base64, None
        except Exception as e:
            return None, None, str(e)

    def _get_menu_data_direct(self, db_name, config_id, token):
        """Get full menu data by directly accessing the database registry"""
        try:
            reg = odoo_registry(db_name)
            with reg.cursor() as cr:
                env = Environment(cr, SUPERUSER_ID, {})
                menu_config = env['v60.menu.config'].browse(config_id)

                if not menu_config.exists() or not menu_config.active:
                    return None, None, None, "not_found"

                # Validate token
                if menu_config.access_token and token != menu_config.access_token:
                    return None, None, None, "invalid_token"

                # Get logo
                logo_base64 = None
                if menu_config.logo:
                    logo_base64 = menu_config.logo.decode('utf-8') if isinstance(menu_config.logo, bytes) else menu_config.logo

                # Get menu data
                menu_data = menu_config.get_menu_data()

                # Build config data dict
                config_data = {
                    'id': menu_config.id,
                    'cafe_name': menu_config.cafe_name or 'V60 Café',
                    'instagram_url': menu_config.instagram_url,
                }

                return config_data, menu_data, logo_base64, None
        except Exception as e:
            return None, None, None, str(e)

    @http.route(['/v60-menu/<int:config_id>'], type='http', auth='none', methods=['GET'], csrf=False, sitemap=False)
    def v60_landing_page(self, config_id, token=None, db=None, **kwargs):
        """Landing page with Menu and Instagram options"""
        # Get database name from parameter or try to detect it
        db_name = db
        if not db_name:
            # Try to get from request if available
            if request.db:
                db_name = request.db
            else:
                return Response("Database not specified. Please use a URL with &db=your_database",
                               content_type='text/plain', status=400)

        config_data, logo_base64, error = self._get_menu_config_direct(db_name, config_id, token)

        if error == "not_found":
            return Response("Menu not found", content_type='text/plain', status=404)
        if error == "invalid_token":
            return Response("Invalid access token", content_type='text/plain', status=403)
        if error:
            return Response(f"Error: {error}", content_type='text/plain', status=500)

        # Build menu URL with token and db
        menu_url = f"/v60-menu/{config_id}/menu?token={token}&db={db_name}"

        html = self._render_landing_page(config_data, logo_base64, menu_url)
        return Response(html, content_type='text/html')

    @http.route(['/v60-menu/<int:config_id>/menu'], type='http', auth='none', methods=['GET'], csrf=False, sitemap=False)
    def v60_menu_page(self, config_id, token=None, db=None, **kwargs):
        """Main QR menu page"""
        # Get database name from parameter or try to detect it
        db_name = db
        if not db_name:
            if request.db:
                db_name = request.db
            else:
                return Response("Database not specified. Please use a URL with &db=your_database",
                               content_type='text/plain', status=400)

        config_data, menu_data, logo_base64, error = self._get_menu_data_direct(db_name, config_id, token)

        if error == "not_found":
            return Response("Menu not found", content_type='text/plain', status=404)
        if error == "invalid_token":
            return Response("Invalid access token", content_type='text/plain', status=403)
        if error:
            return Response(f"Error: {error}", content_type='text/plain', status=500)

        html = self._render_menu_page(config_data, menu_data, logo_base64)
        return Response(html, content_type='text/html')

    @http.route(['/v60-menu/print-qr/<int:config_id>'], type='http', auth='user')
    def print_qr_code(self, config_id, **kwargs):
        """Print QR code page for backend users"""
        menu_config = request.env['v60.menu.config'].sudo().browse(config_id)

        if not menu_config.exists():
            return request.not_found()

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        db_name = request.env.cr.dbname
        menu_url = f"{base_url}/v60-menu/{menu_config.id}?token={menu_config.access_token}&db={db_name}"

        return request.render('v60_qr_menu.v60_qr_code_page', {
            'menu_config': menu_config,
            'menu_url': menu_url,
            'base_url': base_url,
        })

    def _render_landing_page(self, config_data, logo_base64, menu_url):
        """Render landing page as plain HTML"""
        logo_html = ''
        if logo_base64:
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Logo"/>'
        else:
            logo_html = '''<div>
                <div class="v60-landing-logo-text">V60</div>
                <div class="v60-landing-logo-sub">Café</div>
            </div>'''

        instagram_html = ''
        if config_data.get('instagram_url'):
            instagram_html = f'''
            <a href="{config_data['instagram_url']}" target="_blank" class="v60-landing-btn v60-landing-btn-instagram">
                <svg class="v60-instagram-icon" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
                Follow us on Instagram
            </a>'''

        cafe_name = config_data.get('cafe_name', 'V60 Café')

        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{cafe_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&family=Lora:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            min-height: 100vh;
            background: linear-gradient(135deg, #1a1a1a 0%, #000000 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            font-family: 'Lora', 'Georgia', serif;
        }}
        .v60-landing-card {{
            text-align: center;
            max-width: 350px;
            width: 100%;
        }}
        .v60-landing-logo {{
            width: 120px;
            height: 120px;
            margin: 0 auto 30px;
            border: 3px solid #ffffff;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #000000;
            overflow: hidden;
        }}
        .v60-landing-logo img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .v60-landing-logo-text {{
            color: #ffffff;
            font-size: 36px;
            font-weight: bold;
        }}
        .v60-landing-logo-sub {{
            color: #ffffff;
            font-size: 12px;
        }}
        .v60-landing-title {{
            font-family: 'Dancing Script', cursive;
            font-size: 42px;
            color: #ffffff;
            margin-bottom: 10px;
        }}
        .v60-landing-subtitle {{
            font-size: 16px;
            color: #888888;
            margin-bottom: 50px;
        }}
        .v60-landing-btn {{
            display: block;
            width: 100%;
            padding: 18px 30px;
            margin-bottom: 15px;
            font-family: 'Lora', serif;
            font-size: 18px;
            font-weight: 500;
            text-decoration: none;
            border-radius: 30px;
            transition: all 0.3s ease;
            cursor: pointer;
            border: 2px solid #ffffff;
        }}
        .v60-landing-btn-menu {{
            background: #ffffff;
            color: #000000;
        }}
        .v60-landing-btn-menu:hover {{
            background: #f0f0f0;
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(255,255,255,0.2);
        }}
        .v60-landing-btn-instagram {{
            background: transparent;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        .v60-landing-btn-instagram:hover {{
            background: rgba(255,255,255,0.1);
            transform: translateY(-2px);
        }}
        .v60-instagram-icon {{
            width: 24px;
            height: 24px;
        }}
    </style>
</head>
<body>
    <div class="v60-landing-card">
        <div class="v60-landing-logo">
            {logo_html}
        </div>
        <h1 class="v60-landing-title">{cafe_name}</h1>
        <p class="v60-landing-subtitle">Welcome</p>
        <a href="{menu_url}" class="v60-landing-btn v60-landing-btn-menu">View Menu</a>
        {instagram_html}
    </div>
</body>
</html>'''

    def _render_menu_page(self, config_data, menu_data, logo_base64):
        """Render menu page as plain HTML"""
        logo_html = ''
        if logo_base64:
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Logo"/>'
        else:
            logo_html = '''<div>
                <div class="v60-logo-text">V60</div>
                <div class="v60-logo-subtext">Café</div>
            </div>'''

        cafe_name = config_data.get('cafe_name', 'V60 Café')

        # Build hot categories HTML
        hot_html = ''
        if menu_data.get('hot_categories'):
            hot_items = ''
            for cat_name, products in menu_data['hot_categories'].items():
                items_html = ''
                for product in products:
                    price = '{:,.0f}'.format(product['price'])
                    items_html += f'''
                    <li class="v60-menu-item">
                        <span class="v60-item-name v60-item-name-light">{product['name']}</span>
                        <span class="v60-item-line v60-item-line-wavy"></span>
                        <span class="v60-item-price v60-item-price-light">{price}</span>
                    </li>'''
                hot_items += f'''
                <div class="v60-category-header">
                    <span class="v60-category-title v60-category-title-light">{cat_name}</span>
                </div>
                <ul class="v60-menu-items">{items_html}</ul>'''
            hot_html = f'<div class="v60-section-light">{hot_items}</div>'

        # Build cold categories HTML
        cold_html = ''
        if menu_data.get('cold_categories'):
            cold_items = ''
            for cat_name, products in menu_data['cold_categories'].items():
                items_html = ''
                for product in products:
                    price = '{:,.0f}'.format(product['price'])
                    items_html += f'''
                    <li class="v60-menu-item">
                        <span class="v60-item-name v60-item-name-dark">{product['name']}</span>
                        <span class="v60-item-line v60-item-line-wavy v60-item-line-wavy-dark"></span>
                        <span class="v60-item-price v60-item-price-dark">{price}</span>
                    </li>'''
                cold_items += f'''
                <div class="v60-dark-category">
                    <div class="v60-category-header">
                        <span class="v60-category-title v60-category-title-dark">{cat_name}</span>
                    </div>
                    <ul class="v60-menu-items">{items_html}</ul>
                </div>'''
            cold_html = f'<div class="v60-section-dark"><div class="v60-dark-categories">{cold_items}</div></div>'

        # Empty state
        empty_html = ''
        if not menu_data.get('hot_categories') and not menu_data.get('cold_categories'):
            empty_html = '''
            <div class="v60-section-light" style="text-align: center; padding: 60px 30px;">
                <p style="font-size: 18px; color: #666;">No menu items available</p>
                <p style="font-size: 14px; color: #999; margin-top: 10px;">Please configure the menu categories</p>
            </div>'''

        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{cafe_name} - Menu</title>
    <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&family=Lora:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Lora', 'Georgia', serif;
            background-color: #ffffff;
            min-height: 100vh;
        }}
        .v60-menu-container {{
            max-width: 100%;
            margin: 0 auto;
            background: #ffffff;
        }}
        .v60-menu-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 20px 30px 10px;
            background-color: #ffffff;
        }}
        .v60-menu-title {{
            font-family: 'Dancing Script', cursive;
            font-size: 48px;
            font-weight: normal;
            color: #000000;
        }}
        .v60-logo-container {{
            width: 80px;
            height: 80px;
            border: 2px solid #000000;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 5px;
            background: #000000;
        }}
        .v60-logo-container img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .v60-logo-text {{
            color: #ffffff;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
        }}
        .v60-logo-subtext {{
            color: #ffffff;
            font-size: 10px;
            text-align: center;
        }}
        .v60-section-light {{
            background-color: #ffffff;
            padding: 20px 30px 40px;
        }}
        .v60-section-dark {{
            background-color: #000000;
            padding: 30px;
        }}
        .v60-category-header {{
            display: inline-block;
            margin-bottom: 20px;
        }}
        .v60-category-title {{
            font-size: 22px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 3px;
            padding: 8px 25px;
            border: 2px solid currentColor;
            border-radius: 25px;
            display: inline-block;
        }}
        .v60-category-title-light {{
            color: #000000;
            border-color: #000000;
        }}
        .v60-category-title-dark {{
            color: #ffffff;
            border-color: #ffffff;
        }}
        .v60-menu-items {{
            list-style: none;
        }}
        .v60-menu-item {{
            display: flex;
            align-items: baseline;
            margin-bottom: 12px;
            font-size: 18px;
        }}
        .v60-item-name {{
            font-weight: 500;
            white-space: nowrap;
        }}
        .v60-item-name-light {{ color: #000000; }}
        .v60-item-name-dark {{ color: #ffffff; }}
        .v60-item-line {{
            flex: 1;
            height: 10px;
            margin: 0 10px;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='10' viewBox='0 0 100 10'%3E%3Cpath d='M0 5 Q 12.5 0, 25 5 T 50 5 T 75 5 T 100 5' fill='none' stroke='%23000' stroke-width='1'/%3E%3C/svg%3E");
            background-repeat: repeat-x;
            background-position: center;
        }}
        .v60-item-line-wavy-dark {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='10' viewBox='0 0 100 10'%3E%3Cpath d='M0 5 Q 12.5 0, 25 5 T 50 5 T 75 5 T 100 5' fill='none' stroke='%23fff' stroke-width='1'/%3E%3C/svg%3E");
        }}
        .v60-item-price {{
            font-weight: 500;
            white-space: nowrap;
        }}
        .v60-item-price-light {{ color: #000000; }}
        .v60-item-price-dark {{ color: #ffffff; }}
        .v60-dark-categories {{
            display: flex;
            flex-wrap: wrap;
            gap: 30px;
        }}
        .v60-dark-category {{
            flex: 1;
            min-width: 280px;
        }}
        @media (max-width: 768px) {{
            .v60-menu-header {{ padding: 15px 20px; }}
            .v60-menu-title {{ font-size: 36px; }}
            .v60-logo-container {{ width: 60px; height: 60px; }}
            .v60-section-light, .v60-section-dark {{ padding: 20px; }}
            .v60-category-title {{ font-size: 16px; padding: 6px 18px; }}
            .v60-menu-item {{ font-size: 15px; margin-bottom: 10px; }}
            .v60-dark-categories {{ flex-direction: column; }}
            .v60-dark-category {{ min-width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="v60-menu-container">
        <div class="v60-menu-header">
            <h1 class="v60-menu-title">menu</h1>
            <div class="v60-logo-container">{logo_html}</div>
        </div>
        {hot_html}
        {cold_html}
        {empty_html}
    </div>
</body>
</html>'''
