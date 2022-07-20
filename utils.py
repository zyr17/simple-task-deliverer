import yaml

def get_configs(filename):
    return yaml.load(open(filename), yaml.SafeLoader)

def gen_cmd_prefix(prefix, device, number):
    return prefix + str(device) + '_' + str(number)

def get_real_path(unk_path, config_folder):
    if unk_path[0] == '/':
        return unk_path
    return f'{config_folder}/{unk_path}'
