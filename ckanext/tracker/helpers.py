import hashlib
import json
import logging
import math

import ckan.plugins.toolkit as toolkit
from ckanext.tracker.backend import TrackerBackend
from domain import Configuration
from redis import Redis
from rq import Queue, Worker

log = logging.getLogger(__name__)

from ckan import model
from datetime import datetime
import ckan.plugins.toolkit as toolkit
from ckanext.tracker.backend import TrackerBackend
from domain.task_status import DomainTaskStatus, ERROR, COMPLETE
from sqlalchemy import and_

import logging


def get_tracker_activities(entity_type, entity_id, limit=100):
    context = {'user': toolkit.g.user}
    trackers = []
    result = {}
    for tracker in TrackerBackend.get_trackers():
        if tracker.show_ui:
            trackers.append(tracker.name)
    query = []
    if trackers:
        query = model.Session.query(model.TaskStatus) \
            .filter(and_(
            model.TaskStatus.entity_id == entity_id,
            model.TaskStatus.entity_type == entity_type,
            model.TaskStatus.task_type.in_(trackers),
            model.TaskStatus.key != model.TaskStatus.task_type,
        )).order_by(model.TaskStatus.last_updated.desc()).limit(limit).all()
    task_status_list = sorted(
        [DomainTaskStatus.from_dict(task_status.as_dict()) for task_status in query],
        key=lambda x: x.created
    )
    for task_status in task_status_list:
        if task_status.task_type in result:
            result[task_status.task_type].append(task_status)
        else:
            result[task_status.task_type] = [task_status]
    return result


def get_tracker_activities_stream(entity_type, entity_id, limit=100):
    activities = get_tracker_activities(entity_type, entity_id, limit)
    timestamps = []
    tracker_streams = {}
    rows = []
    ## create timestamps
    for name, stream in activities.iteritems():
        for activity in stream:
            timestamps.extend(filter(None, [activity.created, activity.pending, activity.running, activity.complete]))
    timestamps = sorted(list(set(timestamps)))
    for name, tracker_activities in activities.iteritems():
        streams = []
        max_timestamps = []
        for activity in tracker_activities:
            saved_to_stream = False
            n_streams = len(streams)
            for i in range(n_streams):
                if max_timestamps[i] >= activity.created:
                    continue
                else:
                    streams[i].append(activity)
                    if activity.complete is None:
                        max_timestamps[i] = datetime.max
                    else:
                        max_timestamps[i] = activity.complete
                    saved_to_stream = True
                    break
            if not saved_to_stream:
                streams.append([activity])
                if activity.complete is None:
                    max_timestamps.append(datetime.max)
                else:
                    max_timestamps.append(activity.complete)
        for s in range(len(streams)):
            timestamp_stream = [None] * len(timestamps)
            for activity in streams[s]:
                end = len(timestamps) - 1
                start = timestamps.index(activity.created)
                if activity.complete is not None:
                    end = timestamps.index(activity.complete)
                t_list = [None] * (end + 1 - start)
                for t in range(start, end + 1):
                    t_list[t - start] = {
                        "state": activity.get_state(timestamps[t]),
                        "id": activity.id,
                        "hash": activity.hash(),
                        "action": activity.action,
                        "start": t == start,
                        "end": t == end
                    }
                timestamp_stream[start:end + 1] = t_list
            streams[s] = timestamp_stream
        tracker_streams[name] = streams
    for t in range(len(timestamps)):
        diff = None
        if t + 1 < len(timestamps):
            diff = math.log10((timestamps[t+1] - timestamps[t]).total_seconds())
        _t = {
            "timestamp": timestamps[t],
            "diff": int(diff) if diff > 0 else 0,
            "activities": []
        }
        for name, streams in tracker_streams.iteritems():
            for stream in streams:
                _t["activities"].append(stream[t])
        rows.append(_t)

    headers = []
    for name, streams in tracker_streams.iteritems():
        headers.append({
            "name": name,
            "size": len(streams)
        })

    return headers, reversed(rows)


WORKER_STATUS_MAPPING = {
    'started': 'active',
    'suspended': 'inactive',
    'busy': 'busy',
    'idle': 'active'
}

JOB_STATUS_MAPPING = {
    'queued': 'queued',
    'started': 'running',
    # 'deferred': 'deferred',
    # 'finished': 'finished',
    # 'stopped': 'stopped',
    # 'scheduled': 'scheduled',
    # 'canceled': 'canceled',
    'failed': 'failed'
}


# queued, started, deferred, finished, stopped, scheduled, canceled and failed


def get_tracker_queues():
    result = {}
    trackers = TrackerBackend.get_trackers()
    for tracker in trackers:
        queue = tracker.queue
        if queue not in result:
            result[queue] = {
                'n_plugins': 0, 'plugins': {},
                'n_jobs': 0, 'jobs': {'queued': 0, 'running': 0, 'failed': 0},
                'n_workers': 0, 'workers': {'active': 0, 'busy': 0, 'inactive': 0}
            }
        result[queue]['n_plugins'] += 1
        result[queue]['plugins'][tracker.name] = {'n_jobs': 0, 'jobs': {'queued': 0, 'running': 0, 'failed': 0}}

    redis_url = toolkit.config.get('ckan.redis.url', "redis://localhost:6379/")
    site_url = toolkit.config.get('ckan.site_url')
    redis = Redis.from_url(redis_url)
    for queue in result:
        redis_queue = Queue(connection=redis, name=queue)
        # result[queue]['jobs'] = len(redis_queue.jobs)
        for job in redis_queue.jobs:
            configuration = job.args[0]
            if not isinstance(configuration, Configuration):
                configuration = Configuration.from_dict(json.loads(configuration))
            if configuration.source_ckan_host == site_url:
                plugin_name = configuration.plugin_name
                if plugin_name in result[queue]['plugins']:
                    result[queue]['plugins'][plugin_name]['n_jobs'] += 1
                    result[queue]['n_jobs'] += 1
                    job_status = job.get_status()
                    if job_status in JOB_STATUS_MAPPING:
                        result[queue]['jobs'][JOB_STATUS_MAPPING[job_status]] += 1
                        result[queue]['plugins'][plugin_name]['jobs'][JOB_STATUS_MAPPING[job_status]] += 1
                    else:
                        log.debug("job status '{}' not found in mapping".format(job_status))
    failed_queue = Queue(connection=redis, name='failed')
    for failed_job in failed_queue.jobs:
        queue = failed_job.origin
        if queue in result:
            result[queue]['n_jobs'] += 1
            job_status = failed_job.get_status()
            if job_status in JOB_STATUS_MAPPING:
                result[queue]['jobs'][JOB_STATUS_MAPPING[job_status]] += 1
            else:
                log.debug("job status '{}' not found in mapping".format(job_status))
    workers = Worker.all(redis)
    for worker in workers:
        for queue in worker.queues:
            if queue.name in result:
                result[queue.name]['n_workers'] += 1
                worker_status = worker.state
                if worker_status in WORKER_STATUS_MAPPING:
                    result[queue.name]['workers'][WORKER_STATUS_MAPPING[worker_status]] += 1
                else:
                    log.debug("worker status '{}' not found in mapping".format(worker_status))
    return result


def get_tracker_status(context, tracker, entity_type, entity_id):
    """
    This method will return the TaskStatus information for a specific tracker and entity_id
    @param context: context
    @param tracker: TrackerModel
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: dict containing the information of the specific TaskStatus object
    """
    if not entity_id:
        return None
    query = model.Session.query(
        model.TaskStatus
    ).filter(
        and_(
            model.TaskStatus.entity_id == entity_id,
            model.TaskStatus.entity_type == entity_type,
            model.TaskStatus.task_type == tracker.name,
            model.TaskStatus.key != model.TaskStatus.task_type,
            model.TaskStatus.state.notin_([ERROR, COMPLETE])
        )
    ).order_by(
        model.TaskStatus.last_updated.desc()
    ).all()
    result = None
    if query is None or len(query) == 0:
        query = model.Session.query(
            model.TaskStatus
        ).filter(
            and_(
                model.TaskStatus.entity_id == entity_id,
                model.TaskStatus.entity_type == entity_type,
                model.TaskStatus.task_type == tracker.name,
                model.TaskStatus.key != model.TaskStatus.task_type,
                model.TaskStatus.state.in_([ERROR, COMPLETE])
            )
        ).order_by(
            model.TaskStatus.last_updated.desc()
        ).first()
        if query is not None:
            query = [query]
    if query is not None and len(query) > 0:
        result = [DomainTaskStatus.from_dict(row.as_dict()) for row in query]
    return result


def get_tracker_statuses(entity_type, entity_id):
    """
    This method will get all trackers registered using the entity_type from the backend and if those are configured to
    show the UI it will get the specific TaskStatus information
    @param entity_type: type of tracker ('resource', 'package', etc)
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: list of dicts containing the information of the TaskStatus objects
    """
    context = {'user': toolkit.g.user}
    result = {}
    for tracker in TrackerBackend.get_trackers():
        if tracker.show_ui:
            status = get_tracker_status(context, tracker, entity_type, entity_id)
            if status is not None:
                result[tracker.name] = status
    return result


def get_tracker_badges(entity_type, entity_id):
    """
    This method will get all trackers registered using the entity_type from the backend and if those are configured to
    show the badge it will get the specific badge
    @param entity_type: type of tracker ('resource', 'package', etc)
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: list of strings containing the badges
    """
    context = {'user': toolkit.g.user}
    result = {}
    for tracker in TrackerBackend.get_trackers():
        if tracker.show_badge:
            status = get_tracker_status(context, tracker, entity_type, entity_id)
            if status is not None:
                result[tracker.name] = [get_tracker_badge(tracker, task_status) for task_status in status]
    return result


def get_tracker_badge(tracker, task_status):
    """
    This method will return the badge for a specific tracker and entity_id
    @param context: context
    @param tracker: TrackerModel
    @param entity_id: the id of an entity (resource id, package id, etc)
    @return: string containing the code of the badge
    """
    if task_status is None:
        return None
    return create_badge(tracker.name, tracker.badge_title, task_status.state)


def create_badge(identifier, title, status):
    """
    This method will create the svg as a string to be shown in HTML. It will try to calculate the width of all the
    separate elements (title, status) based on the strings
    @param identifier: to distinguish this particular badge which should always be different
    @param color: hex representation of the color
    @param title: title to be shown (left side of the badge)
    @param status: status to be shown (right side of the badge)
    @return: string containing the svg code
    """
    status = toolkit._(status)
    if status == ERROR:
        color = '#e05d44'
    elif status == COMPLETE:
        color = '#97CA00'
    else:
        color = '#9f9f9f'
    title_width = calculate_length_text_in_pixels(title, 11)
    status_width = calculate_length_text_in_pixels(status, 11)

    return '''
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20">
        <linearGradient id="b-{identifier}" x2="0" y2="100%">
            <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
            <stop offset="1" stop-opacity=".1"/>
        </linearGradient>
        <clipPath id="a-{identifier}">
            <rect width="{width}" height="20" rx="3" fill="#fff"/>
        </clipPath>
        <g clip-path="url(#a-{identifier})">
            <path fill="#555" d="M0 0h{title_width}v20H0z"/>
            <path fill="{color}" d="M{title_width} 0h{status_width}v20H{title_width}z"/>
            <path fill="url(#b-{identifier})" d="M0 0h{width}v20H0z"/>
        </g>
        <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11px">
            <text x="{title_mid}" y="15" fill="#010101" fill-opacity=".3">{title}</text>
            <text x="{title_mid}" y="14">{title}</text>
            <text x="{status_mid}" y="15" fill="#010101" fill-opacity=".3">{status}</text>
            <text x="{status_mid}" y="14">{status}</text>
        </g>
    </svg>
    '''.format(
        identifier=identifier,
        width=title_width + status_width,
        title_width=title_width, status_width=status_width,
        title_mid=title_width / 2, status_mid=title_width + status_width / 2,
        color=color, title=title, status=status)


def calculate_length_text_in_pixels(text, font_size):
    """
    Simple first try to calculate the width of a text based on font size and type of characters
    """
    upper_case = sum(1 for c in text if c.isupper())
    lower_case = sum(1 for c in text if c.islower())
    unknown_case = len(text) - (upper_case + lower_case)
    return font_size * unknown_case + (font_size + 1) * upper_case + (font_size - 1) * lower_case


def hash(value):
    return hashlib.md5(value).hexdigest()
