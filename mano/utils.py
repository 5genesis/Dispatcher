import os
import yaml

from datetime import datetime, tzinfo, timedelta


class SimpleUtc(tzinfo):
    def tzname(self, **kwargs):
        return "UTC"

    def utcoffset(self, dt):
        return timedelta(0)


def current_datatime():
    return str(datetime.utcnow().replace(tzinfo=SimpleUtc()).isoformat()).replace('+00:00', 'Z')


def str_to_bool(string):
    if str(string).lower() in ['true', '1', 't', 'y', 'yes', 'public']:
        return True
    return False


def init_directory():
    if not os.path.isfile('/repository/index.yaml'):
        os.mkdir('/repository/vnf')
        os.mkdir('/repository/nsd')
        index_data = {'apiVersion': 'v1', 'generated': current_datatime(), 'vnf_packages': {}, 'nsd_packages': {}}
        with open('/repository/index.yaml', 'w') as outfile:
            yaml.dump(index_data, outfile, default_flow_style=False)
