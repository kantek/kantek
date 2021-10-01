class Error(Exception):
    pass


class MissingArgumentsError(Error):
    pass


class UnknownTopicError(Error):
    pass


class UpdateError(Error):
    pass
