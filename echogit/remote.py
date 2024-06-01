
class RemoteStatus:
    def __init__(self, name, dirty, push, pull, other):
        """
        Initialize a new RemoteStatus instance.

        :param name: The name of the remote.
        :param dirty: Boolean indicating if there are uncommitted changes.
        :param push: Boolean indicating if there are commits that need to be pushed.
        :param pull: Boolean indicating if there are changes that need to be pulled.
        :param other: Boolean indicating any other issues with the remote.
        """
        self.name = name
        self.dirty = dirty
        self.push = push
        self.pull = pull
        self.other = other

    def __str__(self):
        """
        Provide a string representation of the remote's status.

        Returns:
            str: A formatted string indicating the remote's status.
        """
        status = []
        if self.dirty:
            status.append('D')
        if self.push:
            status.append('P')
        if self.pull:
            status.append('L')
        if self.other:
            status.append('R')
        return f"{self.name}: {''.join(status)}"
