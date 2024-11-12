import yaml
from base4.utilities.files import get_project_config_folder, get_project_root


def generate_nginx_conf():

    nginx_template = get_project_config_folder() / 'docker' / 'nginx.conf.tpl'
    services_yaml = get_project_config_folder() / 'services.yaml'

    result = get_project_config_folder() / 'docker' / 'nginx-generated.conf'

    with open(nginx_template, 'r') as f:
        template = f.read()

    with open(services_yaml, 'r') as f:
        services = yaml.safe_load(f.read())

    nginx_locations = '\n'
    for svc in services['services']:
        svc_name = list(svc.keys())[0]
        nginx_locations += '\n'+'''    location /api/'''+svc_name+'''     { proxy_pass http://'''+svc_name+''':8000; proxy_redirect off; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $remote_addr; }'''
    nginx_locations += '\n'

    template = template.replace('{{services}}', nginx_locations)

    with open(result, 'w') as f:
        f.write(template)

    print('Nginx configuration generated successfully!')

if __name__ == '__main__':
    generate_nginx_conf()
