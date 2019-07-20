import oyaml as yaml
from collections import OrderedDict as odict

def get_sample_config(name = '{name}'):
    return yaml.dump(odict({
        'name' : name,
        'version' : 0.1,
        'release' : 1,
        'summary' : 'anonymous P2P communication platform',
        'description' : 'Onionr is a decentralized, peer-to-peer communication network, designed to be anonymous and resistant to (meta)data analysis, spam, and corruption.',
        'license' : 'GPL',
        'website' : 'https://onionr.net',
        'contact' : 'contact@onionr.net',
        'author' : 'Kevin Froman',

        'sources' : [
            {'git' : 'https://gitlab.com/beardog/onionr.git', 'branch' : 'master'}
        ],
        
        'dependencies' : [
            {
                'deb' : 'git',
                'required' : True
            },
            {
                'deb' : 'curl',
                'required' : True
            },
            {
                'deb' : 'tor',
                'required' : True
            },
            {
                'deb' : 'python3.7',
                'pkgbuild' : 'python',
                'build' : True,
                'required' : True
            },
            {
                'deb' : 'python3-setuptools',
                'pkgbuild' : 'python-setuptools',
                'build' : True,
                'required' : True
            },
            {
                'deb' : 'python3-pip',
                'pkgbuild' : 'python-pip',
                'build' : True,
                'required' : True
            }
        ],

        'movements' : [
            {'install/onionr' : '/usr/bin/', 'chown' : 'root:root', 'chmod' : 755},
            {'install/onionr.service' : '/etc/systemd/system/', 'chown' : 'root:root', 'chmod' : 644},
            {'*' : '/usr/share/onionr', 'chown' : 'root:root', 'chmod' : 755}
        ],

        'scripts' : [
            {'pre_install' : 'install/pre_install.sh'},
            {'post_install' : 'install/post_install.sh'}
        ]
    }), default_flow_style = False, indent = 2)

def is_name_valid(name):
    charset = 'abcdefghijklmnopqrstuvwxyz0123456789-_'
    
    name = name.lower()

    for char in charset:
        name = name.replace(char, '')

    return len(name) == 0

def escape(string, wrap = '"'):
    string = string.replace('\\', '\\\\').replace('"', '\\"')

    if wrap == "'":
        string = string.replace(wrap, '\'"\'"\'')

    return string

def format_list(string, wrap = '"'):
    if isinstance(string, str):
        string = [string]

    return wrap + (wrap + ' ' + wrap).join([escape(x, wrap = wrap) for x in string]) + wrap

def format_source(mode, config, wrap = '"'):
    sources = []

    if mode == 'pkgbuild':
        for source in config.get('source', []):
            if 'git' in source:
                git_source = source['git']
                branch = source.get('branch', 'master')
                
                sources.append('${pkgname}-${pkgver}::git+%s#branch=%s' % (git_source, branch))

    return format_list(format_source, wrap = wrap)

def filter_depends(mode, config, build = None, required = None):
    filtered = list()

    for depend in config.get('dependencies', []):
        if not (required != None and required == depend.get('required', True)):
            continue

        if not (build != None and build == depend.get('build', False)):
            continue

        if mode in depend:
            filtered.append(depend[mode])
        else:
            for test_mode in ['deb', 'pkgbuild', 'rpm']:
                if test_mode in depend:
                    filtered.append(depend[test_mode])

    return filtered


def prepare_package(mode, config, path):
    if mode == 'pkgbuild':
        output = ''

        if 'name' in config:
            output += 'pkgname="%s"\n' % escape(config['name'])
        if 'version' in config:
            output += 'pkgvers="%s"\n' % escape(config['version'])
        if 'release' in config:
            output += 'pkgrel="%s"\n' % escape(config['release'])
        if 'license' in config:
            output += 'license=(%s)\n' % format_list(config['license'])
        if 'website' in config:
            output += 'url="%s"\n' % escape(config['website'])
        if 'summary' in config or 'description' in config:
            output += 'pkgdesc="%s"\n' % escape(config.get('summary', config.get('description', '')))
        if 'source' in config:
            output += 'source=(%s)\n' % format_source(mode, config)
        if len(filter_depends(mode, config, build = True)) != 0:
            output += 'makedepends=(%s)\n' % format_list(filter_depends(mode, config, build = True))
        if len(filter_depends(mode, config, build = False)) != 0:
            output += 'depends=(%s)\n' % format_list(filter_depends(mode, config, build = False))

        # post_install or pre_install use install directive: https://bbs.archlinux.org/viewtopic.php?id=39903
        # more docs: https://wiki.archlinux.org/index.php/creating_packages#prepare()
        
        sources += '''
prepare() {
    // pre_build
}

build() {
    // build
}

check() {
    // post_build
}

package() {
    // "movements"
}
        '''
    pass

def build_package(mode, path):
    return './tarball.xz'
