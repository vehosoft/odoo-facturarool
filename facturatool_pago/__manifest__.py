# Copyright VeHoSoft - Vertical & Horizontal Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
	'name': 'Complemento de Pago CFDI v4.0',
	'summary': 'Permite emitir Facturas CFDI v4.0 Complemento de Pago',
	'version': '17.0.1.0.1',
	'category': 'Invoicing Management',
	'author': 'VeHoSoft',
	'website': 'http://www.vehosoft.com',
	'license': 'AGPL-3',
	'depends': [
		'account','facturatool_cfdi',
	],
	'data': [
		'security/ir.model.access.csv',
		'wizard/account_payment_register_views.xml',
		'wizard/account_payment_timbrar_views.xml',
		'views/account_payment_views.xml',
		'views/account_move_views.xml',
		#'views/report_payment_templates.xml',
	],
	'qweb': [

	],
	'application': False,
	'installable': True,
	"external_dependencies": {
		"python": ["zeep"],
	},
}
