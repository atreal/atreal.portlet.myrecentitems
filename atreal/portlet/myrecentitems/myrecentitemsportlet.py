from zope.interface import implements
from ZTUtils import make_query

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from plone.app.portlets.cache import render_cachekey

from plone.memoize import ram
from plone.memoize.compress import xhtml_compress
from plone.memoize.instance import memoize

from Acquisition import aq_inner

from zope import schema
from zope.formlib import form
from zope.component import getMultiAdapter
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from atreal.portlet.myrecentitems import MyRecentItemsPortletMessageFactory as _


class IMyRecentItemsPortlet(IPortletDataProvider):

    name= schema.TextLine(
        title=_(u'Portlet title'),
        description=_(u'The title that will be displayed to the users.'),
        default=_(u"My recent items"),
        required=False,
    )

    count = schema.Int(title=_(u'Number of items to display'),
                       description=_(u'How many items to list.'),
                       required=True,
                       default=5)


class Assignment(base.Assignment):

    implements(IMyRecentItemsPortlet)

    def __init__(self, name=_(u"My recent items"), count=5):
        self.name=name
        self.count=count

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return self.name


def _render_cachekey(fun, self):
    if self.anonymous:
        raise ram.DontCache()
    return render_cachekey(fun, self)


class Renderer(base.Renderer):

    _template = ViewPageTemplateFile('myrecentitemsportlet.pt')
    
    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        context = aq_inner(self.context)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        self.anonymous = portal_state.anonymous()
        self.member = portal_state.member()
        self.portal_url = portal_state.portal_url()
        self.typesToShow = portal_state.friendly_types()

        plone_tools = getMultiAdapter((context, self.request), name=u'plone_tools')
        self.catalog = plone_tools.catalog()
    

    @ram.cache(_render_cachekey)
    def render(self):
        return xhtml_compress(self._template())


    @property
    def available(self):
        return not self.anonymous and len(self._data())


    def getTitle(self):
        return self.data.name or _(u'My recent items')


    def recent_items(self):
        return self._data()


    def all_my_recent_items_link(self):
        return '%s/search?%s' % (self.portal_url, make_query(self._buildQuery()))


    @memoize
    def _data(self):
        limit = self.data.count
        return self.catalog(self._buildQuery())[:limit]


    def _buildQuery(self):
        """ Build a dict used for the catalog search """
        query = dict(Creator=self.member.id,
                    portal_type=self.typesToShow,
                    sort_on='modified',
                    sort_order='reverse')
        return query



class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IMyRecentItemsPortlet)
    label = _(u"Add My recent items Portlet")
    description = _(u"This portlet displays recent items of the current user.")

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IMyRecentItemsPortlet)
    label = _(u"Modify My recent items Portlet")
    description = _(u"This portlet displays recent items of the current user.")
