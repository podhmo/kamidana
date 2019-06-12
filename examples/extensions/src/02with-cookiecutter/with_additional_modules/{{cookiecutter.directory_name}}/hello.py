# use the feature of builtin additional modules
original = "{{cookiecutter.project_name}}"
print("camelcase: {{cookiecutter.project_name|camelcase}}")
print("snakecase: {{cookiecutter.project_name|snakecase}}")
print("kebabcase: {{cookiecutter.project_name|kebabcase}}")


# use the feature of individial additional modules
"""
{{about_kamidana()}}
"""
