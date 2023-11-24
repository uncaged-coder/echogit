Each project can be configured to be accessible within specified LXC/LXD containers.
This feature isn't directly related to project synchronization, but it can be quite useful,
especially for security reasons.
In my workflow, I utilize various LXC/LXD containers, and to accommodate this, I've implemented the capability to optionally specify LXC container names in the .echogit/config.ini file for each project.

You can include the following lines in your project's configuration file:

[LXC]
containers = container_name
    
When executing the echogit sync command, the system will ensure that the specified LXC/LXD containers have access to this project. Additionally, it will revoke access from all other containers that are defined in the global ~/.config/echogit/config.ini file."
