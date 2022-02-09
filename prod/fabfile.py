import os
from fabric.contrib.files import sed
from fabric.contrib.files import env, local, run
from fabric.api import venv


# initialize the base directory
abs_dir_path = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# declare environment global variables

# root user
env.user = 'root'

# list of remote IP addresses
env.hosts = ['<remote-server-ip>']

# password for the remote server
env.password = '<remote-server-password>'

# full name of the user
env.full_name_user = '<your-name>'

# user group
env.user_group = 'deployers'

# user for the above group

env.user_name = 'deployer'

env.ssh_key_dir = os.path.join(abs_dir_path, 'ssh-keys')


def start_provision():
    """
    start server provisioning
    :return:
    """
# Create a new directory for a new remote server
    env.ssh_keys_name = os.path.join(
        env.ssh_key_dir, env.host_string + '_prod_key')
    local('ssh-keygen -t rsa -b 2048 -f {0}'.format(env.ssh_keys_name))
    local('cp {0} {1}/authorized_keys'.format(
        env.ssh_keys_name + '.pub', env.ssh_keys_dir))
    # Prevent root SSHing into the remote server
    sed('/etc/ssh/sshd_config', '^UsePAM yes', 'UsePAM no')
    sed('/etc/ssh/sshd_config', '^PermitRootLogin yes',
        'PermitRootLogin no')
    sed('/etc/ssh/sshd_config', '^#PasswordAuthentication yes',
        'PasswordAuthentication no')


def create_deployer_group():
    """
    Create a user group for all project developers
    :return:
    """
    run('groupadd {}'.format(env.user_group))
    run('mv /etc/sudoers /etc/sudoers-backup')
    run('(cat /etc/sudoers-backup; echo "%' +
        env.user_group + 'ALL=(ALL) ALL") > /etc/sudoers')
    run('chmod 440 /etc/sudoers')


def create_deployer_user():
    """
    Create a user for the user group
    :return:
    """
    run('adduser -c "{}" -m -g {} {}'.format(
        env.full_name_user, env.user_group, env.user_name))
    run('passwd {}'.format(env.user_name))
    run('usermod -a -G {} {}'.format(env.user_group, env.user_name))
    run('mkdir /home/{}/.ssh'.format(env.user_name))
    run('chown -R {} /home/{}/.ssh'.format(env.user_name, env.user_name))
    run('chgrp -R {} /home/{}/.ssh'.format(
        env.user_group, env.user_name))


def upload_keys():
    """
    Upload the SSH public/ private keys to the remote server via scp
    :return:
    """
    scp_command = 'scp {} {}/authorized_keys {}@{}:~/.ssh'.format(
        env.ssh_keys_name + '.pub',
        env.ssh_keys_dir,
        env.user_name,
        env.host_string
    )
    local(scp_command)


def install_ansible_dependencies():
    """
    Install the python-dnf module so that Ansible can communicate with
    Fedora's Package Manager
    :return:
    """
    run('dnf install -y python-dnf')


def set_selinux_permissive():
    """
    Set SELinux to Permissive/Disabled Mode
    :return:
    """
    run('sudo setenforce 0')


def upgrade_server():
    """
    Upgrade the server as a root user
    :return:
    """
    run('dnf upgrade -y')
    run('dnf install -y python')
    run('reboot')



install_ansible_dependencies()
create_deployer_group()
create_deployer_user()
upload_keys()
set_selinux_permissive()
run('service sshd reload')
upgrade_server()

