# Copyright VeHoSoft - Vertical & Horizontal Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
	'name': 'Facturación Electrónica CFDI v4.0 FacturaTool',
	'summary': 'Permite emitir Facturas CFDI v4.0 validas para el SAT',
	'version': '17.0.1.0.1',
	'category': 'Invoicing Management',
	'author': 'VeHoSoft',
	'website': 'http://www.vehosoft.com',
	'license': 'AGPL-3',
	'depends': [
		'account','facturatool_account',
	],
	'data': [
		'security/ir.model.access.csv',
		'data/mail_template_data.xml',
		'views/partner_views.xml',
		'views/product_views.xml',
		'views/account_views.xml',
		'wizard/account_move_timbrar_views.xml',
		'views/report_invoice.xml',
	],
	'qweb': [

	],
	'application': False,
	'installable': True,
	"external_dependencies": {
		"python": ["zeep"],
	},
}
