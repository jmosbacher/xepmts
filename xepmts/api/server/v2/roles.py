
GLOBAL_WRITE_ROLES = ["admin", "expert"]
GLOBAL_READ_ROLES = ["read:all"]

def add_roles(resources,
              global_write_roles=GLOBAL_WRITE_ROLES,
              global_read_roles=GLOBAL_READ_ROLES):

    new_resources = {}
    for name, resource in resources.items():
        experiment_name = resource["schema"]["experiment"]["default"]
        detector = resource["schema"]["detector"]["default"]

        write_roles = global_write_roles + [f'write:{experiment_name}', 
                                                f'write:{experiment_name}_{detector}', 
                                                f'write:{resource["datasource"]["source"]}']
        read_roles = write_roles + global_read_roles + [ f'read:{experiment_name}',
                                        f'read:{experiment_name}_{detector}',
                                        f'read:{resource["datasource"]["source"]}']
        new_resource = dict(resource)
        new_resource["allowed_read_roles"] = resource.get("allowed_read_roles", []) + read_roles
        new_resource["allowed_item_read_roles"] = resource.get("allowed_item_read_roles", []) + read_roles
        new_resource["allowed_write_roles"] = resource.get("allowed_write_roles", []) + write_roles
        new_resource["allowed_item_write_roles"] = resource.get("allowed_item_write_roles", []) + write_roles
        new_resources[name] = new_resource
    return new_resources