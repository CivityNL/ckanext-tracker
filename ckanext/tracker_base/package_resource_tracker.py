from ckan import model
import ckanext.tracker_base.helpers as th
from context import TrackerContext
from base_tracker import BaseTrackerPlugin
import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


class PackageResourceTrackerPlugin(BaseTrackerPlugin):
    """
    This Plugin contains all the logic necessary to have access to the queues/workers/mappers, feedback and
    UI capabilities
    """
    plugins.implements(plugins.IMapper, inherit=True)
    plugins.implements(plugins.IActions)

    separate_tracking = False
    ignore_packages = False  # type: bool
    ignore_resources = False  # type: bool

    include_resource_fields = None  # type: list
    exclude_resource_fields = None  # type: list

    include_package_fields = None   # type: list
    exclude_package_fields = None   # type: list

    def _action(self, type):

        @toolkit.chained_action
        def _chained_action(original_action, context, data_dict):
            if 'tracker' not in context:
                package_id = data_dict.get("id", None) if type == 'package' else data_dict.get("package_id", None)
                context['tracker'] = TrackerContext(package_id)
            context['tracker'].enter()
            try:
                result = original_action(context, data_dict)
                context['tracker'].exit()
                if context['tracker'].level():
                    package_id = result.get("id", None) if type == 'package' else result.get("package_id", None)
                    context['tracker'].after(package_id)
                    self.determine_actions_based_on_context(context)
                    del context['tracker']
                return result
            except Exception as e:
                context['tracker'].exit()
                if context['tracker'].level():
                    del context['tracker']
                raise e

        return _chained_action

    def get_actions(self):
        types = ['package', 'resource']
        functions = ['create', 'patch', 'update', 'delete']
        actions = {"{}_{}".format(t, f): self._action(t) for t in types for f in functions}
        actions['package_revise'] = self._action('package')
        return actions

    def determine_actions_based_on_context(self, context):
        tracker_context = context['tracker']  # type: TrackerContext
        if tracker_context is None:
            log.warning("Could not determine any tracker context")
            return
        pkg_dict = tracker_context.after_package()
        before_package = tracker_context.before_package()
        before_resources = {}
        if before_package is not None:
            before_resources = {res.get("id"): res for res in before_package.pop("resources", [])}

        after_package = tracker_context.after_package()
        after_resources = {}
        if after_package is not None:
            after_resources = {res.get("id"): res for res in after_package.pop("resources", [])}

        changes_package = th.compare_dicts(
            before_package, after_package, self.include_package_fields, self.exclude_package_fields
        )

        created_resources = th.get_ids_inserted_resources(before_resources, after_resources)
        deleted_resources = th.get_ids_deleted_resources(before_resources, after_resources)
        active_resources = th.get_ids_same_resources(before_resources, after_resources)
        changes_resources = {}
        for res_id in active_resources:
            res_changes = th.compare_dicts(
                before_resources.get(res_id), after_resources.get(res_id),
                self.include_resource_fields, self.exclude_resource_fields
            )
            if res_changes:
                changes_resources[res_id] = res_changes

        if before_package is None and after_package is not None:
            # create package
            if not self.ignore_packages:
                self.package_create(context, pkg_dict)
            if not self.ignore_resources:
                for res_id in active_resources:
                    self.resource_create(context, after_resources.get(res_id), pkg_dict)
        elif before_package is not None and after_package is not None:
            # update / delete
            if before_package.get("id") != after_package.get("id"):
                log.warning("Got a different package")
                return
            elif th.has_been_deleted(after_package, changes_package):
                # delete
                if not self.ignore_packages:
                    self.package_delete(context, pkg_dict)
                if not self.ignore_resources and not self.separate_tracking:
                    for res_dict in pkg_dict.get("resources", []):
                        self.resource_delete(context, res_dict, pkg_dict)
            else:
                if not self.ignore_packages:
                    if changes_package or (self.ignore_resources and not self.separate_tracking and changes_resources):
                        self.package_update(context, pkg_dict, changes_package)
                if not self.ignore_resources:
                    for res_id in created_resources:
                        self.resource_create(context, after_resources.get(res_id), pkg_dict)
                    for res_id in deleted_resources:
                        self.resource_delete(context, after_resources.get(res_id), pkg_dict)
                    for res_id in active_resources:
                        if res_id in changes_resources or (changes_package and not self.separate_tracking):
                            self.resource_update(
                                context,
                                after_resources.get(res_id), changes_resources.get(res_id), pkg_dict, changes_package)
            # update / delete
        else:
            log.warning("Could not retrieve any information about a package")
            pass

    # IMapper
    def after_delete(self, mapper, connection, instance):
        """
        This method is a wrapper to combine both the after_delete for the IMapper, IPackageController and
        IResourceController. In case of the latter two it will trigger their corresponding methods. For the IMapper hook
        a first setup for a resource/package_purge has been implemented
        """
        super(PackageResourceTrackerPlugin, self).after_delete(mapper, connection, instance)
        context = {'model': model, 'session': model.Session, 'user': toolkit.g.user}
        if mapper.entity == model.Resource and not self.ignore_resources:
                pkg_dict = instance['package'].as_dict()
                res_dict = instance.as_dict()
                self.resource_purge(context, res_dict, pkg_dict)
        elif mapper.entity == model.Package and not self.ignore_packages:
                pkg_dict = instance.as_dict()
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
        except toolkit.NotFound:
            pkg_dict = None
        log.debug("{} :: {} :: package_show returned something = [{}]".format(
            self.name, method, bool(pkg_dict)
        ))
        return pkg_dict

    def do_resource_show(self, resource_id, context=None, method=None):
        try:
            res_dict = toolkit.get_action("resource_show")(context, {"id": resource_id})
        except toolkit.NotFound:
            res_dict = None
        log.debug("{} :: {} :: resource_show returned something = [{}]".format(
            self.name, method, bool(res_dict)
        ))
        return res_dict
