from urllib.request import urlretrieve
import datetime
import urllib.parse
import io
import boto3
import json
import os

from config import DICTIONARY_BUCKET_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DICTIONARY_FOLDER, \
    DICTIONARY_DEFAULT_VERSION
from ieml.commons import LANGUAGES

__available_versions = None


def get_available_dictionary_version(update=False):
    global __available_versions
    if __available_versions is None or update:
        s3 = boto3.resource(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        bucket_name = 'ieml-dictionary-versions'
        bucket = s3.Bucket(bucket_name)

        result = []
        for obj in bucket.objects.all():
            result.append(DictionaryVersion.from_file_name(obj.key))
        __available_versions = result

    return __available_versions


def _date_to_str(date):
    return date.strftime('%Y-%m-%d_%H:%M:%S')


def _str_to_date(string):
    return datetime.datetime.strptime(string, '%Y-%m-%d_%H:%M:%S')


class DictionaryVersion:
    """
    Track the available versions
    """
    def __init__(self, date=None):
        super(DictionaryVersion, self).__init__()

        self.terms = None
        self.roots = None
        self.inhibitions = None
        self.translations = None
        self.loaded = False

        if date is None:
            date = DICTIONARY_DEFAULT_VERSION

        if isinstance(date, str):
            if date.startswith('dictionary_'):
                self.date = self.from_file_name(date).date
            else:
                self.date = _str_to_date(date)
        elif isinstance(date, datetime.date):
            self.date = date
        else:
            raise ValueError("Invalid date format for dictionary version %s." % _date_to_str(date))

    def __str__(self):
        return 'dictionary_%s' % _date_to_str(self.date)

    def __getstate__(self):
        self.load()

        return {
            'version': _date_to_str(self.date),
            'terms': self.terms,
            'roots': self.roots,
            'inhibitions': self.inhibitions,
            'translations': self.translations
        }

    def __setstate__(self, state):
        self.date = _str_to_date(state['version'])
        self.terms = state['terms']
        self.roots = state['roots']
        self.inhibitions = state['inhibitions']
        self.translations = state['translations']

        self.loaded = True

    def json(self):
        return json.dumps(self.__getstate__())

    def upload_to_s3(self):
        s3 = boto3.resource(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
        bucket_name = 'ieml-dictionary-versions'
        bucket = s3.Bucket(bucket_name)
        obj = bucket.Object("%s.json" % str(self))

        obj.upload_fileobj(io.BytesIO(bytes(self.json(), 'utf-8')))
        obj.Acl().put(ACL='public-read')

        assert self in get_available_dictionary_version(update=True)

    def load(self):
        if self.loaded:
            return

        file_name = "%s.json" % str(self)

        if not os.path.isdir(DICTIONARY_FOLDER):
            os.mkdir(DICTIONARY_FOLDER)

        file = os.path.join(DICTIONARY_FOLDER, file_name)

        if not os.path.isfile(file):
            url = urllib.parse.urljoin(DICTIONARY_BUCKET_URL, file_name)
            print("\t[*] Downloading dictionary %s at %s" % (file_name, url))
            urlretrieve(url, file)

        with open(file, 'r') as fp:
            self.__setstate__(json.load(fp))

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return str(self).__hash__()

    def __lt__(self, other):
        return self.date < other.date

    def __gt__(self, other):
        return self.date > other.date

    @staticmethod
    def from_file_name(file_name):
        date = _str_to_date(file_name.split('.')[0].split('_', maxsplit=1)[1])
        return DictionaryVersion(date=date)

_default_version = None


def get_default_dictionary_version():
    global _default_version
    if _default_version is None:
        _default_version = DictionaryVersion()

    return _default_version


def create_dictionary_version(old_version, add=None, update=None, remove=None):
    """

    :param old_version: the dictionary version to build the new version from
    :param add: a dict with the element to add {'terms': list of script to add,
                                                'roots': list of script to add root paradigm,
                                                'inhibitions': dict {root_p: list of relations to inhibits in this root p}
                                                'translations': dict {language: {script: traduction}}}
    :param update: a dict to update the translations and inhibtions
    :param remove: a list of term to remove, they are removed from root, terms, inhibitions and translations
    :return:
    """
    v = get_available_dictionary_version()[-1]
    last_date = v.date

    while True:
        new_date = datetime.datetime.today()
        if new_date != last_date:
            break

    old_version.load()

    state = {
        'version': _date_to_str(new_date),
        'terms': old_version.terms,
        'roots': old_version.roots,
        'inhibitions': old_version.inhibitions,
        'translations': old_version.translations
    }

    if add is not None:
        if 'terms' in add:
            state['terms'] = list(set(state['terms']).union(add['terms']))
        if 'roots' in add:
            state['roots'] = list(set(state['roots']).union(add['roots']))
        if 'inhibitions' in add:
            state['inhibitions'] = {**state['inhibitions'], **add['inhibitions']}
        if 'translations' in add:
            state['translations'] = {l: {**state['translations'][l], **add['translations'][l]} for l in LANGUAGES}

    if remove is not None:
        state['terms'] = list(set(state['terms']).difference(remove))
        state['roots'] = list(set(state['roots']).difference(remove))
        for r in remove:
            if r in state['inhibitions']:
                del state['inhibitions'][r]

            for l in LANGUAGES:
                if r in state['translations'][l]:
                    del state['translations'][l][r]

    if update is not None:
        if 'inhibitions' in update:
            for s, l in update['inhibitions'].items():
                if s not in state['inhibitions']:
                    continue
                state['inhibitions'][s].extend(l)
        if 'translations' in update:
            state['translations'] = {l: {**state['translations'][l], **update['translations'][l]} for l in LANGUAGES}

    dictionary_version = DictionaryVersion(new_date)
    dictionary_version.__setstate__(state)

    from ieml.ieml_objects.terms.dictionary import Dictionary

    if set(old_version.terms) == set(state['terms']) and set(old_version.roots) == set(state['roots']) and \
       all(old_version.inhibitions[s] == state['inhibitions'][s] for s in old_version.inhibitions):

        old_dict_state = Dictionary(old_version).__getstate__()
        d = Dictionary(dictionary_version, load=False)
        d.__setstate__(old_dict_state)
        d.load()
    else:
        # graph is updated, must check the coherence
        Dictionary(dictionary_version)

    return dictionary_version


if __name__ == '__main__':
    print(get_available_dictionary_version())