==========================
Enabling Solum in DevStack
==========================

1. Install Docker version 1.7.0 using following steps (Solum has been tested with this version of Docker)::

    echo deb http://get.docker.com/ubuntu docker main | sudo tee /etc/apt/sources.list.d/docker.list
    sudo apt-key adv --keyserver pgp.mit.edu --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
    sudo apt-get update
    sudo apt-get install -y lxc-docker-1.7.0

2. Download DevStack::

    git clone https://git.openstack.org/openstack-dev/devstack.git
    cd devstack

3. Add this repo as an external repository::

    cat > local.conf <<END
    [[local|localrc]]
    enable_plugin solum git://git.openstack.org/openstack/solum
    END

4. Run ``stack.sh``.

.. note::

  This setup will produce virtual machines, not Docker containers.
  For an example of the Docker setup, see::

    http://wiki.openstack.org/Solum/Docker
