#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

from __future__ import absolute_import
from __future__ import print_function
import sys
import re

__author__ = "Alberto Pettarin"
__copyright__ = "Copyright 2015, Alberto Pettarin (www.albertopettarin.it)"
__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "alberto@albertopettarin.it"
__status__ = "Production"

class MOEdit():
    """
    A class to add/remove MO attributes from a given XHTML file.

    :param tags: the list of tag names to process
    :type  tags: list of str
    :param mo_class: the value of the MO class
    :type  mo_class: str
    :param nomo_class: the value of the "no MO" class
    :type  nomo_class: str
    :param id_regex: the regex string to match id values generated by this plugin
    :type  id_regex: str
    :param id_format: the format string (with a "%d" placeholder) to generate id values
    :type  id_format: str
    """

    def __init__(self, tags, mo_class, nomo_class, id_regex, id_format):
        self.tags = tags
        self.mo_class = mo_class
        self.nomo_class = nomo_class
        self.id_regex = id_regex
        self.id_format = id_format
        self.id_pattern = re.compile(self.id_regex)

    @classmethod
    def get_classes(cls, elem):
        """
        Return a set object, containing the classes
        of the given element (possibly, empty).

        :param elem: the element
        :type  elem: elem
        :rtype: set of str
        """
        classes = []
        if "class" in elem.attrs:
            classes = elem.attrs["class"]
            if not isinstance(classes, list):
                classes = [classes]
        return set(classes)

    @classmethod
    def remove_id_attribute(cls, elem):
        """
        Remove id attribute from the given element.

        :param elem: the element
        :type  elem: elem
        """
        if "id" in elem.attrs:
            del elem.attrs["id"]

    def has_id_not_mo(self, elem):
        """
        Determine if the given element has an id attribute not generated by this plugin.

        :param elem: the element
        :type  elem: elem
        :rtype: bool
        """
        return ("id" in elem.attrs) and (self.id_pattern.match(elem.attrs["id"]) is None)

    def has_mo_id(self, elem):
        """
        Determine if the given element has an id attribute generated by this plugin.

        :param elem: the element
        :type  elem: elem
        :rtype: bool
        """
        return ("id" in elem.attrs) and (self.id_pattern.match(elem.attrs["id"]) is not None)

    def has_mo_class(self, elem):
        """
        Determine if the given element has the "MO" class.

        :param elem: the element
        :type  elem: elem
        :rtype: bool
        """
        return self.mo_class in self.get_classes(elem)

    def has_nomo_class(self, elem):
        """
        Determine if the given element has the "no MO" class.

        :param elem: the element
        :type  elem: elem
        :rtype: bool
        """
        return self.nomo_class in self.get_classes(elem)

    def add_mo_class(self, elem):
        """
        Add the "MO" class to the given element.

        :param elem: the element
        :type  elem: elem
        """
        classes = self.get_classes(elem)
        classes.add(self.mo_class)
        elem.attrs["class"] = list(classes)

    def remove_mo_class(self, elem):
        """
        Remove the "MO" class from the given element,
        if present.
        If, after removing the "MO" class, the class
        attribute is empty, remove it from elem.

        :param elem: the element
        :type  elem: elem
        """
        classes = self.get_classes(elem)
        if self.mo_class in classes:
            classes.remove(self.mo_class)
        if len(classes) > 0:
            elem.attrs["class"] = list(classes)
        else:
            del elem.attrs["class"]

    def add_mo_attributes(self, data):
        """
        Add MO attributes to tags in the given XHTML file,
        and return the resulting XHTML string.

        :param data: the source code
        :type  data: str
        :rtype: str
        """
        import sigil_gumbo_bs4_adapter as gumbo_bs4
        msgs = []
        soup = gumbo_bs4.parse(data)
        i = 1
        for node in soup.find_all():
            if node.name in self.tags:
                new_id = self.id_format % (i)
                i += 1
                if self.has_nomo_class(node):
                    msgs.append(("WARN", "element '%s' with class 'nomo' => ignoring (it would be '%s')" % (node.name, new_id)))
                else:
                    if self.has_id_not_mo(node):
                        msgs.append(("WARN", "element '%s' with id '%s' => not changing (it would be '%s')" % (node.name, node.attrs["id"], new_id)))
                    else:
                        msgs.append(("INFO", "element '%s' => setting id '%s'" % (node.name, new_id)))
                        node.attrs["id"] = new_id
                    self.add_mo_class(node)
        out_data = self.output_xhtml_code(soup)
        return (msgs, out_data)

    def remove_mo_attributes(self, data, remove_class=True, remove_id=True):
        """
        Remove MO attributes to tags in the given XHTML file,
        and return the resulting XHTML string.

        :param data: the source code
        :type  data: str
        :param remove_class: remove the MO class attribute
        :type  remove_class: bool
        :param remove_id: remove the MO id attribute
        :type  remove_id: bool
        """
        msgs = []
        if (not remove_class) and (not remove_id):
            return (msgs, data)
        import sigil_gumbo_bs4_adapter as gumbo_bs4
        soup = gumbo_bs4.parse(data)
        for node in soup.find_all():
            if node.name in self.tags:
                if self.has_mo_class(node):
                    if remove_class:
                        self.remove_mo_class(node)
                        msgs.append(("INFO", "removed class 'mo' from element '%s'" % (node.name)))
                    if remove_id:
                        if self.has_mo_id(node):
                            old_id = node.attrs["id"]
                            self.remove_id_attribute(node)
                            msgs.append(("INFO", "removed id '%s' from element '%s'" % (old_id, node.name)))
                        elif self.has_id_not_mo(node):
                            msgs.append(("WARN", "element '%s' with id '%s' => not removing" % (node.name, node.attrs["id"])))
        out_data = self.output_xhtml_code(soup)
        return (msgs, out_data)

    @classmethod
    def output_xhtml_code(cls, soup):
        """
        Serialize the given soup element and output
        the corresponding XHTML source code as a string (bytes).

        :param soup: the soup object
        :type  soup: gumbo_bs4 soup
        :rtype: str
        """
        self_closing_tags = [
            #"area",
            #"base",
            "br",
            "col",
            #"command",
            "embed",
            "hr",
            "img",
            "input",
            #"keygen",
            "link",
            "meta",
            #"param",
            #"source",
            "track",
            #"wbr",
        ]

        out_data = soup.serialize_xhtml()
        #out_data = soup.prettyprint_xhtml(
        #    indent_level=0,
        #    eventual_encoding="utf-8",
        #    formatter="minimal",
        #    indent_chars="  "
        #)

        # this is a workaround for Sigil < 0.9.2
        # see https://github.com/Sigil-Ebook/Sigil/issues/169
        for tag in self_closing_tags:
            out_data = out_data.replace("></%s>" % (tag), "/>")
        return out_data



