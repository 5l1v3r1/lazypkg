import oyaml as yaml, os, random, shutil
from collections import OrderedDict as odict

def get_sample_config(name = '{name}'):
    return yaml.dump(odict({
        'name' : name,
        'version' : 0.1,
        'release' : 1,
        'group' : None,
        'summary' : 'anonymous P2P communication platform',
        'description' : 'Onionr is a decentralized, peer-to-peer communication network, designed to be anonymous and resistant to (meta)data analysis, spam, and corruption.',
        'license' : 'GPL',
        'website' : 'https://onionr.net',
        'contact' : 'contact@onionr.net',
        'maintainer' : 'Kevin Froman',

        'sources' : [
            {'git' : 'https://gitlab.com/beardog/onionr.git', 'branch' : 'master'}
        ],

        'relationships' : [
            {'conflicts' : 'onionr2'},
            {'provides' : 'onionr2'}
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
            {'.' : '/usr/share/onionr', 'chown' : 'root:root', 'chmod' : 755}
        ],

        'scripts' : [
            {'pre_install' : 'install/pre_install.sh'},
            {'post_install' : 'install/post_install.sh'}
        ]
    }), default_flow_style = False, indent = 2)

def check_file(filename):
    if os.path.isfile(filename):
        return input('File %s exists. Overwrite (y/N)? ' % filename).strip().lower() == 'y'
    return True

def is_name_valid(name):
    charset = 'abcdefghijklmnopqrstuvwxyz0123456789-_'
    
    name = name.lower()

    for char in charset:
        name = name.replace(char, '')

    return len(name) == 0

def escape(string, wrap = '"'):
    string = str(string).replace('\\', '\\\\').replace('"', '\\"')

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
        for source in config.get('sources', []):
            if 'git' in source:
                git_source = source['git']
                branch = source.get('branch', 'master')
                
                sources.append('${pkgname}-${pkgver}::git+%s#branch=%s' % (git_source, branch))
    
    return format_list(sources, wrap = wrap)

def filter_depends(mode, config, build = None, required = None):
    filtered = list()

    for depend in config.get('dependencies', []):
        if required != None:
            if required != depend.get('required', True):
                continue

        if build != None:
            if build != depend.get('build', False):
                continue

        if mode in depend:
            filtered.append(depend[mode])
        else:
            for test_mode in ['deb', 'pkgbuild', 'rpm']:
                if test_mode in depend:
                    filtered.append(depend[test_mode])
                    break

    return filtered

def filter_relationships(mode, config, provides = None, conflicts = None):
    filtered = list()

    for package_def in config.get('relationships', []):
        for package in package_def:
            if not provides is None:
                if provides != ('provides' == package):
                    continue
            
            if not conflicts is None:
                if conflicts != ('conflicts' == package):
                    continue
    
            filtered.append(package_def[package])

    return filtered

def indent_lines(text, size = 4):
    output = ''

    for line in text.strip().split('\n'):
        output += ' ' * size + line.strip() + '\n'

    return output

def filter_scripts(mode, config, event, prepend = '', indent = 0):
    source = ''

    for script_def in config.get('scripts', []):
        for script in script_def:
            if script == event:
                source += prepend + script_def[event] + '\n'

    return indent_lines(source, indent)

def generate_movements(mode, config, indent = 0):
    source = ''

    if mode != 'pkgbuild':
        source += 'cd "${srcdir}/${pkgname}-${pkgver}"\n\n'

    for movement_def in config.get('movements', []):
        for movement in movement_def:
            if not movement in ['chmod', 'chown']:
                source += 'mkdir -p "%s"\n' % (('$pkgdir/' if mode == 'pkgbuild' else '') + escape(movement_def[movement]))

    if not source == '':
        source = '# ensure target directories exist\n' + source + '\n# copy files over and change perms\n'

    for movement_def in config.get('movements', []):
        src, target = [None] * 2
        chmod, chown = [None] * 2

        for movement in movement_def:
            if movement == 'chmod':
                chmod = movement_def[movement]
            elif movement == 'chown':
                chown = movement_def[movement]
            else:
                src = movement
                target = movement_def[movement]

        if not target is None:
            # we have to chmod/chown beforehand because we don't know the path of the dest file
            if mode != 'pkgbuild':
                if not chmod is None:
                    source += 'chmod -R %d "%s"\n' % (int(chmod), escape(src))
                if not chown is None:
                    source += 'chown -R "%s" "%s"\n' % (escape(chown), escape(src))
                
                source += 'rsync -pr "%s" "%s"\n' % (escape(src), escape(target))
            else:
                if src == '.':
                    src = '.'

                append = ''
                if not chmod is None:
                    append += '--mode=%d ' % int(chmod)
                if not chown is None:
                    owner, group = chown.split(':')
                    append += '--owner="%s" --group="%s"' % (escape(owner), escape(group))

                source += 'rinstall "${srcdir}/${pkgname}-${pkgver}/%s" "${pkgdir}/%s" %s\n' % (escape(src), escape(target), append)

    return indent_lines(source, indent)

def prepare_package(mode, config, path):
    config = yaml.safe_load(config)

    if mode == 'pkgbuild':
        output = ''
        create_install = True

        if 'maintainer' in config:
            output += '# Maintainer: %s' % config['maintainer']

            if 'contact' in config:
                output += ' <%s>' % config['contact']

            output += '\n'
        if 'name' in config:
            output += 'pkgname="%s"\n' % escape(config['name'])
        if 'version' in config:
            output += 'pkgver="%s"\n' % escape(config['version'])
        if 'release' in config:
            output += 'pkgrel="%s"\n' % escape(config['release'])
        if 'group' in config:
            output += 'groups="%s"\n' % escape(config['group'])
        if len(filter_relationships(mode, config, provides = True, conflicts = False)) != 0:
            output += 'provides=(%s)\n' % format_list(filter_relationships(mode, config, provides = True, conflicts = False))
        if len(filter_relationships(mode, config, provides = False, conflicts = True)) != 0:
            output += 'conflicts=(%s)\n' % format_list(filter_relationships(mode, config, provides = False, conflicts = True))
        if 'license' in config:
            output += 'license=(%s)\n' % format_list(config['license'])
        output += 'arch=("i686" "x86_64")\n'
        output += 'md5sums=("SKIP")\n'
        if 'website' in config:
            output += 'url="%s"\n' % escape(config['website'])
        if 'summary' in config or 'description' in config:
            output += 'pkgdesc="%s"\n' % escape(config.get('summary', config.get('description', '')))
        if 'sources' in config:
            output += 'source=(%s)\n' % format_source(mode, config)
        if len(filter_depends(mode, config, build = True)) != 0:
            output += 'makedepends=(%s)\n' % format_list(filter_depends(mode, config, build = True))
        if len(filter_depends(mode, config, build = False, required = True)) != 0:
            output += 'depends=(%s)\n' % format_list(filter_depends(mode, config, build = False, required = True))
        if len(filter_depends(mode, config, build = False, required = False)) != 0:
            output += 'optdepends=(%s)\n' % format_list(filter_depends(mode, config, build = False, required = False))
        if len(config.get('install', [])) != 0:
            output += 'install=%s.install\n' % config['name']
            create_install = True


        # post_install or pre_install use install directive: https://bbs.archlinux.org/viewtopic.php?id=39903
        # more docs: https://wiki.archlinux.org/index.php/creating_packages#prepare()
        # todo figure out about "maintainer"
        
        output += '''
rinstall() {{
    if [ -f "$1" ]; then
        install -D "$1" "$2/" "$3" "$4"
        return 0
    fi

    for file in $(find "$1" -type f -printf '%P\\n'); do
        install -D "$1/$file" "$2/$file" "$3" "$4"
    done

    return 0
}}

prepare() {{
    # pre_build

    cd "${{srcdir}}/${{pkgname}}-${{pkgver}}"
{pre_build}}}

build() {{
    # build

    cd "${{srcdir}}/${{pkgname}}-${{pkgver}}"
{build}}}

check() {{
    # post_build

    cd "${{srcdir}}/${{pkgname}}-${{pkgver}}"
{post_build}}}

package() {{
    # "movements"
{movements}}}
'''.format(pre_build = filter_scripts(mode, config, 'pre_build', prepend = 'sh ', indent = 4), build = filter_scripts(mode, config, 'build', prepend = 'sh ', indent = 4), post_build = filter_scripts(mode, config, 'post_build', prepend = 'sh ', indent = 4), movements = generate_movements(mode, config, indent = 4))
        
        if check_file('PKGBUILD'):
            with open('PKGBUILD', 'w') as f:
                f.write(output)

        if create_install:
            install_file = '%s.install' % config['name']
            install_contents = ''

            if check_file(install_file):
                scripts = ['pre_install', 'post_install', 'pre_upgrade', 'post_upgrade', 'pre_remove', 'post_remove']

                for script in scripts:
                    install_contents += '''
{script} {{
    # {script}

    cd "${{srcdir}}/${{pkgname}}-${{pkgver}}"
{op}
}}
'''.format(script = script, op = filter_scripts(mode, config, script, prepend = 'sh ', indent = 4))
                
                with open(install_file, 'w') as f:
                    f.write(install_contents)

        return 'PKGBUILD'

def build_package(mode, config, path):
    build_dir = '/tmp/lazypkg.%s' % random.randint(0, 999999)
    output = None

    config = yaml.safe_load(config)

    if mode == 'pkgbuild':
        os.mkdir(build_dir)
        os.system('BUILDDIR=%s/ makepkg -f' % build_dir)
        shutil.rmtree(build_dir)

    return output
