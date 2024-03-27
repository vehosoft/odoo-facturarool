# Copyright VeHoSoft - Vertical & Horizontal Software (http://www.vehosoft.com)
# Code by: Francisco Rodriguez (frodriguez@vehosoft.com).

from odoo import api, fields, models
from lxml import etree

import logging
_logger = logging.getLogger(__name__)

class MailThread(models.AbstractModel):
	_inherit = 'mail.thread'
	
	@api.model
	def _message_route_process(self, message, message_dict, routes):
		#_logger.debug('===== _message_route_process message_dict = %r',message_dict)
		_logger.debug('===== _message_route_process routes = %r',routes)
		res = super(MailThread, self)._message_route_process(message, message_dict, routes)
		#res = self._message_route_process(message, message_dict, routes)
		return res
	
	@api.model
	def message_new(self, msg_dict, custom_values=None):
		record = super(MailThread, self).message_new(msg_dict, custom_values)
		_logger.debug('===== message_new self._name = %r',self._name)
		_logger.debug('===== message_new record.move_type = %r',record.move_type)
		#Si es una factura de proveedor, busca el cfdi (xml) para obtener los detalles de la factura
		if self._name == 'account.move' and record.move_type == 'in_invoice' and record.state == 'draft':
			cdfi_ok = False
			for attachment in msg_dict['attachments']:
				if attachment[0].endswith(".xml") and cdfi_ok == False:
					_logger.debug('===== message_new attachment[0] = %r',attachment[0])
					_logger.debug('===== message_new attachment[1] = %r',attachment[1])
					cfdi_data = self.env['account.move'].get_cfdi_data(attachment[1])
					if cfdi_data != False:
						_logger.debug('===== message_new cfdi_data = %r',cfdi_data)
						#Se verifica que no exista el uuid en otra factura
						invoice_exist = self.env['account.move'].search([('cfdi_uuid','=',cfdi_data['uuid'])])
						if len(invoice_exist) > 0:
							record.message_post(body="Error: Ya existe una factura con el UUID: "+cfdi_data['uuid'], message_type='comment')
							continue
						#Si la factura no tiene uuid, el total es cero, el xml cfdi es valido y existen la relación de emisor (proveedor) y receptor (empresa)
						if (record.cfdi_uuid == '' or  record.cfdi_uuid == None or record.cfdi_uuid == False) and record.amount_total == 0.00 and cfdi_data != False and cfdi_data['receptor']['id'] != False and cfdi_data['emisor']['id'] != False:
							cdfi_ok = True
							#Se actualiza la factura con la fecha, el proveedor, uuid y los conceptos
							invoice_line_ids = []
							for concepto in cfdi_data['conceptos']:
								invoice_line_ids.append((0,0,concepto))
							record.write({
								'invoice_date':cfdi_data['fecha'],
								'date':cfdi_data['fecha'],
								'partner_id':cfdi_data['emisor']['id'],
								'cfdi_uuid':cfdi_data['uuid'],
								'cfdi_folio':cfdi_data['folio'],
								'invoice_line_ids':invoice_line_ids
							})
							#Se Verifica el estado del cfdi
							verificar_cfdi = record.verificar_cfdi(cfdi_data['emisor']['rfc'],cfdi_data['receptor']['rfc'],cfdi_data['total'],cfdi_data['uuid'])
							if verificar_cfdi != False and verificar_cfdi['Estado'] == 'Vigente' and verificar_cfdi['EstatusCancelacion'] == None:
								record.write({
									'cfdi_state':'done'
								})
		return record

	def message_update(self, msg_dict, update_vals=None):
		res = super(MailThread, self).message_update(msg_dict, update_vals)

		#Si es una factura de proveedor, busca el cfdi (xml) para obtener los detalles de la factura
		if self._name == 'account.move' and self.move_type == 'in_invoice' and self.state == 'draft':
			for attachment in msg_dict['attachments']:
				if attachment[0].endswith(".xml"):
					cfdi_data = self.env['account.move'].get_cfdi_data(attachment[1])
					_logger.debug('===== message_update cfdi_data = %r',cfdi_data)
					#Se verifica que no exista el uuid en otra factura
					invoice_exist = self.env['account.move'].search([('cfdi_uuid','=',cfdi_data['uuid'])])
					if len(invoice_exist) > 0:
						self.message_post(body="Error: Ya existe una factura con el UUID: "+cfdi_data['uuid'], message_type='comment')
						continue
					#Si la factura no tiene uuid, el total es cero, el xml cfdi es valido y existen la relación de emisor (proveedor) y receptor (empresa)
					if (self.cfdi_uuid == '' or  self.cfdi_uuid == None or self.cfdi_uuid == False) and self.amount_total == 0.00 and cfdi_data != False and cfdi_data['receptor']['id'] != False and cfdi_data['emisor']['id'] != False:
						#Se actualiza la factura con la fecha, el proveedor, uuid y los conceptos
						invoice_line_ids = []
						for concepto in cfdi_data['conceptos']:
							invoice_line_ids.append((0,0,concepto))
						self.write({
							'invoice_date':cfdi_data['fecha'],
							'date':cfdi_data['fecha'],
							'partner_id':cfdi_data['emisor']['id'],
							'cfdi_uuid':cfdi_data['uuid'],
							'cfdi_folio':cfdi_data['folio'],
							'invoice_line_ids':invoice_line_ids
						})
						#Se Verifica el estado del cfdi
						verificar_cfdi = self.verificar_cfdi(cfdi_data['emisor']['rfc'],cfdi_data['receptor']['rfc'],cfdi_data['total'],cfdi_data['uuid'])
						if verificar_cfdi != False and verificar_cfdi['Estado'] == 'Vigente' and verificar_cfdi['EstatusCancelacion'] == None:
							self.write({
								'cfdi_state':'done'
							})
		return res