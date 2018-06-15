import configparser
import os


def create_config(path):
    """
    Create a config file
    """
    config = configparser.ConfigParser()
    config.add_section("Suspension")
    config.set("Suspension", "LFMax", "18")
    config.set("Suspension", "LFRef", "10")
    config.set("Suspension", "RFMax", "18")
    config.set("Suspension", "RFRef", "10")
    config.set("Suspension", "LRMax", "18")
    config.set("Suspension", "LRRef", "10")
    config.set("Suspension", "RRMax", "18")
    config.set("Suspension", "RRRef", "10")

    with open(path, "w") as config_file:
        config.write(config_file)


def get_config(path):
    """
    Returns the config object
    """
    if not os.path.exists(path):
        create_config(path)

    config = configparser.ConfigParser()
    config.read(path)
    return config


def get_setting(path, section, setting):
    """
    Print out a setting
    """
    config = get_config(path)
    value = config.get(section, setting)
    msg = "{section} {setting} is {value}".format(
        section=section, setting=setting, value=value
    )

    print(msg)
    return value


def update_setting(path, section, setting, value):
    """
    Update a setting
    """
    config = get_config(path)
    config.set(section, setting, value)
    with open(path, "w") as config_file:
        config.write(config_file)


def delete_setting(path, section, setting):
    """
    Delete a setting
    """
    config = get_config(path)
    config.remove_option(section, setting)
    with open(path, "w") as config_file:
        config.write(config_file)


if __name__ == "__main__":
    path = 'suspension_config.ini'
    font = get_setting(path, 'Suspension', 'LFMax')
    font_size = get_setting(path, 'Suspension', 'LFRef')
