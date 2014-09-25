#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2014 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Convert XLIFF translation files to OpenDocument (ODF) files.

See: http://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/odf2xliff.html
for examples and usage instructions.
"""

import zipfile
from cStringIO import StringIO

import lxml.etree as etree

from translate.convert import convert
from translate.storage import factory, odf_io, odf_shared
from translate.storage.xml_extract import extract, generate, unit_tree


def translate_odf(template, input_file):

    def load_dom_trees(template):
        odf_data = odf_io.open_odf(template)
        return dict((filename, etree.parse(StringIO(data))) for filename, data in odf_data.iteritems())

    def load_unit_tree(input_file):
        store = factory.getobject(input_file)
        tree = unit_tree.build_unit_tree(store)

        def extract_unit_tree(filename, root_dom_element_name):
            """Find the subtree in 'tree' which corresponds to the data in XML file 'filename'"""

            def get_tree():
                try:
                    return tree.children['office:%s' % root_dom_element_name, 0]
                except KeyError:
                    return unit_tree.XPathTree()
            return (filename, get_tree())

        return dict([extract_unit_tree('content.xml', 'document-content'),
                     extract_unit_tree('meta.xml', 'document-meta'),
                     extract_unit_tree('styles.xml', 'document-styles')])

    def translate_dom_trees(unit_trees, dom_trees):
        make_parse_state = lambda: extract.ParseState(odf_shared.no_translate_content_elements, odf_shared.inline_elements)
        for filename, dom_tree in dom_trees.iteritems():
            file_unit_tree = unit_trees[filename]
            generate.apply_translations(dom_tree.getroot(), file_unit_tree, generate.replace_dom_text(make_parse_state))
        return dom_trees

    dom_trees = load_dom_trees(template)
    unit_trees = load_unit_tree(input_file)
    return translate_dom_trees(unit_trees, dom_trees)


def write_odf(template, output_file, dom_trees):

    def write_content_to_odf(output_zip, dom_trees):
        for filename, dom_tree in dom_trees.iteritems():
            output_zip.writestr(filename, etree.tostring(dom_tree, encoding='UTF-8', xml_declaration=True))

    template_zip = zipfile.ZipFile(template, 'r')
    output_zip = zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED)

    output_zip = odf_io.copy_odf(template_zip, output_zip, dom_trees.keys())
    write_content_to_odf(output_zip, dom_trees)


def convertxliff(input_file, output_file, template):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    # Since the convertoptionsparser will give us an open file, we risk that
    # it could have been opened in non-binary mode on Windows, and then we'll
    # have problems, so let's make sure we have what we want.
    template.close()
    template = file(template.name, mode='rb')
    output_file.close()
    output_file = file(output_file.name, mode='wb')

    xlf_data = input_file.read()
    dom_trees = translate_odf(template, StringIO(xlf_data))
    write_odf(template, output_file, dom_trees)
    output_file.close()
    return True


def main(argv=None):
    formats = {
        ('xlf', 'odt'): ("odt", convertxliff),  # Text
        ('xlf', 'ods'): ("ods", convertxliff),  # Spreadsheet
        ('xlf', 'odp'): ("odp", convertxliff),  # Presentation
        ('xlf', 'odg'): ("odg", convertxliff),  # Drawing
        ('xlf', 'odc'): ("odc", convertxliff),  # Chart
        ('xlf', 'odf'): ("odf", convertxliff),  # Formula
        ('xlf', 'odi'): ("odi", convertxliff),  # Image
        ('xlf', 'odm'): ("odm", convertxliff),  # Master Document
        ('xlf', 'ott'): ("ott", convertxliff),  # Text template
        ('xlf', 'ots'): ("ots", convertxliff),  # Spreadsheet template
        ('xlf', 'otp'): ("otp", convertxliff),  # Presentation template
        ('xlf', 'otg'): ("otg", convertxliff),  # Drawing template
        ('xlf', 'otc'): ("otc", convertxliff),  # Chart template
        ('xlf', 'otf'): ("otf", convertxliff),  # Formula template
        ('xlf', 'oti'): ("oti", convertxliff),  # Image template
        ('xlf', 'oth'): ("oth", convertxliff),  # Web page template
    }
    parser = convert.ConvertOptionParser(formats, usetemplates=True, description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
