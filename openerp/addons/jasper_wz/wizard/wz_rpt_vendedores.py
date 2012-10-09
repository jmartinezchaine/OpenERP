# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _

class wz_rpt_vendedores(osv.osv_memory):
    """ Wizard para filtros de Vendedores y Ciudad """

    def _get_vendedores_ids(self, cr, uid, context=None):
        user_obj = self.pool.get('res.users')
        res = []
        usuarios = user_obj.search(cr, uid, [('active','=',True)])
        for usuario in usuarios:
            nombre = user_obj.browse(cr, uid, usuario, context=context).name
            res.append((str(usuario), str(nombre)))
        return res

    _name = "wz.rpt.vendedores"
    _description = "Wizard para Filtro de Clientes por Vendedor y/o Ciudad"

    _columns = {
        'vendedores': fields.selection(_get_vendedores_ids, 'Vendedores'),
        'todos_vendedores': fields.boolean('Todos',),
        'ciudad': fields.char('Ciudad', size=64),
    }

    def print_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'account.invoice'
        datas['form'] = self.read(cr, uid, ids)[0]
        #sql = "select rp.id, rp.name, ru.id usuid, ru.name usuname, ra.city, ra.street, ra.phone from res_partner as rp"
        sql = " LEFT JOIN res_partner_address as ra on ra.partner_id = rp.id"
        sql += " LEFT JOIN res_users as ru on rp.user_id = ru.id"
        sql += " WHERE rp.customer = 'True' and rp.active = 'True' group by rp.id, rp.name, ru.id, ru.name , ra.city, ra.street, ra.phone"
        sql += " order by ru.name,ra.city"
        
        parameters = {}
        
        for wz_obj in self.read(cr, uid, ids, context=context):
            vendedor = wz_obj.get('vendedores', False)     
            todos = wz_obj.get('todos_vendedores', False)
            ciudad = wz_obj.get('ciudad', False)       
            
            if vendedor:
                #sql = "select rp.id, rp.name, ru.id usuid, ru.name usuname, ra.city, ra.street, ra.phone from res_partner as rp"
                sql = " LEFT JOIN res_partner_address as ra on ra.partner_id = rp.id"
                sql += " JOIN res_users as ru on rp.user_id = ru.id and ru.id = "+vendedor
                sql += " WHERE rp.customer = 'True'  and rp.active = 'True' group by rp.id, rp.name, ru.id, ru.name , ra.city, ra.street, ra.phone"
                sql += " order by ru.name,ra.city"
                #parameters.update({'VENDEDOR': vendedor})
            if ciudad:
                #sql = "select rp.id, rp.name, ru.id usuid, ru.name usuname, ra.city, ra.street, ra.phone from res_partner as rp"
                sql = " JOIN res_partner_address as ra on ra.partner_id = rp.id and ra.city = '"+ciudad+"'"
                sql += " LEFT JOIN res_users as ru on rp.user_id = ru.id"
                sql += " WHERE rp.customer = 'True' and rp.active = 'True' group by rp.id, rp.name, ru.id, ru.name , ra.city, ra.street, ra.phone"
                sql += " order by ru.name,ra.city"
                    
            if vendedor and ciudad:    
                #sql = "select rp.id, rp.name, ru.id usuid, ru.name usuname, ra.city, ra.street, ra.phone from res_partner as rp"
                sql = " JOIN res_partner_address as ra on ra.partner_id = rp.id and ra.city = '"+ciudad+"'"
                sql += " JOIN res_users as ru on rp.user_id = ru.id and ru.id ="+vendedor
                sql += " WHERE rp.customer = 'True' and rp.active = 'True' group by rp.id, rp.name, ru.id, ru.name , ra.city, ra.street, ra.phone "
                sql += " order by ru.name,ra.city"
                #parameters.update({'CIUDAD': ciudad})
            print sql    
            parameters.update({str('SQL'): str(sql)})    
            datas['parameters'] = parameters
        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'jasper_clientes_vendedor_ciudad',
            'datas': datas,
        }
        
    def imprimir(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids,)[-1]
        return{
               'type': 'ir.actions.report.xml',
               'report_name' : 'jasper_clientes_vendedor_ciudad',
               'datas':{
                        'model':'account.invoice',
                        'form':data
                        },
               'nodestroy': False
               }

wz_rpt_vendedores()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
