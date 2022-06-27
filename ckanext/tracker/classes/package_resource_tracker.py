from ckan import model
from ckan.logic import NotFound
from ckan.model.package import Package
from ckan.model.resource import Resource
import helpers as helpers
from ckanext.tracker.classes import BaseTrackerPlugin
import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import c

log = logging.getLogger(__name__)


class PackageResourceTrackerPlugin(BaseTrackerPlugin):
    """
    This Plugin contains all the logic necessary to have access to the queues/workers/mappers, feedback and
    UI capabilities
    """
    plugins.implements(plugins.IMapper, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    package_context = helpers.init_package_context()

    separate_tracking = False
    ignore_packages = False  # type: bool
    ignore_resources = False  # type: bool

    include_resource_fields = None  # type: list
    exclude_resource_fields = None  # type: list

    include_package_fields = None   # type: list
    exclude_package_fields = None   # type: list

    def clear_context(self):
        self.package_context = helpers.init_package_context()

    def filter_fields_from_resource_changes(self, resource_changes):
        return helpers.filter_fields_from_changes(
            resource_changes, self.include_resource_fields, self.exclude_resource_fields
        )

    def filter_fields_from_package_changes(self, package_changes):
        return helpers.filter_fields_from_changes(
            package_changes, self.include_package_fields, self.exclude_package_fields
        )

    def create_context(self):
        log.info("creating context ...")
        return {'model': model, 'session': model.Session, 'user': c.user}

    # IMapper
    def after_insert(self, mapper, connection, instance):
        if mapper.entity == Resource:
            helpers.add_resource_to_tracker_context(self.package_context, 'insert', instance)

    '''
    List of before_* implementations for the IResourceController and IPackageController. In some cases the IMapper is
    also mentioned, but this is only due to conflicting naming of methods between the different interfaces. 
    The main use of these implementations is to:
     - check if we entered via the IResourceController (and if not via the IPackageController)
     - clear the context for a fresh start
    '''

    # IPackageController
    def before_package_create(self, context, pkg_dict):
        self.clear_context()

    # IPackageController
    def before_package_update(self, context, pkg_dict):
        self.clear_context()

    '''
    List of after_* implementations for the IResourceController, the IPackageController and the IMapper. 
    The main use of these implementations is to differentiate between the different action due to conflicting naming and
    pass the correct parameters to the specific action implementation __after_*_** where:
     - '*' is either package, resource or mapper
     - '**' is either create, delete, update or purge
    '''

    # IPackageController
    def after_create(self, context, package):
        """
        This method is a Wrapper to combine the after_create for both the IPackageController and IResourceController
        Checks if it comes from IPackageController or IResourceController

        If IPackageController:
            Check if any resources have been created (inserted)
                trigger the corresponding method for each resource
                (later the 'original' package_create method will be called)
        If IResourceController:
            Trigger the corresponding method

       :param list *args: The list of args for either the IPackageController and IResourceController implementation
       :param args[0]: Context
       :param args[1]:
                    IPackageController --> resource_dict
                    IResourceController --> package_dict
        """
        self.__after_package_create(context, package.get("id"))

    # IPackageController & IMapper
    def after_update(self, *args):
        """
        This method is a wrapper to combine both the after_update for the IMapper, IPackageController and
        IResourceController. In the first case a simple check is done to see if something got updated, for the
        IResourceController hook it gets simply passed to the corresponding method. The tricky part is for the
        IPackageController in which case it is checked if this hook was called after any IResourceController hook, in
        which case all resource related changes are ignored. Otherwise all created/changed resources belonging to this
        package are checked and if necessary the corresponding methods are triggered
        """
        if isinstance(args[0], dict) and isinstance(args[1], dict):
            context = args[0]
            package = args[1]
            self.__after_package_update(context, package)
        else:
            mapper = args[0]
            instance = args[2]
            self.__after_mapper_update(mapper, instance)

    # IPackageController & IMapper
    def after_delete(self, *args):
        """
        This method is a wrapper to combine both the after_delete for the IMapper, IPackageController and
        IResourceController. In case of the latter two it will trigger their corresponding methods. For the IMapper hook
        a first setup for a resource/package_purge has been implemented
        """
        if isinstance(args[0], dict):
            # check for IPackageController::after_delete
            context = args[0]
            package = args[1]
            self.__after_package_delete(context, package)
        else:
            # check for IMapper::after_delete
            mapper = args[0]
            connection = args[1]
            instance = args[2]
            self.__after_mapper_delete(mapper, connection, instance)

    '''
    List of __after_*_** implementations which are called in after_* implementations for the IResourceController, the 
    IPackageController and the IMapper.
    '''

    def __after_package_create(self, context, package_id):
        pkg_dict = self.do_package_show(package_id, context, "__after_package_create")
        if not self.ignore_packages:
            self.package_create(context, pkg_dict)
        inserted_resources = self.package_context['resources']['insert']
        if inserted_resources:
            if not self.ignore_resources:
                for resource in inserted_resources:
                    res_dict = self.do_resource_show(resource.get("id"), context, "__after_package_create")
                    self.resource_create(context, res_dict, pkg_dict)
        self.clear_context()

    def __after_package_update(self, context, package):
        pkg_dict = self.do_package_show(package.get("id"), context, "__after_package_update")
        res_dict_dict = {resource.get("id"): resource for resource in pkg_dict.get("resources", [])}
        revision_id = helpers.get_revision_id(context)
        pkg_full_changes, res_full_changes_dict = helpers.get_package_changes(
            revision_id, package.get("id"), include_extras=True, include_resources=True
        )
        pkg_changes = self.filter_fields_from_package_changes(pkg_full_changes.copy())

        if not self.ignore_packages:
            if pkg_changes or (self.ignore_resources and not self.separate_tracking and res_full_changes_dict):
                self.package_update(context, pkg_dict, pkg_changes)
        # get all inserted resources from context
        inserted_resources = self.package_context['resources']['insert']
        if inserted_resources:
            if not self.ignore_resources:
                for resource in inserted_resources:
                    res_dict = res_dict_dict.pop(resource.get("id"))
                    self.resource_create(context, res_dict, pkg_dict)
        # get all updated resources from context
        updated_resources = self.package_context['resources']['update']
        if (updated_resources or res_dict_dict) and not self.ignore_resources:
            for resource in updated_resources:
                if resource.get("id") not in res_dict_dict:
                    res_dict_dict[resource.get("id")] = resource
            for res_dict in res_dict_dict.values():
                res_full_changes = res_full_changes_dict.get(res_dict.get("id"), {})
                res_changes = self.filter_fields_from_resource_changes(res_full_changes.copy())
                if res_dict.get("state") == "active":
                    if res_changes or (pkg_changes and not self.separate_tracking):
                        self.resource_update(context, res_dict, res_changes, pkg_dict, pkg_changes)
                elif res_dict.get("state") == "deleted" and "state" in res_full_changes:
                    self.resource_delete(context, res_dict, pkg_dict)
        self.clear_context()

    def __after_mapper_update(self, mapper, instance):
        # due to the way an update works newly created resources will also get updated. This prevents doubles
        if mapper.entity == Resource:
            if instance.id not in [res.get("id") for res in self.package_context['resources']['insert']]:
                helpers.add_resource_to_tracker_context(self.package_context, 'update', instance)

    def __after_package_delete(self, context, package):
        package_id = package.get("id")
        pkg_dict = self.do_package_show(package_id, context, "__after_package_delete")
        if not self.ignore_packages:
            self.package_delete(context, pkg_dict)
        if not self.ignore_resources and not self.separate_tracking:
            resources = pkg_dict.get("resources", [])
            for res_dict in resources:
                self.resource_delete(context, res_dict, pkg_dict)
        self.clear_context()

    def __after_mapper_delete(self, mapper, connection, instance):
        context = self.create_context()
        if mapper.entity == Resource:
            helpers.purge_task_statuses(connection, instance.id, 'resource', self.name)
            if not self.ignore_resources:
                # getting the package as entity instead of sing package_show as we don't have context
                pkg_dict = self.do_package_show(instance.package_id, context, method="__after_mapper_delete")
                res_dict = instance.as_dict()
                self.resource_purge(context, res_dict, pkg_dict)
        elif mapper.entity == Package:
            helpers.purge_task_statuses(connection, instance.id, 'package', self.name)
            if not self.ignore_packages:
                pkg_dict = self.do_package_show(instance.id, context, method="__after_mapper_delete")
                self.package_purge(context, pkg_dict)


    # Package & Resource Public Functions ***********************************************************************
    def package_create(self, context, pkg_dict):
        action = self.action_to_take_on_package_create(context, pkg_dict)
        if action:
            log.info('{}: acting on package_create with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'package', action, None, pkg_dict, None, None)

    def package_update(self, context, pkg_dict, package_changes):
        action = self.action_to_take_on_package_update(context, pkg_dict, package_changes)
        if action:
            log.info('{}: acting on package_update with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'package', action, None, pkg_dict, None, package_changes)

    def package_delete(self, context, pkg_dict):
        action = self.action_to_take_on_package_delete(context, pkg_dict)
        if action:
            log.info('{}: acting on package_delete with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'package', action, None, pkg_dict, None, None)

    def package_purge(self, context, pkg_dict):
        action = self.action_to_take_on_package_purge(context, pkg_dict)
        if action:
            log.info('{}: acting on package_purge with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'package', action, None, pkg_dict, None, None)

    def resource_create(self, context, res_dict, pkg_dict):
        action = self.action_to_take_on_resource_create(context, res_dict, pkg_dict)
        if action:
            log.info('{}: acting on resource_create with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'resource', action, res_dict, pkg_dict, None, None)

    def resource_update(self, context, res_dict, resource_changes, pkg_dict, package_changes):
        action = self.action_to_take_on_resource_update(context, res_dict, resource_changes, pkg_dict, package_changes)
        if action:
            log.info('{}: acting on resource_update with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'resource', action, res_dict, pkg_dict, resource_changes, package_changes)

    def resource_delete(self, context, res_dict, pkg_dict):
        action = self.action_to_take_on_resource_delete(context, res_dict, pkg_dict)
        if action:
            log.info('{}: acting on resource_delete with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'resource', action, res_dict, pkg_dict, None, None)

    def resource_purge(self, context, res_dict, pkg_dict):
        action = self.action_to_take_on_resource_purge(context, res_dict, pkg_dict)
        if action:
            log.info('{}: acting on resource_purge with action {}'.format(self.name, action))
            self.put_on_a_queue(context, 'resource', action, res_dict, pkg_dict, None, None)

    #  Return the action for each Hook - Default to None ***********************************
    def action_to_take_on_package_create(self, context, pkg_dict):
        return None

    def action_to_take_on_resource_create(self, context, res_dict, pkg_dict):
        return None

    def action_to_take_on_package_update(self, context, pkg_dict, package_changes):
        return None

    def action_to_take_on_resource_update(self, context, res_dict, resource_changes, pkg_dict, package_changes):
        return None

    def action_to_take_on_package_delete(self, context, pkg_dict):
        return None

    def action_to_take_on_resource_delete(self, context, res_dict, pkg_dict):
        return None

    def action_to_take_on_package_purge(self, context, pkg_dict):
        return None

    def action_to_take_on_resource_purge(self, context, res_dict, pkg_dict):
        return None

    def do_package_show(self, package_id, context=None, method=None):
        try:
            pkg_dict = toolkit.get_action("package_show")(context, {"id": package_id})
        except NotFound:
            pkg_dict = None
        log.debug("{} :: {} :: package_show returned something = [{}]".format(
            self.name, method, bool(pkg_dict)
        ))
        return pkg_dict

    def do_resource_show(self, resource_id, context=None, method=None):
        try:
            res_dict = toolkit.get_action("resource_show")(context, {"id": resource_id})
        except NotFound:
            res_dict = None
        log.debug("{} :: {} :: resource_show returned something = [{}]".format(
            self.name, method, bool(res_dict)
        ))
        return res_dict

    # def on_resource_create(self, context, res_dict, pkg_dict):
    #     action = None
    #     if self.should_resource_exist(res_dict, pkg_dict):
    #         action = self.action_on_resource_create()
    #     if action:
    #         self.put_on_a_queue(context, 'resource', action, res_dict, pkg_dict, None, None)
    #
    # def on_resource_update(self, context, res_dict, resource_changes, pkg_dict, package_changes):
    #     should_resource_exist = self.should_resource_exist(res_dict, pkg_dict)
    #     does_resource_exist = self.does_resource_exist(res_dict, pkg_dict)
    #     if does_resource_exist is None:
    #         # create a copy of the new res_dict and update it with the old values from the changes
    #         old_res_dict = res_dict.copy()
    #         old_res_dict.update({key: resource_changes[key]["old"] for key in resource_changes})
    #         # create a copy of the new res_dict and update it with the old values from the changes
    #         old_pkg_dict = pkg_dict.copy()
    #         old_pkg_dict.update({key: package_changes[key]["old"] for key in package_changes})
    #         # determine if the resource should exist based on the previous information
    #         does_resource_exist = self.should_resource_exist(old_res_dict, old_pkg_dict)
    #     filtered_res_changes = self.filter_fields_from_resource_changes(resource_changes.copy())
    #     filtered_pkg_changes = self.filter_fields_from_package_changes(package_changes.copy())
    #     action = None
    #     if not should_resource_exist and does_resource_exist:
    #         action = self.action_on_resource_delete()
    #     elif should_resource_exist and not does_resource_exist:
    #         action = self.action_on_resource_create()
    #     else:
    #         if filtered_res_changes or filtered_pkg_changes:
    #             action = self.action_on_resource_update()
    #     if action is not None:
    #         self.put_on_a_queue(context, 'resource', action, res_dict, pkg_dict,
    #                             filtered_res_changes, filtered_pkg_changes)
    #
    # def on_resource_purge(self, context, res_dict, pkg_dict):
    #     does_resource_exist = self.does_resource_exist(res_dict, pkg_dict)
    #     if does_resource_exist is None:
    #         does_resource_exist = self.should_resource_exist(res_dict, pkg_dict)
    #     action = None
    #     if does_resource_exist:
    #         action = self.action_on_resource_purge()
    #     if action:
    #         self.put_on_a_queue(context, 'resource', action, res_dict, pkg_dict, None, None)
    #
    # def on_package_create(self, context, pkg_dict):
    #     action = None
    #     if self.should_package_exist(pkg_dict):
    #         action = self.action_on_package_create()
    #     if action:
    #         self.put_on_a_queue(context, 'package', action, None, pkg_dict, None, None)
    #
    # def on_package_update(self, context, pkg_dict, package_changes):
    #     should_package_exist = self.should_package_exist(pkg_dict)
    #     does_package_exist = self.does_package_exist(pkg_dict)
    #     if does_package_exist is None:
    #         # create a copy of the new res_dict and update it with the old values from the changes
    #         old_pkg_dict = pkg_dict.copy()
    #         old_pkg_dict.update({key: package_changes[key]["old"] for key in package_changes})
    #         # determine if the resource should exist based on the previous information
    #         does_package_exist = self.should_package_exist(old_pkg_dict)
    #     filtered_pkg_changes = self.filter_fields_from_package_changes(package_changes.copy())
    #     action = None
    #     if not should_package_exist and does_package_exist:
    #         action = self.action_on_package_delete()
    #     elif should_package_exist and not does_package_exist:
    #         action = self.action_on_package_create()
    #     else:
    #         if filtered_pkg_changes:
    #             action = self.action_on_resource_update()
    #     if action is not None:
    #         self.put_on_a_queue(context, 'package', action, None, pkg_dict, None, filtered_pkg_changes)
    #
    # def on_package_purge(self, context, pkg_dict):
    #     does_package_exist = self.does_package_exist(pkg_dict)
    #     if does_package_exist is None:
    #         does_package_exist = self.should_package_exist(pkg_dict)
    #     action = None
    #     if does_package_exist:
    #         action = self.action_on_package_purge()
    #     if action:
    #         self.put_on_a_queue(context, 'package', action, None, pkg_dict, None, None)
    #
    # def does_package_exist(self, pkg_dict):
    #     pass
    #
    # def does_resource_exist(self, res_dict, pkg_dict):
    #     pass
    #
    # def should_package_exist(self, pkg_dict):
    #     pass
    #
    # def should_resource_exist(self, res_dict, pkg_dict):
    #     pass
    #
    # def action_on_package_create(self):
    #     pass
    #
    # def action_on_package_update(self):
    #     pass
    #
    # def action_on_package_delete(self):
    #     pass
    #
    # def action_on_package_purge(self):
    #     pass
    #
    # def action_on_resource_create(self):
    #     pass
    #
    # def action_on_resource_update(self):
    #     pass
    #
    # def action_on_resource_delete(self):
    #     pass
    #
    # def action_on_resource_purge(self):
    #     pass
