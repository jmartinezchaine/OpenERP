# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

def check_rut(rut):
    sRut = '';
    try:
        sRut = str(rut);
        if not rut:
            return True
        if len(sRut) <> 12:
            return False
    except:
        return False
    
class Partner(osv.osv):
    _inherit = "res.partner"
    _columns = {
        'property_account_payable': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Account Payable",
            method=True,
            view_load=True,
            domain="[('type', '=', 'payable')]",
            help="This account will be used instead of the default one as the payable account for the current partner",
            required=False),
        'property_account_receivable': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Account Receivable",
            method=True,
            view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="Esta cuenta se utiliza para recibir los pagos del Cliente.",
            required=False),
    }
    
    def _check_rut_key(self, cr, uid, ids, context=None):
        for partner in self.browse(cr, uid, ids, context=context):
            res = check_rut(partner.rut)
        return res

    #_constraints = [(_check_rut_key, 'Error: Verificar el formato del RUT', ['rut'])]

    
Partner()


    

