# -*- mode: ruby -*-
# vi: set ft=ruby :

# For a complete vagrant reference, please see the online documentation:
# https://docs.vagrantup.com.
Vagrant.configure(2) do |config|
  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/trusty64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Hostname the machine should have. The hostname will be set on boot.
  config.vm.hostname = "dockerhost.local"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine.
  config.vm.network "forwarded_port", guest: 5000,  host: 5000  # Tornado
  config.vm.network "forwarded_port", guest: 80,    host: 8080  # HTTP
  config.vm.network "forwarded_port", guest: 443,   host: 8443  # HTTPS
  config.vm.network "forwarded_port", guest: 3306,  host: 3306  # MariaDB

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # View the documentation for the provider you are using for more
  # information on available options.
  # config.vm.provider "virtualbox" do |v|
  #   v.memory = "1024"
  # end

  # Enable provisioning with Docker.
  config.vm.provision "docker" do |docker|
    docker.images = %w[mariadb python:2.7.10]
  end

  # Provision using a shell.
  config.vm.provision "shell", inline: <<-SH
    curl -sSL https://github.com/docker/compose/releases/download/1.2.0/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
  SH
end
