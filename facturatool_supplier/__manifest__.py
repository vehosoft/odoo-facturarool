# Copyright VeHoSoft - Vertical & Horizontal Software
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
	'name': 'Facturación Electrónica Proveedores - FacturaTool',
	'summary': 'Facturación Electrónica Proveedores - FacturaTool',
	'version': '16.0.1.0.1',
	'category': 'Invoicing Management',
	'sequence': 50,
	'author': 'VeHoSoft',
	'website': 'http://www.vehosoft.com',
	'license': 'AGPL-3',
	'depends': [
		'account','account_edi','mail','facturatool_cfdi'
	],
	'data': [
		'views/account_views.xml'
	],
	'qweb': [

	],
	'application': False,
	'installable': True,
}
