# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api
from openerp import SUPERUSER_ID
from openerp.exceptions import AccessError
from openerp.osv import osv, fields
from openerp.sql_db import TestCursor
from openerp.tools import config
from openerp.tools.misc import find_in_path
from openerp.tools.translate import _
from openerp.addons.web.http import request
from openerp.tools.safe_eval import safe_eval as eval
from openerp.exceptions import UserError

import re
import time
import base64
import logging
import tempfile
import lxml.html
import os
import subprocess
from contextlib import closing
from distutils.version import LooseVersion
from functools import partial
from pyPdf import PdfFileWriter, PdfFileReader
from reportlab.graphics.barcode import createBarcodeDrawing


class Report(osv.Model):
    _inherit = "report"