###############
### imports ###
###############

from fabric.api import cd, env, lcd, put, prompt, local, sudo
from fabric.contrib.files import exists


##############
### config ###
##############

PROJECT_NAME = 'website'

local_app_dir = '/Users/maruthgoyal/Desktop/crypt/backend'
local_config_dir = '/Users/maruthgoyal/Desktop/crypt/backend/config'

remote_app_dir = '/home/www'
remote_git_dir = '/home/git'
remote_flask_dir = remote_app_dir + PROJECT_NAME
remote_nginx_dir = '/etc/nginx/sites-enabled'
remote_supervisor_dir = '/etc/supervisor/conf.d'

env.hosts = ['add_ip_or_domain']  # replace with IP address or hostname
env.user = 'webadmin'
# env.password = 'blah!'


#############
### tasks ###
#############

def install_requirements():
    """ Install required packages. """
    sudo('apt-get update')
    sudo('apt-get install -y python')
    sudo('apt-get install -y python-pip')
    sudo('apt-get install -y python-virtualenv')
    sudo('apt-get install -y nginx')
    sudo('apt-get install -y gunicorn')
    sudo('apt-get install -y supervisor')
    sudo('apt-get install -y git')


def install_flask():
    """
    1. Create project directories
    2. Create and activate a virtualenv
    3. Copy Flask files to remote host
    """
    if exists(remote_app_dir) is False:
        sudo('mkdir ' + remote_app_dir)
    if exists(remote_flask_dir) is False:
        sudo('mkdir ' + remote_flask_dir)
    with lcd(local_app_dir):
        with cd(remote_app_dir):
            sudo('virtualenv env')
            sudo('source env/bin/activate')
            sudo('pip install flask')
        with cd(remote_flask_dir):
            put('*', './', use_sudo=True)


def configure_nginx():
    """
    1. Remove default nginx config file
    2. Create new config file
    3. Setup new symbolic link
    4. Copy local config to remote config
    5. Restart nginx
    """
    sudo('/etc/init.d/nginx start')

    if exists('/etc/nginx/sites-enabled/default'):
        sudo('rm /etc/nginx/sites-enabled/default')

    if exists('/etc/nginx/sites-enabled/' + PROJECT_NAME) is False:

        sudo('touch /etc/nginx/sites-available/' + PROJECT_NAME)
        sudo('ln -s /etc/nginx/sites-available/' + PROJECT_NAME +
             ' /etc/nginx/sites-enabled/' + PROJECT_NAME)

    with lcd(local_config_dir):
        with cd(remote_nginx_dir):
            put('./' + PROJECT_NAME, './', use_sudo=True)
    sudo('/etc/init.d/nginx restart')


def configure_supervisor():
    """
    1. Create new supervisor config file
    2. Copy local config to remote config
    3. Register new command
    """
    if exists('/etc/supervisor/conf.d/' + PROJECT_NAME + '.conf') is False:
        with lcd(local_config_dir):
            with cd(remote_supervisor_dir):
                put('./' + PROJECT_NAME + '.conf', './', use_sudo=True)
                sudo('supervisorctl reread')
                sudo('supervisorctl update')


def configure_git():
    """
    1. Setup bare Git repo
    2. Create post-receive hook
    """
    if exists(remote_git_dir) is False:

        sudo('mkdir ' + remote_git_dir)

        with cd(remote_git_dir):

            sudo('mkdir ' + PROJECT_NAME + '.git')

            with cd(PROJECT_NAME + '.git'):

                sudo('git init --bare')

                with lcd(local_config_dir):

                    with cd('hooks'):
                        
                        put('./post-receive', './', use_sudo=True)
                        sudo('chmod +x post-receive')


def run_app():
    """ Run the app! """
    with cd(remote_flask_dir):
        sudo('supervisorctl start ' + PROJECT_NAME)


def deploy():
    """
    1. Copy new Flask files
    2. Restart gunicorn via supervisor
    """
    with lcd(local_app_dir):
        local('git add -A')
        commit_message = prompt("Commit message?")
        local('git commit -am "{0}"'.format(commit_message))
        local('git push production master')
        sudo('supervisorctl restart ' + PROJECT_NAME)


def rollback():
    """
    1. Quick rollback in case of error
    2. Restart gunicorn via supervisor
    """
    with lcd(local_app_dir):
        local('git revert master  --no-edit')
        local('git push production master')
        sudo('supervisorctl restart ' + PROJECT_NAME)


def status():
    """ Is our app live? """
    sudo('supervisorctl status')


def create():
    install_requirements()
    install_flask()
    configure_nginx()
    configure_supervisor()
    configure_git()
