import re
from os import urandom
from random import choice
from StringIO import StringIO
from string import ascii_letters, punctuation
from fabric.api import *


def _check_sudo():
    with settings(warn_only=True):
        result = sudo('pwd')
        if result.failed:
            print "Trying to install sudo. Must be root"
            run('apt-get update && apt-get install -y sudo')


def create_credentials(domain):
    return {
        "user": domain.replace('.', '')[:16],
        "password": urandom(16).encode('hex')[:13],
        "dbname": domain.replace('.', '')[3:18]
    }


def wp_prefix():
    """
    New database prefix for WordPress wp-config.php
    """
    return '"{0}_"'.format(''.join(choice(ascii_letters) for x in range(2)))


def wp_salt():
    """
    Salts for WordPress wp-config.php
    """
    match = r"[\",',\\,\*,\/]"
    charset = re.sub(match, 'x', ascii_letters + punctuation)
    return "'" + ''.join(choice(charset) for x in range(64)) + "'"


def setup_database(credentials):
    """
    Creates mysql database using credentials
    """

    with settings(warn_only=True):
        if sudo('mysqladmin create ' + credentials['dbname']).failed:
            sudo('mysqladmin drop ' + credentials['dbname'])
            sudo('mysqladmin create ' + credentials['dbname'])

    sql = """echo "GRANT ALL PRIVILEGES ON {dbname}.* TO '{user}'@localhost IDENTIFIED BY '{password}';" | mysql"""
    sudo(sql.format(**credentials))


def www(domain):
    """
    Create new www file directory
    """

    with cd("/var/www/"):
        run("mkdir " + domain)
        sudo('chown -R www-data:www-data ' + domain)
        sudo('chmod -R g+rw ' + domain)


def nginx(domain):
    """
    Create new PHP NGINX server in /etc/nginx/ with web directory at /var/www
    """

    default_config = """
    server {{
        server_name {1};
        return 301 $scheme://{0}$request_uri;
    }}

    server {{
        server_name {0};
        root /var/www/{0};
        location / {{
            try_files $uri $uri/ /index.php?$args;
        }}

        access_log /var/log/nginx/{0}.access.log;
        error_log /var/log/nginx/{0}.error.log;

        include /etc/nginx/www_params;
        include /etc/nginx/fastcgi_php;
    }}
    """
    new_config = default_config.format(domain, domain[4:])

    with cd('/etc/nginx/sites-available/'):
        with settings(warn_only=True):
            if (put(StringIO(new_config), domain)).failed:
                pass

    with cd('/etc/nginx/sites-enabled'):
        with settings(warn_only=True):
            if (run("ln -s /etc/nginx/sites-available/" + domain)).failed:
                pass

    www(domain)

    sudo('invoke-rc.d nginx reload')


def wordpress(domain):
    """
    Installs WordPress, including NGINX config, DB, and wp-config.php
    """

    credentials = create_credentials(domain)
    wp_config = StringIO()
    match = {
        "user": 'username_here',
        "password": 'password_here',
        "dbname": 'database_name_here',
        "phrase": "'put your unique phrase here'",
        "prefix": "'wp_'"
    }

    nginx(domain)
    # www(domain)
    setup_database(credentials)

    with cd('/var/www/' + domain):
        # clone wordpress
        run('git clone git://github.com/WordPress/WordPress.git .')
        # checkout latest tag (stable branch in SVN)
        run('git checkout $(git describe --tags $(git rev-list --tags --max-count=1))')

        get('wp-config-sample.php', wp_config)
        new_config = wp_config.getvalue()

        for key in match:
            if "phrase" in key:
                new_config = re.sub(match[key], wp_salt, new_config)
            elif "prefix" in key:
                new_config = re.sub(match[key], wp_prefix, new_config)
            else:
                new_config = re.sub(match[key], credentials[key], new_config)

        put(StringIO(new_config), "wp-config.php")
