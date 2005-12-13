"""Plone Properties tool setup handlers.

$Id:$
"""

from xml.dom.minidom import parseString

from zope.app import zapi
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import INode
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import NodeAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.GenericSetup.utils import I18NURI
from Products.CMFPlone.PropertiesTool import SimpleItemWithProperties
from Products.CMFPlone.interfaces import IPropertiesTool, ISimpleItemWithProperties

_FILENAME = 'propertiestool.xml'

def importPloneProperties(context):
    """ Import plone properties tool.
    """
    site = context.getSite()
    logger = context.getLogger('plone properties')
    ptool = getToolByName(site, 'portal_properties')

    body = context.readDataFile(_FILENAME)
    if body is None:
        logger.info('Properties tool: Nothing to import.')
        return

    importer = zapi.queryMultiAdapter((ptool, context), IBody)
    if importer is None:
        logger.warning('Properties tool: Import adapter misssing.')
        return

    importer.body = body
    logger.info('Properties tool imported.')

def exportPloneProperties(context):
    """ Export plone properties tool.
    """
    site = context.getSite()
    logger = context.getLogger('plone properties')
    ptool = getToolByName(site, 'portal_properties', None)
    if ptool is None:
        logger.info('Properties tool: Nothing to export.')
        return

    exporter = INode(ptool)
    if exporter is None:
        return 'Properties tool: Export adapter misssing.'

    context.writeDataFile(_FILENAME, exporter.body, exporter.mime_type)
    logger.info('Plone properties tool exported.')

class SimpleItemWithPropertiesNodeAdapter(XMLAdapterBase, PropertyManagerHelpers):

    """Node im- and exporter for SimpleItemWithProperties.
    """

    __used_for__ = ISimpleItemWithProperties

    def _exportNode(self, doc):
        """Export the object as a DOM node.
        """
        self._doc = doc
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        self._initProperties(node)

    node = property(_exportNode, _importNode)

class PlonePropertiesToolNodeAdapter(XMLAdapterBase, ObjectManagerHelpers):

    """Node im- and exporter for Plone PropertiesTool.
    """

    __used_for__ = IPropertiesTool

    def _exportNode(self, doc):
        """Export the object as a DOM node.
        """
        self._doc = doc
        node = self._getObjectNode('object')
        #node.setAttribute('xmlns:i18n', I18NURI)
        node.appendChild(self._extractObjects())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeObjects()

        self._initObjects(node)

    def _initObjects(self, node):
        """Import subobjects"""
        ## XXX: We could just use the _initObjects() from
        ## ObjectManagerHelpers except that it looks up the object
        ## constructor from Products.meta_type and
        ## SimpleItemWithProperties doesn't get registered there.
        for child in node.childNodes:
            if child.nodeName != 'object':
                continue
            if child.hasAttribute('deprecated'):
                continue
            parent = self.context

            obj_id = str(child.getAttribute('name'))
            if obj_id not in parent.objectIds():
                parent._setObject(obj_id, SimpleItemWithProperties(obj_id))
##                 Original _initObjects code:
##                 meta_type = str(child.getAttribute('meta_type'))
##                 for mt_info in Products.meta_types:
##                     if mt_info['name'] == meta_type:
##                         parent._setObject(obj_id, mt_info['instance'](obj_id))
##                         break
##                 else:
##                     raise ValueError('unknown meta_type \'%s\'' % obj_id)

            if child.hasAttribute('insert-before'):
                insert_before = child.getAttribute('insert-before')
                if insert_before == '*':
                    parent.moveObjectsToTop(obj_id)
                else:
                    try:
                        position = parent.getObjectPosition(insert_before)
                        parent.moveObjectToPosition(obj_id, position)
                    except ValueError:
                        pass
            elif child.hasAttribute('insert-after'):
                insert_after = child.getAttribute('insert-after')
                if insert_after == '*':
                    parent.moveObjectsToBottom(obj_id)
                else:
                    try:
                        position = parent.getObjectPosition(insert_after)
                        parent.moveObjectToPosition(obj_id, position+1)
                    except ValueError:
                        pass

            obj = getattr(self.context, obj_id)
            importer = zapi.queryMultiAdapter((obj, self.environ), INode)
            if importer:
                importer.node = child
