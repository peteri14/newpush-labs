import os

import pytest

def test_passwd_file(host):
    passwd = host.file("/etc/passwd")
    assert passwd.contains("root")
    assert passwd.user == "root"
    assert passwd.group == "root"
    assert passwd.mode == 0o644


def test_docker_running_and_enabled(host):
    docker = host.service("docker")
    assert docker.is_running
    assert docker.is_enabled

def test_traefik_running_and_enabled(host):
    traefik = host.docker("traefik")
    assert traefik.is_running


@pytest.mark.parametrize("service_name", [
    # "promtail",
    # "sshwifty",
    # "loki",
    # "traefik-forward-auth",
    "traefik",
    "mafl",
    "casdoor",
    # "prometheus",
    # "grafana",
    # "node-exporter",
    # "watchtower",
    # "portainer",
    # "mafl-service-discovery",
    # "dockge",
    # "dozzle",
    # "cadvisor",
])
def test_core_docker_running_and_enabled(host, service_name):
    service = host.docker(service_name)
    assert service.is_running

@pytest.fixture(scope="module")
def ip_address(host):
    return host.run("curl -4 https://ifconfig.me").stdout.strip()

def _lab_domain_zone_from_group_vars():
    group_vars = os.getenv("LAB_GROUP_VARS", "provisioning/ansible/group_vars/lab.yaml")
    try:
        with open(group_vars, encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped.startswith("lab_domain_zone:"):
                    return stripped.split(":", 1)[1].strip().strip("'\"")
    except FileNotFoundError:
        return None
    return None

@pytest.fixture(scope="module")
def lab_domain(ip_address):
    configured_domain = os.getenv("LAB_DOMAIN")
    if configured_domain:
        return configured_domain

    domain_zone = os.getenv("LAB_DOMAIN_ZONE") or _lab_domain_zone_from_group_vars()
    if not domain_zone:
        pytest.fail("LAB_DOMAIN is unset and lab_domain_zone could not be read from group_vars/lab.yaml")
    return f"{ip_address}.{domain_zone}"

def test_auth_url_loads(host, lab_domain):
    url = f"https://auth.{lab_domain}"
    print(f"Testing URL: {url}")
    response = host.run(f"curl -k -s -o /dev/null -w '%{{http_code}}' {url}")
    assert response.stdout == "200"

def test_www_url_loads(host, lab_domain):
    url = f"https://www.{lab_domain}"
    print(f"Testing URL: {url}")
    response = host.run(f"curl -k -s -o /dev/null -w '%{{http_code}}' {url}")
    assert response.stdout == "307" # Redirects to auth

def check_root_free_space(host):
    root_partition = host.run("df / --output=avail -B1 | tail -n1").stdout.strip()
    assert int(root_partition) > 2000000000 # 2GB
