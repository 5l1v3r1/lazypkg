#!/usr/bin/python3

import lazypkg, os, sys

version = '1.0'

if __name__ == '__main__':
    if len(sys.argv) != 1:
        command = sys.argv[1].lower().strip().replace('-', '')

        if command.startswith('h'): # help
            print('lazypkg v%s - by arinerron\n\nusage:\n%s <command> <config.yml>\n\ncommands:\nhelp - get help\nrpm - build rpm package\ndeb - build deb package\npkgbuild - build pkgbuild package' % (version, sys.argv[0]))
            exit()
        else:
            if len(sys.argv) != 3:
                print('usage:\n%s %s <config.yml>' % (sys.argv[0], sys.argv[1]))
                exit(1)
            
            config_file = sys.argv[2]
            path = os.path.dirname(config_file)

            config_contents = ''

            with open(config_file, 'r') as f:
                config_contents = f.read()

            mode = ''
            
            if command.startswith('r'): # rpm
                mode = 'rpm'
            elif command.startswith('d'): # deb
                mode = 'deb'
            else: # pkgbuild (default, because arch is epic)
                mode = 'pkgbuild'

            print('preparing %s configs...' % mode)

            output = lazypkg.prepare_package(mode, config_contents, path)

            print('package prepared at %s' % output)

            if input('\nbuild %s now (y/N)? ' % mode).lower().strip() == 'y':
                output = lazypkg.build_package(mode, config_contents, path)

                print('packge built at %s' % output)

            print('\ngood luck / goodbye!')
            exit()

    # otherwise, let's make a config

    name = ''

    while True:
        name = input('package name: ')

        if lazypkg.is_name_valid(name):
            break

        print('invalid name.')

    config_file = '%s.yml' % name

    if not lazypkg.check(config_file):
        print('goodbye!')
        exit(1)

    with open('%s.yml' % name, 'w') as f:
        f.write(lazypkg.get_sample_config(name = name))

    print('your config was written to %s' % config_file)
