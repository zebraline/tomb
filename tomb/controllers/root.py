# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, lurl
from tg import request, redirect, tmpl_context
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.exceptions import HTTPFound
from tg import predicates
from tomb import model
from tomb.controllers.secure import SecureController
from tomb.model import DBSession
from tgext.admin.tgadminconfig import BootstrapTGAdminConfig as TGAdminConfig
from tgext.admin.controller import AdminController

from tomb.lib.base import BaseController
from tomb.controllers.error import ErrorController
import transaction
from error_code import * 
from base import *
from sputnik.SpuUOM import POST_FILE

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the tomb application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    secc = SecureController()
    admin = AdminController(model, DBSession, config_type=TGAdminConfig)

    error = ErrorController()

    def _before(self, *args, **kw):
        tmpl_context.project_name = "tomb"

    @expose('tomb.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')

    @expose('tomb.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about')

    @expose('tomb.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(page='environ', environment=request.environ)

    @expose('tomb.templates.data')
    @expose('json')
    def data(self, **kw):
        """
        This method showcases how you can use the same controller
        for a data page and a display page.
        """
        return dict(page='data', params=kw)

    @expose('tomb.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('tomb.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

    # @expose('tomb.templates.login')
    # def login(self, came_from=lurl('/'), failure=None, login=''):
    #     """Start the user login."""
    #     if failure is not None:
    #         if failure == 'user-not-found':
    #             flash(_('User not found'), 'error')
    #         elif failure == 'invalid-password':
    #             flash(_('Invalid Password'), 'error')

    #     login_counter = request.environ.get('repoze.who.logins', 0)
    #     if failure is None and login_counter > 0:
    #         flash(_('Wrong credentials'), 'warning')

    #     return dict(page='login', login_counter=str(login_counter),
    #                 came_from=came_from, login=login)

    @expose()
    def post_login(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                     params=dict(came_from=came_from, __logins=login_counter))
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)

        # Do not use tg.redirect with tg.url as it will add the mountpoint
        # of the application twice.
        return HTTPFound(location=came_from)

    @expose()
    def post_logout(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        return HTTPFound(location=came_from)


    @expose('json')
    def registe(self, user_name, password, photo='', email_address=''):
        '''
        '''
        # import ipdb;ipdb.set_trace()
        user = model.User()
        user.user_name = user_name
        user.password = password
        user.photo = photo
        user.email_address = email_address

        # check registed user
        find_result = DBSession.query(model.User).filter_by(user_name=user_name
            ).first()
        if find_result:
            return USER_EXIST

        try:
            DBSession.add(user)
            transaction.commit()
            result_dict = dict(user_name=user_name, photo=photo,
                email_address=email_address)
            SUCCESS.update(result_dict)
            return SUCCESS
        except Exception, e:
            transaction.abort()
            print 'error of registe: {}'.format(e)
            return UNKNOW_ERROR

    @expose('json')
    def login(self, user_name, password):
        '''
        '''
        # import ipdb;ipdb.set_trace()

        # check registed user
        find_result = DBSession.query(model.User).filter_by(
            user_name=user_name).filter_by(password=password).first()
        if not find_result:
            return USER_PASSWORD_ERROR

        for key in USER_KEYS:
            LOGIN_SUCCESS.update({key: getattr(find_result, key)})

        return LOGIN_SUCCESS

    @expose('json')
    def add_message(self, user_id, text, image_list=[]):
        message = model.Message()
        message.user_id = user_id
        message.text = text

        try:
            DBSession.add(message)
            model.DBSession.flush()
            message_id = message.message_id
            transaction.commit()
        except Exception, e:
            transaction.abort()
            print 'error: {}'.format(e)
            return UNKNOW_ERROR

        image_list = eval(image_list)
        for img in image_list:
            image = model.Image()
            image.message_id = message_id
            image.image_url = img

            try:
                DBSession.add(image)
                transaction.commit()
            except Exception, e:
                transaction.abort()
                print 'error: {}'.format(e)
                return UNKNOW_ERROR

        result_dict = dict(image_list=image_list, text=text)
        SUCCESS.update(result_dict)
        return SUCCESS


    @expose('json')
    def get_message(self, user_id):
        result = {}
        result_list = []
        # import ipdb;ipdb.set_trace()
        
        query_res = model.DBSession.query(model.Message).filter(
            model.Message.user_id==user_id).all()
        for res in query_res:
            node = {}
            message_id = res.message_id
            node['text'] = res.text
            node['message_id'] = message_id
            query_res = model.DBSession.query(model.Image).filter(
                model.Image.message_id==message_id).all()
            node['image_list'] = self.__trans_image(query_res)
            result_list.append(node)

        result['result_list'] = result_list
        return result


    def __trans_image(self, image):
        result_list = []
        for img in image:
            result_list.append(img.image_url)
        return result_list


    # @expose('json')
    # def store_image(self, image):
    #     file_data = image.file.read()
    #     type = image.type
    #     filename = image.filename
    #     image_url = image_ctrl.upload(filename=filename, file_data=file_data, type=type)
    #     print image_url
    #     return {'image_url': image_url}


