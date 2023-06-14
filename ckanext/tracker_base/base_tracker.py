import ckanext.tracker_base.helpers as base_helpers
import logging
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.tracker_base.backend import TrackerBackend
from domain import Configuration
from ckan.model import Resource, Package
from worker import WorkerWrapper
from mapper.mapper import Mapper
from rq import Queue
from rq.job import Job
from redis import Redis
from domain.task_status import PENDING, ERROR

log = logging.getLogger(__name__)


class BaseTrackerPlugin(plugins.SingletonPlugin):
    """
    This Plugin contains all the logic necessary to have access to the queues/workers/mappers, feedback and
    UI capabilities
    """
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IMapper, inherit=True)

    queue_name = None  # type: str
    configuration = None  # type: Configuration
    worker = None  # type: WorkerWrapper
    redis_connection = None  # type: Redis
    mapper = None  # type: Mapper

    badge_title = None  # type: str
    show_ui = True  # type: bool
    show_badge = False  # type: bool

    # IConfigurable

    def configure(self, config):
        """
        Setting values on load and registering to the backend
        """
        if self.queue_name is None:
            self.queue_name = self.name
        if self.badge_title is None:
            self.badge_title = self.name
        self.redis_connection = base_helpers.set_connection()
        self.configuration = Configuration.from_dict(base_helpers.get_configuration_dict(self.name))
        TrackerBackend.register(self)

    # Getters
    def get_worker(self):
        return self.worker

    def get_configuration(self):
        return self.configuration

    def get_connection(self):
        return self.redis_connection

    def get_queue_name(self):
        return self.queue_name

    # UI related methods (see TrackerPlugin)
    def get_badge_title(self):
        # Loads badge_title from configuration, defaults to the
        return toolkit.config.get('ckanext.{}.badge_title'.format(self.name), self.badge_title)

    def get_show_ui(self):
        return toolkit.config.get('ckanext.{}.show_ui'.format(self.name), self.show_ui)

    def get_show_badge(self):
        """
        This method checks if the badge should be shown for this tracker
        """
        show_badge = toolkit.config.get('ckanext.{}.show_badge'.format(self.name), self.show_badge)
        should_show_badge = show_badge and self.get_badge_title()
        return should_show_badge

    # QUEUE / JOB RELATED METHODS
    def put_on_a_queue(self, context, entity_type, command, res_dict, pkg_dict, res_changes, pkg_changes):
        """
        This method will make sure a job is created and put on the queue and giving the correct feedback
        """
        task = None
        job_context = context.copy()
        # Added ignore_auth header, because the context.user and context.user_auth_obj have information about the user performing this action.
        # The user is not necessarly a sysadmin, and the task_status_update call only authorizes sysadmins to perform it.
        # Therefore we need to ignore the authorization otherwise this action is not sucessfull for users who are not sysadmin.
        job_context['ignore_auth'] = True
        job_context['session'] = context['model'].meta.create_local_session()
        try:
            job = self.create_job(command)
            task = base_helpers.create_task(job_context, job, self.name, entity_type, res_dict, pkg_dict)
            if task:
                task_id = task.id
            else:
                task_id = None
            self.enqueue_job(context, job, entity_type, task_id, res_dict, pkg_dict)
            if task is not None:
                base_helpers.update_task(job_context, task, state=PENDING)
        except Exception as unexpected_error:
            log.error("An unexpected error occurred: {}".format(unexpected_error))
            if task is not None:
                base_helpers.update_task(job_context, task, state=ERROR, error=unexpected_error.message)

    def create_job(self, command):
        """
        This method will create the Job to be put on the queue based on all the information
        """
        configuration = self.get_configuration()
        return Job.create(
            command,
            connection=self.get_connection(),
            timeout=configuration.redis_job_timeout,
            result_ttl=configuration.redis_job_result_ttl,
            ttl=configuration.redis_job_ttl
        )

    def enqueue_job(self, context, job, entity_type, task_id, res_dict, pkg_dict):
        q = Queue(self.get_queue_name(), connection=self.get_connection())
        job.args = base_helpers.get_data(context, self.configuration, entity_type, task_id, self.mapper, res_dict, pkg_dict)
        job.description = 'Job for action [{}] on {} [{}] created by {}'.format(
            job.func_name,
            entity_type,
            res_dict.get("id") if entity_type == 'resource' else pkg_dict.get("id"),
            self.name)
        q.enqueue_job(job)

    # IMapper
    def after_delete(self, mapper, connection, instance):
        if mapper.entity == Resource:
            base_helpers.purge_task_statuses(connection, instance.id, 'resource', self.name)
        elif mapper.entity == Package:
            base_helpers.purge_task_statuses(connection, instance.id, 'package', self.name)
